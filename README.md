# TDS
[![Build Status](https://ci.tagged.com/job/tds-tds-features/badge/icon)](https://ci.tagged.com/job/tds-tds-features/)

## Authors
Kenneth Lareau, Karandeep Nagra

## Description
TDS is a deployment system developed at if(we) with a database backend
and a command line frontend.
The primary application is written in Python and integrates with several
other applications.
MySQL was used as the database engine,
and SQLAlchemy as the object-relational mapper,
with Alembic used for SQLAlchemy schema migrations.

**WARNING**: Consider this code **EXPERIMENTAL**.  It has
not been fully prepared for use outside If(we) though we will be
working on this.  If you have any questions or suggestions, please
email <tds@ifwe.co>

## License
<a href="http://www.apache.org/licenses/LICENSE-2.0">Apache License, Version 2.0</a>

## Installation
To install all necessary dependencies and TDS:

```bash
$ ./setup.py install
```

## Dependencies

## Python

TDS requires python 2.7. Operation under python 3.x would be nice, but that is
not attempted yet.

### PyPI packages
See `requirements.txt`. To install (NOTE: `setup.py` will do this for you):

```bash
$ pip install -r requirements.txt
```

### Other required packages
* MySQL development library
    * Debian: `sudo apt-get install libmysqlclient-dev`
    * RHEL: `sudo yum install mysql-devel`
* LDAP libraries:
    * Debian: `sudo apt-get install libldap2-dev libsasl2-dev`
    * RHEL: `sudo yum install openldap-devel`

## Testing
First, install development requirements
(again, `setup.py` automatically does this for you):

```bash
$ pip install -r requirements-dev.txt
```

### Unit tests

Note: many unit tests currently fail; unit testing does not seem to have kept
up with development.

The following command will run all unit tests:

```bash
$ ./run_tests.py
```

### Feature tests

Note: feature tests depend on infrastructure that no longer exists. To run
feature tests, the test environment needs to be modified to (at least) run a
local mysql server on demand.

The following command will run all
<a href="//pythonhosted.org/behave/">Behave</a> tests:

```bash
$ behave
```

You may specify a set of tags to restrict which feature tests to run:
<table>
<thead>
    <tr>
        <th>Tag</th>
        <th>Specification</th>
    </tr>
</thead>
<tbody>
    <tr>
        <td>no_db</td>
        <td>No database queries</td>
    </tr>
    <tr>
        <td>email_server</td>
        <td>Set up and use an email server mimic</td>
    </tr>
    <tr>
        <td>jenkins_server</td>
        <td>Set up and use a Jenkins server mimic</td>
    </tr>
    <tr>
        <td>hipchat_server</td>
        <td>Set up and use a HipChat server mimic</td>
    </tr>
    <tr>
        <td>wip</td>
        <td>Works in progress</td>
    </tr>
    <tr>
        <td>delay</td>
        <td>Commands with timed delays</td>
    </tr>
</tbody>
</table>

## Navigation
* [./.jenkins/](./.jenkins/)
* [./doc/](./doc/) -
Documentation
* [./etc/](./etc/)
* [./features/](./features/) -
Feature tests
* [./pkg/](./pkg/)
* [./share/](./share/)
* [./tds/](./tds/) -
Models, views, and controllers for TDS application.
* [./tests/](./tests/) -
Unit tests
* [./requirements-dev.txt](./requirements-dev.txt) -
Development and testing PyPI dependencies
* [./requirementx.txt](./requirements.txt) -
Deployment PyPI dependencies
* [./setup.py](./setup.py) -
Complete setup script

## Terminology
Definitions of terms used in this documentation and in source
are listed below.  Controller entries may be incomplete, as some
functions related to object types are spread across the application.
<table>
<thead>
    <tr>
        <th>Term</th>
        <th>Definition</th>
        <th>Examples</th>
        <th>Model - `tds.model.`</th>
        <th>Controller - `tds.commands.`</th>
    </tr>
</thead>
<tbody>
    <tr>
        <td>actor</td>
        <td></td>
        <td></td>
        <td>`actor.Actor`</td>
        <td></td>
    </td>
    <tr>
        <td>application</td>
        <td></td>
        <td></td>
        <td>`application.Application`</td>
        <td></td>
    </tr>
    <tr>
        <td>app type</td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
    </tr>
    <tr>
        <td>deploy target</td>
        <td>Anything on which software can be deployed</td>
        <td>The server SiteOps with IP 10.0.1.10;
        the servers SiteOps1, SiteOps2, and SiteOps3</td>
        <td>`deploy_target.DeployTarget`</td>
        <td></td>
    </tr>
    <tr>
        <td>deployment</td>
        <td>A deployed instance of software</td>
        <td>TDS v1.5 installed on the server SiteOps</td>
        <td>`deployment.Deployment`</td>
        <td>`deploy.DeploymentController`</td>
    </tr>
    <tr>
        <td>package</td>
        <td>A collection of software, commands for installation, dependencies,
        documentation, etc.</td>
        <td>Source and installation commands for Apache, mod_ssl, node.js,
        and MySQL client</td>
        <td>`package.Package`</td>
        <td>`package.PackageController`</td>
    </tr>
    <tr>
        <td>project</td>
        <td>An ongoing or completed endeavor to create
        (or implement) new software</td>
        <td>A new project to efficiently manage software deployment,
        named TDS</td>
        <td>`project.Project`</td>
        <td>`project.ProjectController`</td>
    </tr>
    <tr>
        <td>repository</td>
        <td></td>
        <td></td>
        <td><em>N/A</em></td>
        <td>`repository.RepositoryController`</td>
    </tr>
</tbody>
</table>

## Roadmap
See [roadmap.md](./doc/roadmap.md) for details on the release history and
planned development of TDS.

-----

README.md: Copyright 2016 Ifwe Inc.

README.md is licensed under a Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
