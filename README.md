# TDS
## Author
Kenneth Lareau

## Description
TDS is a deployment system developed at Tagged with a database backend
and a command line frontend.
TDS is written primarily in Python.
MySQL 5.1 was used as the database engine,
and SQLAlchemy as the object-relational mapper,
with Alembic used for SQLAlchemy schema migrations.


## License
<a href="http://opensource.org/licenses/MIT">MIT</a>

## Installation
To install all necessary dependencies and TDS:
```
$ ./setup.py
```

## Dependencies

### PyPI packages
See `requirements.txt`. To install (NOTE: `setup.py` will do this for you):
```
$ pip install -r requirements.txt --allow-all-external --allow-unverified progressbar
```

### Other required packages
* MySQL development library
    * Debian:`sudo apt-get install libmysqlclient-dev`
    * RHEL: `sudo yum install mysql-devel`

## Testing
First, install development requirements
(again, `setup.py` automatically does this for you):
```
$ pip install -r requirements-dev.txt
```

### Unit tests
The following command will run all unit tests:
```
$ ./run_tests.py
```

### Behavior tests
The following command will run all
<a href="//pythonhosted.org/behave/">Behave</a> tests:
```
$ behave
```
You may specify a set of tags to restrict which behavior tests to run:
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
        <td>jenkins_server</td>
        <td>Set up and use a Jenkins server mimic</td>
    </tr>
    <tr>
        <td>wip</td>
        <td>Works in progress</td>
    </tr>
</tbody>
</table>

## Navigation
* [./.jenkins/](./.jenkins/README.md)
* [./doc/](./doc/README.md) -
Documentation
* [./etc/](./etc/README.md)
* [./features/](./features/README.md) -
Behavior tests
* [./pkg/](./pkg/README.md)
* [./share/](./share/README.md)
* [./tds/](./tds/README.md)
* [./tests/](./tests/README.md) -
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