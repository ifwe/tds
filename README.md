# TDS
## Authors
* Kenneth Lareau
* Mike Dougherty
* Christopher Stelma
* Corey Hickey

## Description
TDS is a deployment system developed at Tagged....

## License
<a href="http://www.apache.org/licenses/LICENSE-2.0">Apache License, Version 2.0</a>

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
pip install -r requirements-dev.txt
```

### Unit tests
The following command will run all unit tests:
```
$ ./run_tests.py
```

### Behavioral tests
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
        <td></td>
    </tr>
    <tr>
        <td>wip</td>
        <td>Works in progress</td>
    </tr>
</tbody>
</table>

### Logical Structure
<em>Link to logical structure file in `/docs` (function of each package)</em>
