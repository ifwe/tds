# REST API For Tagged Deployment System (TDS)

This document will cover the various processes one can do within TDS.  It is
a living document currently in beta, and subject to incompatible changes;  let
the user beware!

## Adding a project to TDS
### Action and endpoint
POST /projects

### Data
app_name: **project name**  
build_host: **FQDN of build host**  
project_type: **'application' or 'tagconfig'**  
pkg_type: **'RPM'**  
pkg_name: *(does not need to be sent, same as app_name currently)*  
path: **relative path on build host to packages**

#### *Example*
app_name: spambuild  
build_host: djavabuild01.tag-dev.com  
project_type: application  
pkg_type: RPM  
path: spambuild

### Expected results
#### HTTP code returned
200 OK

#### Data returned
id: **number** *(database ID from package_locations table)*  
env_specific: **0 or 1**  
packages: **[]** *(empty list)*

#### *Example*
id: 18  
env_specific: 0  
packages: []


## Retrieving information about a project in TDS
### Action and endpoint
GET /project/*project name*

#### *Example*
GET /project/spambuild

### Expected results
#### HTTP code returned
200 OK

#### Data returned
id: **number** *(database ID from package_locations table)*  
env_specific: **0 or 1**  
packages: **list of existing packages**  

#### *Example*
id: 18  
env_specific: 0  
packages: [ ... ]


## Adding a package for a project to TDS
### Action and endpoint
POST /project/*project name*/packages

#### *Example*
POST /project/spambuild/packages

### Data
pkg_name: *(currently not sent, same as project name)*  
version: **number**  
revision: **number** *(currently not sent, hardcoded to 1)*  
builder: *(unused at this point)*  
project_type: **'application' or 'tagconfig'** *(optional, unused at this point)*

#### *Example*
version: 142

### Expected results
#### HTTP code returned
200 OK

#### Data returned
id: **number** *(database ID from packages table)*  
version: **number**  
revision: **number**  
project: **list of associated project names**  
created: **timestamp**

#### *Example*
id: 194  
version: 142  
revision: 1  
project: [ spambuild ]  
created: 2012-11-12 12:06:55


## Retrieving information about a package in TDS
### Action and endpoint
GET /project/*project name*/package/*version*

#### *Example*
GET /project/spambuild/package/142

### Expected results
#### HTTP code returned
200 OK

#### Data returned
id: **number** *(database ID from packages table)*  
version: **number**  
revision: **number**  
project: **list of associated project names**  
created: **timestamp**

#### *Example*
id: 194  
version: 142  
revision: 1  
project: [ spambuild ]  
created: 2012-11-12 12:06:55

