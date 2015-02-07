# TDS 2.0 REST API specification
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
Integrate with LDAP to get tokens for users that are passed with each request
for authentication.
All requests should throw a `401: Unauthorized` without LDAP authentication.

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
As a result, `POST` requests will throw a `403: Forbidden` error in this case.

### PUT
`PUT` requests can only be made to individual resources currently.

## Routing
The URLs and methods will be the same for `/packages` and `/projects` as for
`/applications` below.
URLs and methods will also be the same for `/projects/NAME` as for
`/applications/NAME` below.
URLs and methods for deploying have yet to be determined.

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
            <b>400</b>: Bad request. Illegal attributes or malformed JSON most
                likely.<br />
        </td>
    </tr>
    <tr>
        <td>POST</td>
        <td>Create one or more new applications.</td>
        <td>Attributes for the new application.<br />
            See Attributes section below for details.
        </td>
        <td>
            <b>201</b>: Application(s) created.<br />
            <b>400</b>: Bad request.<br />
            <b>403</b>: Forbidden. Unique constraint violated or lack of
                permissions. Give specifics.<br />
        </td>
    </tr>
    <tr>
        <td rowspan="3">/applications/NAME</td>
        <td>DELETE</td>
        <td>Delete the application with name NAME.</td>
        <td><em>None</em</td>
        <td>
            <b>204</b>: Application deleted. Nothing to return.<br />
            <b>301</b>: Moved permanently. Renamed most likely.
                Return the new URI, as per HTTP/1.1.<br />
            <b>400</b>: Bad request. Malformed name most likely.<br />
            <b>403</b>: Forbidden. Lack of permissions.<br />
            <b>404</b>: Not found.<br />
        </td>
    </tr>
        <td>GET</td>
        <td>Retrieve the application with the name NAME.</td>
        <td><em>None</em></td>
        <td>
            <b>200</b>: Return application.<br />
            <b>301</b>: Moved permanently.
                <em>This may be hard to implement. We would need a column for
                former names for applications.</em><br />
            <b>400</b>: Bad request.<br />
            <b>404</b>: Not found.<br />
            <b>410</b>: Gone. The application has been deleted.
                <em>This may be hard to implement. We would need a table for
                deleted applications.</em><br />
        </td>
    </tr>
    <tr>
        <td>PUT</td>
        <td>Update application with name NAME with new attributes.</td>
        <td>New attributes to set for the application.<br />
            See the Attributes section below for more details.
        </td>
        <td>
            <b>200</b>: Application updated. Return new attributes.<br />
            <b>301</b>: Moved permanently.<br />
            <b>400</b>: Bad request.<br />
            <b>403</b>: Forbidden. Lack of permissions or unique constraint.
                <br />
            <b>404</b>: Not found.<br />
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
by `2015-01-30T23:14:15.926535+0000`.

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
This will be fleshed out more as the API is more solidified.

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
        <td rowspan="7">Application</td>
        <td>'id'</td>
        <td>Number</td>
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
            <td>'job_name'</td>
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
        <td rowspan="2">Project</td>
        <td>'id'</td>
        <td>Number</td>
        <td>Unique integer ID for this project.</td>
        <td>18</td>
    </tr>
        <tr>
            <td>'name'</td>
            <td>String</td>
            <td>Unique name for this project.</td>
            <td>'tds'</td>
        </tr>
    <tr>
        <td rowspan="9">Package</td>
        <td>'id'</td>
        <td>Number</td>
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
            <td>Number</td>
            <td>Package version.</td>
            <td>22</td>
        </tr>
        <tr>
            <td>'revision'</td>
            <td>Number</td>
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
            <td>'creator'</td>
            <td>String</td>
            <td>Name of the creator of the package.</td>
            <td>'knagra'</td>
        </tr>
        <tr>
            <td>'builder'</td>
            <td>String</td>
            <td>Build type for this package.<br />
                Choices: 'developer', 'hudson', 'jenkins'.</td>
            <td>'jenkins'</td>
        </tr>
        <tr>
            <td>'created'</td>
            <td>String</td>
            <td>UNIX timestamp.
                See the section on timestamps above for details.</td>
            <td>2015-01-30T23:14:15.926535+0000</td>
        </tr>
        <tr>
            <td>'application'</td>
            <td>Number</td>
            <td>Unique ID of the application of which this package is a
                specific version-revision.</td>
            <td>16</td>
        </tr>
</tbody>
</table>

## Standing Questions
* Should `GET` requests also have ACL restrictions?
    A REST API would be a good place to start when incorporating ACL since we
    plan to integrate LDAP authentication anyway.
* Should the API support `OPTIONS` and `HEAD` HTTP methods?
    Both can be useful and fairly easy to implement.
    It would make the API more robust and allow lighter-weight queries for
    testing transactions and development.
* Should `POST` requests be allowed to update matching resources as well as
    create new ones if none matches?
    Doing so would be more work for us, but less for clients.
    * If 'Yes' to above, should we allow `POST` requests for /TYPE/NAME URLs?
* Should we expose IDs of objects through the API?
    It may prove useful, especially for resource types without other unique
    attributes, but it may prove unnecessary if no such resources exist.
    * Should we reference objects by other unique constraints or by ID?
        This may be influenced by whether SQLAlchemy returns objects or IDs
        for relations.
        E.g., for packages, an application is linked to each package.
        If SQLAlchemy returns the applciation that is linked to the package,
        then it would be no trouble for the API to return the name of the
        application to the client and have the client reference the
        application with that name. But if SQLAlchemy returns just the ID then
        it will be more overhead to retrieve the name for each application
        using the ID and then pass that on to the client.
* Should we hard-code defaults into the API for certain attributes or expect
    the immediate client to pass in its own determination of defaults?
    A good example of this would be the architecture for applications.
* Should there be a /packages/ID URL or should we do
    /applications/NAME-VERSION-REVISION?
    The former seems more sane and canonical.
