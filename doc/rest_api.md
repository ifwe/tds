# TDS 2 REST API specification
Some quick notes:

* All data in requests and responses is in JSON
* All `GET` requests to resource type roots (e.g., `/applications`) return lists
    of matching resources.
    Well-behave clients should query URLs for specific resources (e.g,
    `/applications/tds`) when only that resource is desired rather than query
    the resource root or searching for that resource with a query.

## Terminology

* Collection URL: The URL for interacting with collections of resources
    (e.g., `/applications`)
* Individual URL: The URL for interacting with a single known resource
    (e.g., `/applications/tds`)

## LDAP integration
This API integrates with LDAP for authentication and authorization.
Post to `/login` with your LDAP login credentials to receive a session cookie
to be used for the duration of your session.
Session cookies are valid, as of 2016-02-04, for 15 days since time of issuance.
All requests other than to `/login` throw a `401: Unauthorized` without LDAP
authentication.

## Methods Overview

### DELETE
Returns nothing for successful `DELETE` requests.

### GET
All `200` responses to `GET` requests are:

* lists of matching objects for resource collection URLs.
* JSON objects for individual resource URLs.

### POST
`POST` requests run queries to see if any unique constraints will be violated
by a potential write to the database before doing the actual write.
They also check for the validity of foreign key relationships.
As a result, `POST` requests will throw a `403: Forbidden` error in this case.

### PUT
`PUT` requests can only be made to individual resources currently.

## Routing
The URLs and methods will be the same for `/projects`, `/ganglias`, `/hipchats`,
`/hosts`, `/tiers`, `/deployments`, `/host_deployments`, and `/tier_deployments`
as for `/applications` below.
URLs and methods will also be the same for `/projects/NAME` as for
`/applications/NAME` below.

### Path-Method Table
<table>
<thead>
    <tr>
        <th>URL</th>
        <th>Method</th>
        <th>Operation</th>
        <th>Request</th>
        <th>Response</th>
    </tr>
