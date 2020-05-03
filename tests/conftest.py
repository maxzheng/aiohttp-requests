import os
import ipaddress
from collections import namedtuple
from datetime import datetime, timedelta

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
import pytest


NONEXISTENT = object()


class SetEnv:
    def __init__(self, environ=os.environ):
        self.overridden = {}
        self.environ = environ

    def __setitem__(self, k, v):
        self.overridden[k] = self.environ.get(k, NONEXISTENT)
        self.environ[k] = v

    def __delitem__(self, k):
        if k in self.environ:
            self.overridden[k] = self.environ[k]
            del self.environ[k]

    def __getitem__(self, k):
        if k not in self.overridden:
            raise KeyError(k)
        return self.environ[k]

    def get_overridden(self, k):
        v = self.overridden.get(k, NONEXISTENT)
        if v is NONEXISTENT:
            raise KeyError(k)
        else:
            return v

    def rollback(self):
        for k, v in self.overridden.items():
            if v is NONEXISTENT:
                del self.environ[k]
            else:
                self.environ[k] = v

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.rollback()
        return False


@pytest.fixture
def setenv():
    with SetEnv() as setenv:
        yield setenv


CRYPTOGRAPHY_BACKEND = default_backend()


def gen_privkey():
    return rsa.generate_private_key(
        backend=CRYPTOGRAPHY_BACKEND,
        public_exponent=65537,
        key_size=2048,
    )


def build_dns_name_or_ip_address(dns_name_or_ip_address):
    try:
        ip_address = ipaddress.ip_address(dns_name_or_ip_address)
        return x509.IPAddress(ip_address)
    except ValueError:
        pass

    try:
        ip_network = ipaddress.ip_network(dns_name_or_ip_address)
        return x509.IPAddress(ip_network)
    except ValueError:
        pass

    return x509.DNSName(dns_name_or_ip_address)


def gen_cert_proto(
    common_name,
    public_key,
    country_name="US",
    state_or_province_name="California",
    locality_name="San Francisco",
    organization_name="Yoyodyne, Inc,",
    key_usage="server",
    sans=[],
):
    builder = x509.CertificateBuilder()
    builder = builder.subject_name(x509.Name([
        x509.NameAttribute(x509.oid.NameOID.COUNTRY_NAME, country_name),
        x509.NameAttribute(x509.oid.NameOID.STATE_OR_PROVINCE_NAME, state_or_province_name),
        x509.NameAttribute(x509.oid.NameOID.LOCALITY_NAME, locality_name),
        x509.NameAttribute(x509.oid.NameOID.ORGANIZATION_NAME, organization_name),
        x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, common_name),
    ]))
    if sans:
        builder = builder.add_extension(
            x509.SubjectAlternativeName([build_dns_name_or_ip_address(n) for n in sans]),
            critical=False,
        )
    if key_usage == "server":
        builder = builder.add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        builder = builder.add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        builder = builder.add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
            ]),
            critical=False,
        )
    elif key_usage == "ca":
        builder = builder.add_extension(
            x509.KeyUsage(
                digital_signature=False,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        builder = builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        builder = builder.issuer_name(builder._subject_name)
    builder = builder.not_valid_before(datetime.today() + timedelta(days=-1))
    builder = builder.not_valid_after(datetime.today() + timedelta(days=1))
    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.public_key(public_key)
    return builder


CertKeyPair = namedtuple("CertKeyPair", ["certificate", "key"])


def gen_root_ca_cert(common_name):
    key = gen_privkey()
    return CertKeyPair(
        certificate=gen_cert_proto(
            common_name=common_name,
            public_key=key.public_key(),
            key_usage="ca",
        ).sign(
            private_key=key,
            algorithm=hashes.SHA256(),
            backend=CRYPTOGRAPHY_BACKEND,
        ),
        key=key,
    )


@pytest.fixture
def root_cas():
    return [gen_root_ca_cert("Root CA {}".format(i)) for i in range(0, 3)]


CertKeyCATriplet = namedtuple("CertKeyCATriplet", ["certificate", "key", "ca_certificate"])


@pytest.fixture
def server_certs(root_cas):
    key = gen_privkey()
    return [
        CertKeyCATriplet(
            certificate=gen_cert_proto(
                common_name="127.0.0.1",
                public_key=key.public_key(),
                key_usage="server",
                sans=["127.0.0.1"],
            ).issuer_name(
                ca_cert.subject,
            ).sign(
                private_key=ca_key,
                algorithm=hashes.SHA256(),
                backend=CRYPTOGRAPHY_BACKEND,
            ),
            key=key,
            ca_certificate=ca_cert,
        )
        for ca_cert, ca_key in root_cas
    ]
