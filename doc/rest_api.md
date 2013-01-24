# REST API For Tagged Deployment System (TDS)

This document will cover the various processes one can do within TDS.  It is
a living document currently in beta, and subject to incompatible changes;  let
the user beware!

## Adding a project to TDS
### Endpoint
POST /projects

### Data
app_name: **Project name**  
build_host: **FQDN of build host**  
project_type: **'application' or 'tagconfig'**  
pkg_type: **'RPM'**  
pkg_name: *(does not need to be sent, same as app_name currently)*  
path: **Relative path on build host to packages**

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

