import socket


async def dummy_server_factory(bind_addr, handler, certfile=None, keyfile=None):
    from aiohttp import web

    ssl_context = None
    if certfile is not None:
        import ssl
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(certfile, keyfile)

    sv = web.Server(handler)
    runner = web.ServerRunner(sv)
    await runner.setup()
    site = web.TCPSite(runner, bind_addr, 0, ssl_context=ssl_context)
    await site.start()
    try:
        yield getsockname(site._server.sockets[0])
    finally:
        await site.stop()


def getsockname(sock):
    sockname = sock.getsockname()
    if sock.family == socket.AF_INET:
        return "{}:{}".format(*sockname)
    elif sock.family == socket.AF_INET6:
        return "[{}]:{}".format(*sockname)
    else:
        raise NotImplementedError()
