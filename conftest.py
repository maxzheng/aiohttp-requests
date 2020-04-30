import os

import pytest


NONEXISTENT = object()


class SetEnv:
    def __init__(self, environ=os.environ):
        self.overridden = {}
        self.environ = environ

    def __setitem__(self, k, v):
        self.overridden[k] = self.environ.get(k, NONEXISTENT)
        self.environ[k] = v

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
