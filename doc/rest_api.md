# REST API For Tagged Deployment System (TDS)

This document will cover the various processes one can do within TDS.  It is
a living document currently in beta, and subject to incompatible changes;  let
the user beware!

## Adding a project to TDS

POST /projects

### Data

app_name: **Project name**
build_host: **FQDN of build host**
project_type: **'application' or 'tagconfig'**
pkg_type: **'RPM'**
pkg_name: *(does not need to be sent, same as app_name currently)*
path: **Relative path on build host to packages**

### Expected results
#### HTTP code returned
200 OK

#### Data returned
id: **number** *(should this be serial, or the database ID?)*
env_specific: **0 or 1**
packages: **[]** *(empty list)*