</thead>
<tbody>
    <tr>
        <td rowspan="2">/applications</td>
        <td>GET</td>
        <td>Retrieve the full details, including the unique IDs, for all
            applications</td>
        <td>'limit': Number of applications to return.<br />
            'start': Starting position for returned queries, by ID. If 'start'
            = 10, then all applications with ID >= 10 will be returned.
        </td>
        <td>
            <b>200</b>: Return all matching applications. Can be empty list.
                <br />
            <b>401</b>: Authentication required. Cookie not present, valid,
                and/or unexpired.<br />
            <b>422</b>: Unprocessable entity. Illegal attributes or malformed
            JSON most likely.<br />
        </td>
    </tr>
    <tr>
        <td>POST</td>
        <td>Create a new applications.</td>
        <td>Attributes for the new application.<br />
            See Attributes section below for details.
        </td>
        <td>
            <b>201</b>: Application created. Return application JSON.<br />
            <b>400</b>: Bad request.<br />
            <b>401</b>: Authentication required. Cookie not present, valid,
                and/or unexpired.<br />
            <b>403</b>: Forbidden. Lack of permissions.<br />
            <b>409</b>: Conflict. Unique constraint violated. Check errors in
                response for specifics.<br />
        </td>
    </tr>
    <tr>
        <td rowspan="3">/applications/NAME_OR_ID</td>
        <td>DELETE</td>
        <td>Delete the application with name or ID NAME_OR_ID.</td>
        <td><em>None</em</td>
        <td>
            <b>204</b>: Application deleted. Nothing to return.<br />
            <b>301</b>: Moved permanently. Renamed most likely.
                Return the new URI, as per HTTP/1.1.<br />
            <b>401</b>: Authentication required. Cookie not present, valid,
                and/or unexpired.<br />
            <b>403</b>: Forbidden. Lack of permissions.<br />
            <b>404</b>: Not found.<br />
        </td>
    </tr>
    <tr>
        <td>GET</td>
        <td>Retrieve the application with the name or ID NAME_OR_ID.</td>
        <td><em>None</em></td>
        <td>
            <b>200</b>: Return application.<br />
            <b>301</b>: Moved permanently.
                <em>This may be hard to implement. We would need a column for
                former names for applications.</em><br />
            <b>400</b>: Bad request.<br />
            <b>401</b>: Authentication required. Cookie not present, valid,
                and/or unexpired.<br />
            <b>404</b>: Not found.<br />
            <b>410</b>: Gone. The application has been deleted.
                <em>This may be hard to implement. We would need a table for
                deleted applications.</em><br />
        </td>
    </tr>
    <tr>
        <td>PUT</td>
        <td>Update application with name or ID NAME_OR_ID with new attributes.
            </td>
        <td>New attributes to set for the application.<br />
            See the Attributes section below for details.
        </td>
        <td>
            <b>200</b>: Application updated. Return new attributes.<br />
            <b>301</b>: Moved permanently.<br />
            <b>400</b>: Bad request.<br />
            <b>401</b>: Authentication required. Cookie not present, valid,
                and/or unexpired.<br />
            <b>403</b>: Forbidden. Lack of permissions.<br />
            <b>404</b>: Not found.<br />
            <b>409</b>: Conflict. Unique constraint violated.<br />
        </td>
    </tr>
    <tr>
        <td rowspan="2">/applications/NAME_OR_ID/packages</td>
        <td>GET</td>
        <td>Get all packages for the application with name or ID NAME_OR_ID,
            paginated by 'limit' or 'start', optionally.</td>
        <td>
            'limit': Number of packages to return.
            'start': Starting position for returned queries, by ID.
            If 'start' = 10, then all packages with ID >= 10 will be returned.
        </td>
        <td>
            <b>200</b>: Packages found and returned.<br />
            <b>401</b>: Authentication required. Cookie not present, valid,
                and/or unexpired.<br />
            <b>404</b>: No such application found.<br />
            <b>422</b>: Bad query.<br />
        </td>
    </tr>
    <tr>
        <td>POST</td>
        <td>Add a new package for the given application with the given
            attributes.</td>
        <td>
            Attributes for the new package. See the Attributes section below
            for details.
        </td>
        <td>
            <b>201</b>: Package created. Return package JSON.<br />
            <b>400</b>: Bad request.<br />
            <b>401</b>: Authentication required. Cookie not present, valid,
                and/or unexpired.<br />
            <b>403</b>: Forbidden. Lack of permissions. Check errors in
                response for specifics.<br />
            <b>409</b>: Conflict. Unique constraint violated.<br />
        </td>
    </tr>
    <tr>
        <td rowspan="3">/applications/NAME_OR_ID/packages/VERSION/REVISION</td>
        <td>DELETE</td>
        <td>Get the package with version VERSION, revision REVISION for
            application with name or ID NAME_OR_ID.</td>
        <td><em>None</em></td>
        <td>
            <b>204</b>: Package delete. Nothing to return.<br />
            <b>401</b>: Authentication required. Cookie not present, valid,
                and/or unexpired.<br />
            <b>404</b>: Application or package not found. See errors in
                response for specifics.<br />
        </td>
    </tr>
    <tr>
        <td>GET</td>
        <td>Delete the given package.</td>
        <td><em>None</em></td>
        <td>
            <b>200</b>: Return package.<br />
            <b>401</b>: Authentication required. Cookie not present, valid,
                and/or unexpired.<br />
            <b>404</b>: Not found.<br />
        </td>
    </tr>
    <tr>
        <td>PUT</td>
        <td>Update this package.</td>
        <td>New attributes for this package. See the Attributes section
            below for details.</td>
        <td>
            <b>200</b>: Package updated.<br />
            <b>400</b>: Bad request. See errors in response for specifics.
                Most likely a bad query.<br />
            <b>401</b>: Authentication required. Cookie not present, valid,
                and/or unexpired.<br />
            <b>404</b>: Not found.<br />
            <b>409</b>: Conflict. Unique constraint violated.<br />
        </td>
    </tr>
    <tr>
        <td>/login</td>
        <td>POST</td>
        <td>Get an auth cookie.</td>
        <td>None, but body must be a valid JSON object with attributes
            "username" and "password".
        </td>
        <td>
            <b>200</b>: Success. Cookie attached to response with name 'session'.<br />
            <b>400</b>: Bad request. See errors in response for specifics.
                Most likely a bad query.<br />
            <b>422</b>: Unprocessable entity.<br />
            <b>401</b>: Authentication failed.
        </td>
    </tr>
    <tr>
        <td rowspan="2">/tiers/NAME_OR_ID/hipchats</td>
        <td>GET</td>
        <td>Get all HipChats associated with the tier with name or ID
            NAME_OR_ID.</td>
        <td><em>None. NOTE: this URL does not supported limit or start
            queries</em></td>
        <td>
            <b>200</b>: OK. HipChats returned.<br />
            <b>404</b>: Tier not found.<br />
            <b>422</b>: Unprocessable entity. This status will be returned for
                queries that include the limit or start parameters.
        </td>
    </tr>
    <tr>
        <td>POST</td>
        <td>Associate an existing HipChat with the tier with name or ID
            NAME_OR_ID.</td>
        <td>'id': ID of the HipChat to associate. Takes precedence over name.
            'name': Name of the HipChat to associate. Gives precedence to ID.
        </td>
        <td>
            <b>200</b>: OK. The HipChat was already associated with the tier.<br />
            <b>201</b>: Created. The HipChat was successfully associated with
                the tier.<br />
            <b>400</b>: Either 'name' or 'id' must be provided in the query.<br />
            <b>404</b>: Either the tier or the HipChat does not exist.<br />
            <b>422</b>: Unprocessable entity.
        </td>
    </tr>
    <tr>
        <td rowspan="2">/tiers/NAME_OR_ID/hipchats/HIPCHAT_NAME_OR_ID</td>
        <td>DELETE</td>
        <td>Delete a Tier-HipChat association.</td>
        <td>
            <b>200</b>: HipChat disassociated from tier. HipChat returned.<br />
            <b>404</b>: Tier or tier-HipChat association does not exist.
        </td>
    </tr>
    <tr>
        <td>GET</td>
        <td>Get a HipChat that is associated with the given tier.</td>
        <td><em>None</em></td>
        <td>
            <b>200</b>: OK. HipChat returned.<br />
            <b>404</b>: Tier or tier-HipChat association does not exist.
        </td>
    </tr>
