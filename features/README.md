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
* [./application/](./application/) -
Test for the `application` command.
* [./authorization/](./authorization/) -
Authorization and permissions tests.
* [./deploy/](./deploy/) -
Tests for the `deploy` command.
* [./helpers/](./helpers/) -
Helper applications for deployment tests.
* [./notification/](./notification/) -
Tests for supported notifications.
* [./package/](./package/) -
Tests for the `package` command.
* [./project/](./project/) -
Tests for the `project` command.
* [./steps/](./steps/) -
Behave <a href="http://pythonhosted.org/behave/api.html#step-functions"
target="_blank">steps</a>.
* [./environment.py](./environment.py) -
Behave
<a href="http://pythonhosted.org/behave/api.html#environment-file-functions"
target="_blank">environment</a>.
Defines functions to be run before and after certain events during testing.

-----

README.md: Copyright 2016 Ifwe Inc.

README.md is licensed under a Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
