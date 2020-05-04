Version 0.2.0
================================================================================
* More compatibility with requests
* Deprecate usage of ``Requests.session`` and ``Requests.close()``. The
  Alternatives are ``Requests.async_session()`` and ``Requests.async_close())``
  respectively
* Raise the required Python version to 3.6
* Raise the required aiohttp version to 3.1.0


Version 0.1.2
================================================================================

* Update setup

Version 0.1.1
--------------------------------------------------------------------------------

* Remove pip.req

Version 0.1.0
--------------------------------------------------------------------------------

* Recreate sessin if loop is closed

Version 0.0.8
================================================================================

* Set min code coverage to 90
* Improve session close and reopen automatically

Version 0.0.7
--------------------------------------------------------------------------------

* Fix code example

Version 0.0.6
--------------------------------------------------------------------------------

* Fix code example
* Remove .pytest_cache
* Add test

Version 0.0.5
--------------------------------------------------------------------------------

* Make close work for older aiohttp

Version 0.0.4
--------------------------------------------------------------------------------

* Drop min Python to 3.5

Version 0.0.3
--------------------------------------------------------------------------------

* Fix setup.py

Version 0.0.2
--------------------------------------------------------------------------------

* Fix readme
* Add aiohttp wrapper
* Initial commit