</tbody>
</table>


## Attributes

### Timestamps
Timestamps are represented in the format `YYYY-mm-ddTHH:MM:SS.SSSSSS+HHOO`,
where:

* `YYYY` - four digit year.
* `mm` - two digit month.
* `dd` - two digit day.
* `HH` - two digit hour.
* `MM` - two digit minute.
* `SS.SSSSSS` - float seconds
* `HH` - two digit hour offset from UTC.
* `OO` - two digit minute offset from UTC.

So the datetime for 3:14:15.926535PM PST, 30 January 2015 would be represented
by `2015-01-30T15:14:15.926535+0000`.

Parsing from Python UTC datetimes to timestamps:

```python
import datetime
now = datetime.datetime.utcnow()
json_timestamp = now.isoformat() + '+0000'
```

Converting from timestamps to Python UTC datetimes:

```python
date_format = "%Y-%m-%dT%H:%M:%S"
now = datetime.datetime.strptime(json_timestamp[:19], date_format)
rem = float(js[19:26]) + int(js[26:29]) * 3600 + int(js[29:31]) * 60
now += datetime.timedelta(seconds=rem)
```

The fractions of seconds are lost in translation from Python datetimes to UNIX
timestamps but it is of little consequence as MySQL also strips second
fractions off timestamps.
The data presented by the API and the data present in the database is
therefore identical.

### Attribute Table
This table describes attributes of JSON objects mapped from the corresponding
objects in Python.

<table>
<thead>
    <tr>
        <th>Resource</th>
        <th>Attribute</th>
        <th>Type</th>
        <th>Description</th>
        <th>Example</th>
    </tr>
