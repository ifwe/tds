Feature: application update application properties
    As a user
    I want to update aspects of an application
    To reflect current needs and changes

    Scenario: attempt for an application that doesn't exist
        Given there is an environment with name="dev"
        And I am in the "dev" environment
        And I have "dev" permissions
        When I run "application update myapp job_name=new_job"
        Then the output is "Application does not exist: myapp"

    Scenario Outline: invalid properties
        Given there is an environment with name="dev"
        And I am in the "dev" environment
        And I have "dev" permissions
        And there is an application with name="myapp"
        When I run "application update myapp <properties>"
        Then the output is "Invalid properties: <prop_list>. Split on '=' once for the declaration fake_prop returned 1 argument, expected 2"
        And there is an application with name="myapp",arch="noarch",path="job",deploy_type="rpm",build_host="fakeci.example.org",build_type="jenkins"

        Examples:
            | properties                    | prop_list                         |
            | fake_prop                     | ['fake_prop']                     |
            | job_name=new_job fake_prop    | ['job_name=new_job', 'fake_prop'] |

    Scenario Outline: pass an attribute more than once
        Given there is an environment with name="dev"
        And I am in the "dev" environment
        And I have "admin" permissions
        And there is an application with name="myapp"
        When I run "application update myapp <properties>"
        Then the output is "Attribute appeared more than once: <attr>"
        And there is an application with name="myapp",arch="noarch",path="job",deploy_type="rpm",build_host="fakeci.example.org",build_type="jenkins"

        Examples:
            | properties                    | attr      |
            | name=a name=b                 | name      |
            | job_name=a name=b job_name=c  | job_name  |

    Scenario Outline: attempt update for a properties that don't exist
        Given there is an environment with name="dev"
        And I am in the "dev" environment
        And I have "dev" permissions
        And there is an application with name="myapp"
        When I run "application update myapp <properties>"
        Then the output is "Invalid attribute: fake_prop. Valid attributes are: ('job_name',)"
        And there is an application with name="myapp",arch="noarch",path="job",deploy_type="rpm",build_host="fakeci.example.org",build_type="jenkins"

        Examples:
            | properties                    |
            | fake_prop=fake_val            |
            | job_name=job fake_prop=val    |

    Scenario Outline: insufficient permissions
        Given there is an environment with name="dev"
        And I am in the "dev" environment
        And I have "dev" permissions
        And there is an application with name="myapp"
        When I run "application update myapp <properties>"
        Then the output is "Invalid attribute: name. Valid attributes are: ('job_name',)"
        And there is an application with name="myapp",arch="noarch",path="job",deploy_type="rpm",build_host="fakeci.example.org",build_type="jenkins"

        Examples:
            | properties                    |
            | name=new_name                 |
            | job_name=job name=new_name    |

    Scenario Outline: update with same information as already present in database
        Given there is an environment with name="dev"
        And I am in the "dev" environment
        And I have "<perm>" permissions
        And there is an application with name="myapp",path="job"
        When I run "application update myapp <properties>"
        Then the output is "Update values match current values for application myapp. Nothing to do."
        And there is an application with name="myapp",arch="noarch",path="job",deploy_type="rpm",build_host="fakeci.example.org",build_type="jenkins"

        Examples:
            | perm      | properties                                                                                            |
            | dev       | job_name=job                                                                                          |
            | admin     | job_name=job name=myapp deploy_type=rpm arch=noarch build_type=jenkins build_host=fakeci.example.org  |

    Scenario Outline: unprivileged user updates job_name and/or repository
        Given there is an environment with name="dev"
        And I am in the "dev" environment
        And I have "dev" permissions
        And there are applications:
            | name      | path  | repository                            |
            | myapp     | job   | https://www.example.org/repos/repo1   |
        When I run "application update myapp <params>"
        Then the output describes an application with name="myapp",arch="noarch",deploy_type="rpm",build_host="fakeci.example.org",build_type="jenkins",<description>
        And the output has "Application has been successfully updated."
        And there is an application with name="myapp",arch="noarch",deploy_type="rpm",build_host="fakeci.example.org",build_type="jenkins",<description>
        And there is no application with name="myapp",arch="noarch",path="job",deploy_type="rpm",build_host="fakeci.example.org",build_type="jenkins",repository="https://www.example.org/repos/repo1"

        Examples:
            | params                                                            | description                                                       |
            | job_name=new_job                                                  | path="new_job"                                                    |
            | repository=https://www.example.org/repos/repo2                    | repository="https://www.example.org/repos/repo2"                  |
            | repository=https://www.example.org/repos/repo2 job_name=new_job   | repository="https://www.example.org/repos/repo2",path="new_job"   |
            | job_name=new_job repository=https://www.example.org/repos/repo2   | repository="https://www.example.org/repos/repo2",path="new_job"   |

    Scenario: matrix_build in job_name
        Given there is an environment with name="dev"
        And I am in the "dev" environment
        And I have "dev" permissions
        And there is an application with name="myapp",path="job"
        When I run "application update myapp job_name=new_job&os=centos6.4&lang=python2.7"
        Then the output describes an application with name="myapp",arch="noarch",path="new_job&os=centos6.4&lang=python2.7",deploy_type="rpm",build_host="fakeci.example.org",build_type="jenkins"
        And the output has "Application has been successfully updated."
        And there is an application
            | name          | myapp                                 |
            | arch          | noarch                                |
            | path          | new_job&os=centos6.4&lang=python2.7   |
            | deploy_type   | rpm                                   |
            | build_type    | jenkins                               |
            | build_host    | fakeci.example.org                    |
        And there is no application with name="myapp",arch="noarch",path="job",deploy_type="rpm",build_host="fakeci.example.org",build_type="jenkins"

    Scenario: admin updates application attributes
        Given there is an environment with name="dev"
        And I am in the "dev" environment
        And I have "admin" permissions
        And there are applications:
            | name  | path  | repository                            |
            | myapp | job   | https://www.example.org/repos/repo1   |
        When I run "application update myapp job_name=new_job name=new_name arch=x86_64 deploy_type=rpm build_type=hudson build_host=hudson.example.org repository=https://www.example.org/repos/repo2"
        Then the output describes an application with name="new_name",arch="x86_64",path="new_job",deploy_type="rpm",build_host="hudson.example.org",build_type="hudson",repository="https://www.example.org/repos/repo2"
        And the output has "Application has been successfully updated."
        And there is an application with name="new_name",arch="x86_64",path="new_job",deploy_type="rpm",build_host="hudson.example.org",build_type="hudson",repository="https://www.example.org/repos/repo2"
        And there is no application with name="myapp",arch="noarch",path="job",deploy_type="rpm",build_host="fakeci.example.org",build_type="jenkins",repository="https://www.example.org/repos/repo1"

    Scenario: invalid arch
        Given there is an environment with name="dev"
        And I am in the "dev" environment
        And I have "admin" permissions
        And there is an application with name="myapp",path="job"
        When I run "application update myapp arch=arm"
        Then the output is "Invalid architecture: arm. Should be one of: i386, noarch, x86_64"
        And there is an application with name="myapp",arch="noarch",path="job",deploy_type="rpm",build_host="fakeci.example.org",build_type="jenkins"

    Scenario: invalid build type
        Given there is an environment with name="dev"
        And I am in the "dev" environment
        And I have "admin" permissions
        And there is an application with name="myapp",path="job"
        When I run "application update myapp build_type=travis"
        Then the output is "Invalid build type: travis. Should be one of: developer, hudson, jenkins"
        And there is an application with name="myapp",arch="noarch",path="job",deploy_type="rpm",build_host="fakeci.example.org",build_type="jenkins"
