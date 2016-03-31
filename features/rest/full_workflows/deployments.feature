Feature: A full deployment workflow run
    As a developer
    I want to deploy code programmatically through the API
    So that I can push my code out more efficiently and quickly

    Background:
        Given I have a cookie with user permissions
        And there is an application with pkg_name="app1"
        And there are packages:
            | version   | revision  | status    |
            | 1         | 1         | completed |
            | 1         | 2         | completed |
            | 2         | 3         | completed |
            | 2         | 4         | completed |
        And there is an application with pkg_name="app2"
        And there are packages:
            | version   | revision  | status    |
            | 3         | 5         | completed |
            | 3         | 6         | completed |
        And there are projects:
            | name  |
            | proj1 |
        And there is an environment with name="dev"
        And there is a deploy target with name="tier1"
        And there are hosts:
            | name  | env   | app_id    |
            | host1 | dev   | 2         |
            | host2 | dev   | 2         |
        And there is a deploy target with name="tier2"
        And there are hosts:
            | name  | env   | app_id    |
            | host3 | dev   | 2         |
            | host4 | dev   | 2         |
        And the tier "tier1" is associated with the application "app1" for the project "proj1"
        And the tier "tier2" is associated with the application "app1" for the project "proj1"

    @rest
    Scenario: do a full deployment to just tiers
        When I query POST "/deployments"
        And I query POST "/tier_deployments?deployment_id=1&tier_id=2&environment_id=1&package_id=1"
        And I query POST "/tier_deployments?deployment_id=1&tier_id=3&environment_id=1&package_id=1"
        And I query PUT "/deployments/1?status=queued"
        Then the response is an object with id=1,status="queued"
        And there is a deployment with id=1,status="queued"
        And there is a tier deployment with deployment_id=1,status="pending",app_id=2,environment_id=1,package_id=1
        And there is a tier deployment with deployment_id=1,status="pending",app_id=3,environment_id=1,package_id=1

    @rest
    Scenario: do a full deployment to just hosts
        When I query POST "/deployments"
        And I query POST "/host_deployments?deployment_id=1&host_id=1&package_id=1"
        And I query POST "/host_deployments?deployment_id=1&host_id=2&package_id=1"
        And I query POST "/host_deployments?deployment_id=1&host_id=3&package_id=1"
        And I query POST "/host_deployments?deployment_id=1&host_id=4&package_id=1"
        And I query PUT "/deployments/1?status=queued"
        Then the response is an object with id=1,status="queued"
        And there is a deployment with id=1,status="queued"
        And there is a host deployment with deployment_id=1,status="pending",host_id=1,package_id=1
        And there is a host deployment with deployment_id=1,status="pending",host_id=2,package_id=1
        And there is a host deployment with deployment_id=1,status="pending",host_id=3,package_id=1
        And there is a host deployment with deployment_id=1,status="pending",host_id=4,package_id=1

    @rest
    Scenario: do a full deployment to tiers and hosts
        When I query POST "/deployments"
        And I query POST "/tier_deployments?deployment_id=1&tier_id=2&environment_id=1&package_id=1"
        And I query POST "/host_deployments?deployment_id=1&host_id=3&package_id=2"
        And I query POST "/host_deployments?deployment_id=1&host_id=4&package_id=2"
        And I query PUT "/deployments/1?status=queued"
        Then the response is an object with id=1,status="queued"
        And there is a deployment with id=1,status="queued"
        And there is a tier deployment with deployment_id=1,status="pending",app_id=2,environment_id=1,package_id=1
        And there is a host deployment with deployment_id=1,status="pending",host_id=1,package_id=1
        And there is a host deployment with deployment_id=1,status="pending",host_id=2,package_id=1
        And there is a host deployment with deployment_id=1,status="pending",host_id=3,package_id=2
        And there is a host deployment with deployment_id=1,status="pending",host_id=4,package_id=2
