Feature: REST API root GET
    As a developer
    I want to get all supported URLs
    So that I can be well informed and probe them later with OPTIONS queries

    @rest
    Scenario: get all URLs
        When I query GET on the root url
        Then the response code is 200
        And the response is a list of 32 items
        And the response list contains objects:
            | url                                                                                       | description                                       |
            | /projects/{name_or_id}/applications/{application_name_or_id}/tiers                        | Collection of all tiers associated with the project and application selected. |
            | /projects/{name_or_id}/applications/{application_name_or_id}/tiers/{tier_name_or_id}      | Individual project-application-tier associations. |
            | /applications                                                                             | Collection of all applications. |
            | /applications/{name_or_id}                                                                | Individual application. |
            | /applications/{name_or_id}/hosts/{host_name_or_id}                                        | Current host deployment of the application on the host. |
            | /applications/{name_or_id}/tiers/{tier_name_or_id}/environments/{environment_name_or_id}  | Current tier deployment of the application on the tier in the environment. |
            | /deployments                                                                              | Collection of deployments. |
            | /deployments/{id}                                                                         | Individual deployment. |
            | /environments                                                                             | Collection of environments. |
            | /environments/{name_or_id}                                                                | Individual environment. |
            | /ganglias                                                                                 | Collection of Ganglias. |
            | /ganglias/{name_or_id}                                                                    | Individual Ganglia. |
            | /hipchats                                                                                 | Collection of HipChats. |
            | /hipchats/{name_or_id}                                                                    | Individual HipChat. |
            | /host_deployments                                                                         | Collection of host deployments. |
            | /host_deployments/{id}                                                                    | Individual host deployment. |
            | /hosts                                                                                    | Collection of hosts. |
            | /hosts/{name_or_id}                                                                       | Individual host. |
            | /login                                                                                    | Get a session cookie for non-OPTIONS requests. |
            | /packages                                                                                 | Collection of packages. |
            | /packages/{id}                                                                            | Individual package. |
            | /applications/{name_or_id}/packages                                                       | Collection of packages for the application. |
            | /applications/{name_or_id}/packages/{version}/{revision}                                  | Package specified by the application, version, and revision. |
            | /projects                                                                                 | Collection of projects. |
            | /projects/{name_or_id}                                                                    | Individual project. |
            | /search/{obj_type}                                                                        | Search for objects of type obj_type. |
            | /tier_deployments                                                                         | Collection of tier deployments. |
            | /tier_deployments/{id}                                                                    | Individual tier deployment. |
            | /tiers/{name_or_id}/hipchats                                                              | Collection of HipChats associated with the tier. |
            | /tiers/{name_or_id}/hipchats/{hipchat_name_or_id}                                         | A HipChat association with a tier. |
            | /tiers                                                                                    | Collection of tiers. |
            | /tiers/{name_or_id}                                                                       | Individual tier.    |
        And the response list has an object with property "obj_type_choices" which lists:
            | application       |
            | application_tier  |
            | deployment        |
            | environment       |
            | ganglia           |
            | hipchat           |
            | host              |
            | host_deployment   |
            | package           |
            | project           |
            | tier              |
            | tier_deployment   |
