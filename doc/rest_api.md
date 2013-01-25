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
packages: **empty list**

#### *Example*
id: 18  
env_specific: 0  
packages: []


## Retrieving information about a project in TDS
### Action and endpoint
GET /project/<em>project name</em>

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
POST /project/<em>project name</em>/packages

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
GET /project/<em>project name</em>/package/<em>version</em>

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


## Perform a deployment via TDS
### Action and endpoint
POST /project/<em>project name</em>/package/<em>version</em>/deploys

#### *Example*
POST /project/spambuild/package/142/deploys

### Data
apptypes: **list of application type objects**  
**OR** hosts: **list of hosts**  
**OR** all_apptypes: true  
delay: **number of seconds** *(optional)*

#### *Example*
apptypes: [ { name: spambuild } ]

### Expected results
#### HTTP code returned
200 OK

#### Data returned
id: **number** *(database ID from deployments table)*  
hosts: **list of hosts if hosts were sent**  
apptypes: **list of application type objects if any were sent**  
declared: **timestamp**  
status: **'inprogress'**  
environment: **environment**  
user: **user name**

#### *Example*
id: 209  
apptypes: [ { name: spambuild } ]  
declared: 2012-11-12 12:08:12  
status: inprogress  
environment: development  
user: aneilson


## Get current state of a deployment (or deployments) via TDS
### Action and endpoint
GET /project/<em>project name</em>/deploys[?<em>options</em>]

#### *Examples*
GET /project/spambuild/deploys?id=209  
GET /project/spambuild/deploys?status=inprogress  
GET /project/spambuild/deploys?user=aneilson  
GET /project/spambuild/deploys?environment=staging

### Expected results
#### HTTP code returned
200 OK

#### Data returned
List of objects of the following:

id: **number** *(database ID from deployments table)*  
hosts: **list of hosts if hosts were sent**  
apptypes: **list of application type objects if any were sent**  
declared: **timestamp**  
status: **state** *(matches app deployment state or host deployment state)*  
environment: **environment**  
user: **user name**

#### *Example*
[  
&nbsp;&nbsp;{ id: 209,  
&nbsp;&nbsp;&nbsp;&nbsp;  apptypes: [ { name: spambuild } ],  
&nbsp;&nbsp;&nbsp;&nbsp;  declared: 2012-11-12 12:08:12,  
&nbsp;&nbsp;&nbsp;&nbsp;  status: inprogress,  
&nbsp;&nbsp;&nbsp;&nbsp;  environment: development,  
&nbsp;&nbsp;&nbsp;&nbsp;  user: aneilson  
&nbsp;&nbsp;},  
&nbsp;&nbsp;[...]  
]

## Performing a redeploy via TDS
### Action and endpoint
PUT /project/<em>project name</em>/package/latest/deploys

#### *Example*
PUT /project/spambuild/package/latest/deploys

### Data
apptypes: **list of application type objects**  
**OR** hosts: **list of hosts**  
**OR** all_apptypes: true  
delay: **number of seconds** *(optional)*

### Expected results
#### HTTP code returned
200 OK

#### Data returned
id: **number** *(database ID from deployments table)*  
hosts: **list of hosts if hosts were sent**  
apptypes: **list of application type objects if any were sent**  
declared: **timestamp**  
status: **state** *(matches app deployment state or host deployment state)*  
environment: **environment**  
user: **user name**

#### *Example*
id: 209  
apptypes: [ { name: spambuild } ]  
declared: 2012-11-12 12:08:12  
status: inprogress  
environment: development  
user: aneilson


## Performing a rollback of a deployment via TDS
### Action and endpoint
DELETE /project/<em>project name</em>/package/latest/deploys

#### *Example*
DELETE /project/spambuild/package/latest/deploys

### Data
apptypes: **list of application type objects**  
**OR** hosts: **list of hosts**  
**OR** all_apptypes: true  
delay: **number of seconds** *(optional)*

### Expected results
#### HTTP code returned
If a single apptype or host:  
&nbsp;&nbsp;&nbsp;&nbsp;303 See other  
Else:  
&nbsp;&nbsp;&nbsp;&nbsp;200 OK

#### Data returned
If HTTP code 303:  
&nbsp;&nbsp;&nbsp;&nbsp;refer: **URL of previous validated deployment**  
Else:  
&nbsp;&nbsp;&nbsp;&nbsp;**None**

#### *Example*
If HTTP code 303:  
&nbsp;&nbsp;&nbsp;&nbsp;refer: http://deploy.tagged.com/project/spambuild/package/141/deploy  


## Restarting an application via TDS
### Action and endpoint
PUT /project/<em>project name</em>/package/latest/deploy?restart_only=true

#### *Example*
PUT /project/spambuild/package/latest/deploy?restart_only=true

### Data
apptypes: **list of application type objects**  
**OR** hosts: **list of hosts**  
**OR** all_apptypes: true  
delay: **number of seconds** *(optional)*

### Expected results
#### HTTP code returned
200 OK

#### Data returned
id: **number** *(database ID from deployments table)*  
hosts: **list of hosts if hosts were sent**  
apptypes: **list of application type objects if any were sent**  
declared: **timestamp**  
status: **state** *(matches app deployment state or host deployment state)*  
environment: **environment**  
user: **user name**

#### *Example*
id: 209  
apptypes: [ { name: spambuild } ]  
declared: 2012-11-12 12:08:12  
status: inprogress  
environment: development  
user: aneilson


## Validate/invalidate a deployment (or deployments) in TDS
### Action and endpoint
PUT /project/<em>project name</em>/package/<em>version</em>/deploy/<em>:id</em>[?force=true]  
*':id' is from deployments table*

#### *Example*
PUT /project/spambuild/package/142/deploy/209

### Data
apptypes: **list of application type objects**  
**OR** all_apptypes: **'true'**  
status: **'validated' or 'invalidated'**

#### *Example*
apptypes: [ { name: spambuild } ]  
status: validated

### Expected results
#### HTTP code returned
200 OK

#### Data returned
id: **number** *(database ID from deployments table)*  
hosts: **list of hosts if hosts were sent**  
apptypes: **list of application type objects if any were sent**  
declared: **timestamp**  
status: **'validated' or 'invalidated'**  
environment: **environment**  
user: **user name**

#### *Example*
id: 209  
apptypes: [ { name: spambuild } ]  
declared: 2012-11-12 12:08:12  
status: validated  
environment: development  
user: aneilson


## Adding an application type from a project in TDS
### Action and endpoint
POST /project/<em>project name</em>/apptypes

#### *Example*
POST /project/tagconfig/apptypes

### Data
apptypes: **list of application type objects to be added**

#### *Example*
apptypes: [ { name: spambuild } ]

### Expected results
#### HTTP code returned
200 OK

### Data returned
apptypes: **list of application type objects just added**

#### *Example*
apptypes: [ { name: spambuild } ]


## Deleting an application type from a project in TDS
### Action and endpoint
DELETE /project/<em>project name</em>/apptypes

#### *Example*
DELETE /project/tagconfig/apptypes

### Data
apptypes: **list of application type objects to be removed**

#### *Example*
apptypes: [ { name: spambuild } ]

### Expected results
#### HTTP code returned
200 OK

### Data returned
**None**


## Getting all application types for a project in TDS
### Action and endpoint
GET /project/<em>project name</em>/apptypes

#### *Example*
GET /project/tagconfig/apptypes

### Expected results
#### HTTP code returned
200 OK

### Data returned
apptypes: **list of application type objects**

#### *Example*
apptypes: [ { name: spambuild }, { name: riskbuild }, { name: riskscan } ]