</thead>
<tbody>
    <tr>
        <td rowspan="9">Application</td>
        <td>'id'</td>
        <td>Integer</td>
        <td>Unique integer ID for this application.</td>
        <td>16</td>
    </tr>
        <tr>
            <td>'name'</td>
            <td>String</td>
            <td>Unique name for this application.</td>
            <td>'tds'</td>
        </tr>
        <tr>
            <td>'job'</td>
            <td>String</td>
            <td>Path on the build server to application's builds.</td>
            <td>'tds-tds-gauntlet'</td>
        </tr>
        <tr>
            <td>'build_host'</td>
            <td>String</td>
            <td>FQDN of the build host for this application.</td>
            <td>'ci.tagged.com'</td>
        </tr>
        <tr>
            <td>'build_type'</td>
            <td>String</td>
            <td>Type of build system.<br />
                Choices: 'developer', 'hudson', 'jenkins'.</td>
            <td>'jenkins'</td>
        </tr>
        <tr>
            <td>'deploy_type'</td>
            <td>String</td>
            <td>Type of package system.</td>
            <td>'rpm'</td>
        </tr>
        <tr>
            <td>'arch'</td>
            <td>String</td>
            <td>Architecture of application's packages.</td>
            <td>'noarch'</td>
        </tr>
        <tr>
            <td>'validation_type'</td>
            <td>String</td>
            <td>The validation type for this application.</td>
            <td>'user'</td>
        </tr>
        <tr>
            <td>'env_specific'</td>
            <td>Boolean</td>
            <td>Whether this application is environment-specific.</td>
            <td>True</td>
    <tr>
        <td rowspan="3">Ganglia</td>
        <td>'id'</td>
        <td>Integer</td>
        <td>Unique integer ID for this Ganglia.</td>
        <td>80</td>
    </tr>
        <tr>
            <td>'name'</td>
            <td>String</td>
            <td>Unique string identifier for this Ganglia.</td>
            <td>'ganglia1'</td>
        </tr>
        <tr>
            <td>'port'</td>
            <td>Integer</td>
            <td>Port for this Ganglia</td>
            <td>986</td>
        </tr>
    <tr>
        <td rowspan="2">HipChat</td>
        <td>'id'</td>
        <td>Integer</td>
        <td>Unique integer ID for this HipChat</td>
        <td>34</td>
    </tr>
        <tr>
            <td>'name'</td>
            <td>String</td>
            <td>Unique name for this HipChat</td>
            <td>'hipchat1'</td>
        </tr>
    <tr>
        <td rowspan="15">Host</td>
        <td>'id'</td>
        <td>Integer</td>
        <td>Unique integer ID for this host</td>
        <td>34</td>
    </tr>
        <tr>
            <td>'name'</td>
            <td>String</td>
            <td>Unique name for this host</td>
            <td>'host1'</td>
        </tr>
        <tr>
            <td>'tier_id'</td>
            <td>Integer</td>
            <td>Foreign key to a tier</td>
            <td>5</td>
        </tr>
        <tr>
            <td>'cage'</td>
            <td>Integer</td>
            <td>Cage location for this host</td>
            <td>10</td>
        </tr>
        <tr>
            <td>'cab'</td>
            <td>String</td>
            <td>Cab location for this host</td>
            <td>'some_cab'</td>
        </tr>
        <tr>
            <td>'rack'</td>
            <td>Integer</td>
            <td>Rack location for this host</td>
            <td>32</td>
        </tr>
        <tr>
            <td>'kernel_version'</td>
            <td>String</td>
            <td>Kernel version running on this host</td>
            <td>'3.19.0-15-generic'</td>
        </tr>
        <tr>
            <td>'console_port'</td>
            <td>String</td>
            <td>Port for the console to this host</td>
            <td>'some_port'</td>
        </tr>
        <tr>
            <td>'power_port'</td>
            <td>String</td>
            <td>Power port for this host</td>
            <td>'some_port'</td>
        </tr>
        <tr>
            <td>'power_circuit'</td>
            <td>String</td>
            <td>Power circuit for this host</td>
            <td>'some_circuit'</td>
        </tr>
        <tr>
            <td>'state'</td>
            <td>String</td>
            <td>Choice of: 'baremetal', 'operational', 'repair', 'parts',
                'reserved', 'escrow'</td>
            <td>'operational'</td>
        </tr>
        <tr>
            <td>'arch'</td>
            <td>String</td>
            <td>Choice of: 'i386', 'noarch', 'x86_64'</td>
            <td>'noarch'</td>
        </tr>
        <tr>
            <td>'distribution'</td>
            <td>String</td>
            <td>Choice of: 'centos5.4', 'centos6.2', 'centos6.4', 'centos6.5',
                'centos7.0', 'centos7.1', 'fedora18', 'rhel5.3', 'rhel6.2',
                'rhel6.3', 'rhel6.4', 'rhel6.5', 'ontap'</td>
            <td>'centos7.1'</td>
        </tr>
        <tr>
            <td>'timezone'</td>
            <td>String</td>
            <td>Timezone for this host</td>
            <td>'PST'</td>
        </tr>
        <tr>
            <td>'environment_id'</td>
            <td>Integer</td>
            <td>ID of this host's environment</td>
            <td>1</td>
        </tr>
    <tr>
        <td rowspan="6">Package</td>
        <td>'id'</td>
        <td>Integer</td>
        <td>Unique integer ID for this package.</td>
        <td>20</td>
    </tr>
        <tr>
            <td>'name'</td>
            <td>String</td>
            <td>Name for this package.</td>
            <td>'tds'</td>
        </tr>
        <tr>
            <td>'version'</td>
            <td>Integer</td>
            <td>Package version.</td>
            <td>22</td>
        </tr>
        <tr>
            <td>'revision'</td>
            <td>Integer</td>
            <td>Package revision.</td>
            <td>24</td>
        </tr>
        <tr>
            <td>'status'</td>
            <td>String</td>
            <td>Status of this package in TDS.<br />
                Choices: 'completed', 'failed', 'pending', 'processing',
                'removed'.</td>
            <td>'completed'</td>
        </tr>
        <tr>
            <td>'builder'</td>
            <td>String</td>
            <td>Build type for this package.<br />
                Choices: 'developer', 'hudson', 'jenkins'.</td>
            <td>'jenkins'</td>
        </tr>
    <tr>
        <td rowspan="2">Project</td>
        <td>'id'</td>
        <td>Integer</td>
        <td>Unique integer ID for this project</td>
        <td>18</td>
    </tr>
        <tr>
            <td>'name'</td>
            <td>String</td>
            <td>Unique name for this project</td>
            <td>'tds'</td>
        </tr>
    <tr>
        <td rowspan="8">Tier</td>
        <td>'id'</td>
        <td>Integer</td>
        <td>Unique integer ID for this tier</td>
        <td>23</td>
    </tr>
        <tr>
            <td>'name'</td>
            <td>String</td>
            <td>Name identifying this tier</td>
            <td>'tier1'</td>
        </tr>
        <tr>
            <td>'distribution'</td>
            <td>String</td>
            <td>Choice of: 'centos5.4', 'centos6.2', 'centos6.4', 'centos6.5',
                'centos7.0', 'centos7.1', 'fedora18', 'rhel5.3', 'rhel6.2',
                'rhel6.3', 'rhel6.4', 'rhel6.5', 'ontap'</td>
            <td>'centos7.1'</td>
        </tr>
        <tr>
            <td>'puppet_class'</td>
            <td>String</td>
            <td>Puppet class for this tier</td>
            <td>'baseclass'</td>
        </tr>
        <tr>
            <td>'ganglia_id'</td>
            <td>Integer</td>
            <td>ID for the ganglia for this tier</td>
            <td>1</td>
        </tr>
        <tr>
            <td>'ganglia_name'</td>
            <td>String</td>
            <td>Ganglia name</td>
            <td>'some_ganglia_thing'</td>
        </tr>
        <tr>
            <td>'status'</td>
            <td>String</td>
            <td>Choice of: 'active', 'inactive'</td>
            <td>'active'</td>
        </tr>
        <tr>
            <td>'hipchats'</td>
            <td>Integers</td>
            <td>Array of HipChat IDs for this tier</td>
            <td>1</td>
        </tr>
    <tr>
        <td rowspan="3">Deployment</td>
        <td>'id'</td>
        <td>Integer</td>
        <td>Unique integer ID for this deployment</td>
        <td>46</td>
    </tr>
        <tr>
            <td>'package_id'</td>
            <td>Integer</td>
            <td>Package being deployment with this deployment</td>
            <td>23</td>
        </tr>
        <tr>
            <td>'status'</td>
            <td>String</td>
            <td>Choice with only 'pending', 'queued', 'canceled' available to
                clients</td>
            <td>'queued'</td>
        </tr>
    <tr>
        <td rowspan="4">Host Deployment</td>
        <td>'id'</td>
        <td>Integer</td>
        <td>Unique integer ID for this host deployment</td>
        <td>23</td>
    </tr>
        <tr>
            <td>'deployment_id'</td>
            <td>Integer</td>
            <td>ID of the deployment to which this host deployment belongs</td>
            <td>46</td>
        </tr>
        <tr>
            <td>'host_id'</td>
            <td>Integer</td>
            <td>ID of the host target for this host deployment</td>
            <td>23</td>
        </tr>
        <tr>
            <td>'status'</td>
            <td>String</td>
            <td>Choice with only 'pending' available to clients</td>
            <td>'pending'</td>
        </tr>
    <tr>
        <td rowspan="5">Tier Deployment</td>
        <td>'id'</td>
        <td>Integer</td>
        <td>Unique integer ID for this tier deployment</td>
        <td>23</td>
    </tr>
        <tr>
            <td>'deployment_id'</td>
            <td>Integer</td>
            <td>ID of the deployment to which this tier deployment belongs</td>
            <td>24</td>
        </tr>
        <tr>
            <td>'tier_id'</td>
            <td>Integer</td>
            <td>ID of the tier target for this tier deployment</td>
            <td>23</td>
        </tr>
        <tr>
            <td>'status'</td>
            <td>String</td>
            <td>Choice with only 'pending' available to clients</td>
            <td>'pending'</td>
        </tr>
        <tr>
            <td>'environment_id'</td>
            <td>Integer</td>
            <td>ID of the environment in which the host targets of this tier
                reside</td>
            <td>1</td>
        </tr>
</tbody>
</table>
