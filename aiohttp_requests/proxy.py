# Copyright (c) 2020 Moriyoshi Koizumi. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import functools
import ipaddress
import re
import urllib.request


if os.name == "nt":
    our_proxy_bypass_os = urllib.request.proxy_bypass_registry
elif os.name == "darwin":
    our_proxy_bypass_os = urllib.request.proxy_bypass_macosx_sysconf
else:
    # FIXME: gsettings!
    our_proxy_bypass_os = None


host_port_regex = re.compile(r"\[([0-9a-fA-F:]+)\](?::([0-9]+))?|([0-9.]+)(?::([0-9]+))?$")
network_port_regex = re.compile(r"(?:\[([0-9a-fA-F:]+)(/[0-9]+)?\](/[0-9]+)?|(\*))(?::([0-9]+|\*))?|(?:([0-9.]+(?:/[0-9]+)?)|(\*))(?::([0-9]+|\*))?$")  # noqa


def parse_ip_address_and_port(addr):
    g = host_port_regex.match(addr)
    if g is None:
        raise ValueError(addr)
    if g.group(1) is not None:
        return ipaddress.ip_address(g.group(1)), g.group(2)
    elif g.group(3) is not None:
        return ipaddress.ip_address(g.group(3)), g.group(4)


def parse_ip_network_and_port(net):
    g = network_port_regex.match(net)
    if g is None:
        raise ValueError(net)

    if g.group(1) is not None:
        # ipv6 address
        if g.group(2) and g.group(3) or (not g.group(2) and not g.group(3)):
            raise ValueError(net)
        if g.group(2):
            return ipaddress.ip_network(g.group(1) + g.group(2)), g.group(5)
        else:
            return ipaddress.ip_network(g.group(1) + g.group(3)), g.group(5)
    elif g.group(4) is not None:
        # ipv6 address (wildcard)
        return None, g.group(5)
    elif g.group(6) is not None:
        # ipv4 address
        ipv4_net, colon, pref_len = g.group(6).partition("/")
        ipv4_net = remove_dot(ipv4_net)
        ndots = ipv4_net.count(".")
        ipv4_net += ".0" * (3 - ndots)
        if not colon:
            pref_len = 8 * (ndots + 1)
        return ipaddress.ip_network(f"{ipv4_net}/{pref_len}"), g.group(8)
    elif g.group(7) is not None:
        # ipv4 address (wildcard)
        return None, g.group(8)


def remove_dot(host):
    if host.endswith("."):
        # a single trailing dot must be ignored, but not two
        host = host[:-1]
    return host


class HostNameMatcher:
    def __init__(self, host_list):
        self.host_list = host_list

    def _match_ip_addr(self, parsed_ip_addr, port):
        for proxy_ip in self.host_list:
            try:
                network_part, port_part = parse_ip_network_and_port(proxy_ip)
            except ValueError:
                try:
                    host_part, port_part = parse_ip_address_and_port(proxy_ip)
                    network_part = (
                        ipaddress.IPv4Network
                        if isinstance(host_part, ipaddress.IPv4Address)
                        else ipaddress.IPv6Network
                    )(
                        host_part, 0
                    )
                except ValueError:
                    continue
            if (
                # port
                (
                    (not port_part)
                    or (port_part == "*" or port == port_part)
                ) and
                # hostname
                (network_part is None or parsed_ip_addr in network_part)
            ):
                return True
        return False

    def _match_hostname(self, hostname, port):
        for host in self.host_list:
            host_part, colon, port_part = host.partition(":")
            if host_part.startswith("."):
                # To conform to the curl's behavior,
                # ".example.com" and "example.com" are the same.
                # See https://github.com/curl/curl/issues/1208#issuecomment-272837735
                host_part = host_part[1:]
            host_part = remove_dot(host_part)
            if (
                (not colon or port_part == "*" or port == port_part) and
                (
                    host_part == "*"
                    or host_part == hostname
                    or (
                        len(hostname) > len(host_part) and
                        hostname.endswith(host_part) and
                        hostname[-len(host_part) - 1] == "."
                    )
                )
            ):
                return True
        return False

    def __call__(self, hostname, port=None):
        assert isinstance(port, (str, None.__class__))
        parsed_ip_addr = None
        hostname = remove_dot(hostname)
        try:
            # braces around a v6 address should have already been removed by yarl.
            parsed_ip_addr = ipaddress.ip_address(hostname)
        except ValueError:
            try:
                parsed_ip_addr, _ = parse_ip_address_and_port(hostname)
            except ValueError:
                pass

        if parsed_ip_addr is not None:
            return self._match_ip_addr(parsed_ip_addr, port)
        else:
            return self._match_hostname(hostname, port)


def memoize(f):
    results = []

    @functools.wraps(f)
    def _(*args):
        for i, (a, retval) in enumerate(results):
            if a == args:
                results.append(results.pop(i))
                break
        else:
            if len(results) >= 16:
                results.pop(0)
            retval = f(*args)
            results.append((args, retval))
        return retval
    return _


@memoize
def split_host_list(host_list_str):
    return [
        host
        for host in (
            host.strip()
            for host in re.split(r"\s+|\s*,\s*", host_list_str)
        )
        if host
    ]


def should_bypass_proxies(parsed, no_proxy):
    if parsed.scheme in ("http", "https", "gopher") and parsed.host is None:
        return False

    if (
        no_proxy and
        HostNameMatcher(split_host_list(no_proxy))(
            parsed.host,
            (str(parsed.port) if parsed.port is not None else None)
        )
    ):
        return True

    if not our_proxy_bypass_os:
        return False

    return our_proxy_bypass_os(parsed.host)
