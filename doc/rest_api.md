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
apptypes: **list of application types**  
**OR** hosts: **list of hosts**  
**OR** all_apptypes: true  
delay: **number of seconds** *(optional)*

#### *Example*
apptypes: [ spambuild ]

### Expected results
#### HTTP code returned
200 OK

#### Data returned
id: **number** *(database ID from deployments table)*  
hosts: **list of hosts if hosts were sent**  
apptypes: **list of application types if application types were sent**  
declared: **timestamp**  
status: **'inprogress'**  
environment: **environment**  
user: **user name**

#### *Example*
id: 209  
apptypes: [ spambuild ]  
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
id: **number** *(database ID from deployments table)*  
hosts: **list of hosts if hosts were sent**  
apptypes: **list of application types if application types were sent**  
declared: **timestamp**  
status: **state** *(matches app deployment state or host deployment state)*
environment: **environment**  
user: **user name**

#### *Example*
id: 209  
apptypes: [ spambuild ]  
**Hmm, this is not quite right, needs to be worked on**


## Performing a redeploy via TDS
### Action and endpoint
PUT /project/<em>project name</em>/deploys  *(Not sure what this should be)*

#### *Example*
PUT /project/spambuild/deploys  *(Not sure what this should be)*

### Data
**What should be here??**

### Expected results
#### HTTP code returned
200 OK

#### Data returned
**What should be here??**

#### *Example*
**What should be here??**


## Performing a rollback of a deployment via TDS
### Action and endpoint
DELETE /project/<em>project name</em>/deploys  *(Not sure what this should be)*

#### *Example*
DELETE /project/spambuild/deploys  *(Not sure what this should be)*

### Data
**What should be here??**

### Expected results
#### HTTP code returned
303 See other

#### Data returned
refer: **URL of previous validated deployment**  *(This could be a list?)*

#### *Example*
refer: http://deploy.tagged.com/project/spambuild/package/141/deploy  
**The above may not quite be right**


## Restarting an application via TDS
### Action and endpoint
PUT /project/<em>project name</em>/deploy?restart_only=true  *(Not sure what this should be)*

#### *Example*
PUT /project/spambuild/deploy?restart_only=true  *(Not sure what this should be)*

### Data
**What should be here??**

### Expected results
#### HTTP code returned
200 OK

#### Data returned
**What should be here??**

#### *Example*
**What should be here??**


## Validate/invalidate a deployment (or deployments) in TDS
### Action and endpoint
PUT /project/<em>project name</em>/package/<em>version</em>/deploy/<em>:id</em>[?force=true]  
**Should 'id' be from deployments or app_deployments table?**

#### *Example*
PUT /project/spambuild/package/142/deploy/209

### Data
apptypes: **list of application types**  
**OR** all_apptypes: **'true'**  
status: **'validated' or 'invalidated'**

#### *Example*
apptypes: [ spambuild ]  
status: validated

### Expected results
#### HTTP code returned
200 OK

#### Data returned
**What should be here??**

#### *Example*
**What should be here??**


## Adding or deleting an application type from a project in TDS
### Action and endpoint
PUT /project/<em>project name</em>

#### *Example*
PUT /project/tagconfig

### Data
apptypes: **new list of application types (add/remove entries to be added/removed)**

#### *Example*
*(Removing 'spambuild' from list that also contained 'riskbuild' and 'riskscan')*  
apptypes: [ riskbuild, riskscan ]

### Expected results
#### HTTP code returned
200 OK

### Data returned
apptypes: **updated list of application types**

#### *Example*
apptypes: [ riskbuild, riskscan ]

