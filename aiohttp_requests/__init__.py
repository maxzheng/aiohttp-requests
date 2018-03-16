import aiohttp
import functools

# Patch ClientResponse.read to release immediately after read so we don't need to worry about that / use context manager
_read_only = aiohttp.client_reqrep.ClientResponse.read
async def _read_and_release(self):  # noqa
    try:
        data = await _read_only(self)
    finally:
        self.close()

    return data
aiohttp.client_reqrep.ClientResponse.read = _read_and_release


class Requests:
    """ Thin wrapper for aiohttp.ClientSession with Requests simplicity """
    def __init__(self, *args, **kwargs):
        self._session_args = (args, kwargs)
        self._session = None

    @property
    def session(self):
        """ An instance of aiohttp.ClientSession """
        if not self._session:
            self._session = aiohttp.ClientSession(*self._session_args[0], **self._session_args[1])
        return self._session

    def __getattr__(self, attr):
        if attr.upper() in aiohttp.hdrs.METH_ALL:
            return functools.partial(self.session._request, attr.upper())
        else:
            return super().__getattribute__(attr)

    def close(self):
        """ aiohttp.ClientSession.close is async even though it isn't calling any async methods """
        if self._session:
            if not self._session.closed:
                # Older aiohttp does not have _connector_owner
                if not hasattr(self._session, '_connector_owner') or self._session._connector_owner:
                    self._session._connector.close()
                self._session._connector = None

    def __del__(self):
        self.close()


requests = Requests()
