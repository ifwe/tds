# Feature Tests

## Description
Feature tests for TDS.  To run all tests, execute
```
$ behave
```
from the [root directory](./..) of TDS.

For more information on the structure of
<a href="//pythonhosted.org/behave/" target="_blank">Behave</a>
tests, please see the
<a href="//pythonhosted.org/behave/api.html" target="_blank">API
documentation</a> for Behave.

## Navigation
* [./authorizations/](./authorizations/) -
Authorization and permissions tests.
* [./config/](./config/) -
Tests for the `config` command.
* [./deploy/](./deploy/) -
Tests for the `deploy` command.
* [./helpers/](./helpers/)
Helper applications for deployment tests.
* [./notification/](./notification/)
Tests for supported notifications.
* [./package/](./package/) -
Tests for the `package` command.
* [./steps/](./steps/) -
Behave <a href="http://pythonhosted.org/behave/api.html#step-functions"
target="_blank">steps</a>.
* [./environment.py](./environment.py) -
Behave
<a href="http://pythonhosted.org/behave/api.html#environment-file-functions"
target="_blank">environment</a>.
Defines functions to be run before and after certain events during testing.
