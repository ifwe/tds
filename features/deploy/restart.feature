# Copyright 2016 Ifwe Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

Feature: deploy restart application [--delay] [--hosts|--apptypes|--all-apptypes]
    As a user
    I want to be able to restart the application on a set of targets
    So I can have changes take effect on those targets

    Background:
        Given I have "dev" permissions
        And there is an environment with name="dev"
        And I am in the "dev" environment
        And there is a project with name="proj"
        And there is an application with name="myapp"
        And there is a deploy target with name="appfoo"
        And the deploy target is a part of the project-application pair
        And there are hosts:
            | name          | env   |
            | appfoo01      | dev   |
            | appfoo02      | dev   |
        And the hosts are associated with the deploy target
        And there is a package with version="123"
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment

    Scenario: too few arguments
        When I run "deploy restart"
        Then the output has "usage:"

    Scenario: invalid argument
        When I run "deploy restart myapp --foo"
        Then the output has "usage:"

    Scenario: restart an application that doesn't exist
        When I run "deploy restart badapp"
        Then the output is "Application does not exist: badapp"

    Scenario: restart an application for an apptype that doesn't exist
        When I run "deploy restart myapp --apptypes badapp"
        Then the output has "Valid apptypes for application "myapp" are: ['appfoo']"

    Scenario: restart an application for several apptypes where one apptype doesn't exist
        When I run "deploy restart myapp --apptypes appfoo badapp"
        Then the output has "Valid apptypes for application "myapp" are: ['appfoo']"

    Scenario: restart an application for a host that doesn't exist
        When I run "deploy restart myapp --hosts badhost"
        Then the output has "Host does not exist: badhost"

    Scenario: restart an application for several hosts where one host doesn't exist
        When I run "deploy restart myapp --hosts appfoo01 badhost"
        Then the output has "Host does not exist: badhost"

    Scenario Outline: restart an application with a single apptype (w/ and w/o option)
        Given the deploy strategy is "<strategy>"
        When I run "deploy restart myapp <option>"
        Then package "myapp" was restarted on the deploy target
        And the output has "appfoo01:		[success]"
        And the output has "appfoo02:		[success]"

        Examples:
        | option            | strategy |
        |                   | salt     |
        | --apptypes appfoo | salt     |

    Scenario Outline: restart an application with multiple apptypes with no option
        Given there is a deploy target with name="appbar"
        And the deploy strategy is "<strategy>"
        And the deploy target is a part of the project-application pair
        When I run "deploy restart myapp"
        Then the output has "Specify a target constraint (too many targets found: appbar, appfoo)"

        Examples:
        | strategy |
        | salt     |

    Scenario Outline: restart an application with multiple apptypes with apptypes option
        Given there is a deploy target with name="appbar"
        And the deploy strategy is "<strategy>"
        And the deploy target is a part of the project-application pair
        And there is a host with name="appbar01"
        And the host is associated with the deploy target
        When I run "deploy restart myapp --apptypes appfoo"
        Then package "myapp" was restarted on the deploy target with name="appfoo"
        And the output has "appfoo01:		[success]"
        And the output has "appfoo02:		[success]"

        Examples:
        | strategy |
        | salt     |

    Scenario Outline: restart an application with multiple apptypes with all-apptypes option
        Given there is a deploy target with name="appbar"
        And the deploy strategy is "<strategy>"
        And there are hosts:
            | name          |
            | appbar01      |
            | appbar02      |
        And the hosts are associated with the deploy target
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy targets in the "dev" env
        And the package has been validated in the "development" environment
        When I run "deploy restart myapp --all-apptypes"
        Then package "myapp" was restarted on the deploy targets
        And the output has "appfoo01:		[success]"
        And the output has "appfoo02:		[success]"
        And the output has "appbar01:		[success]"
        And the output has "appbar02:		[success]"

        Examples:
        | strategy |
        | salt     |

    Scenario Outline: restart an application with a single target in the hosts option
        Given the deploy strategy is "<strategy>"
        When I run "deploy restart myapp --hosts appfoo01"
        Then package "myapp" was restarted on the host with name="appfoo01"
        And the output has "appfoo01:		[success]"

        Examples:
        | strategy |
        | salt     |

    Scenario Outline: restart an application with multiple targets in the hosts option
        Given the deploy strategy is "<strategy>"
        When I run "deploy restart myapp --hosts appfoo01 appfoo02"
        Then package "myapp" was restarted on the hosts
        And the output has "appfoo01:		[success]"
        And the output has "appfoo02:		[success]"

        Examples:
        | strategy |
        | salt     |

    # Note: the delay option actually will wait after the final host as well;
    #       this should probably be fixed (or the behavior changed based on
    #       given situation

    @delay
    Scenario Outline: restart an application with a valid delay option involving a single target
        Given the deploy strategy is "<strategy>"
        When I run "deploy restart myapp --delay 10 --hosts appfoo01"
        Then package "myapp" was restarted on the host with name="appfoo01"
        And the output has "appfoo01:		[success]"

        Examples:
        | strategy |
        | salt     |

    Scenario Outline: restart an application with an invalid delay option involving a single target
        Given the deploy strategy is "<strategy>"
        When I run "deploy restart myapp --delay notnum --hosts appfoo01"
        Then the output has "error: argument --delay: invalid int value:"

        Examples:
        | strategy |
        | salt     |

    Scenario Outline: restart an application with an invalid delay option involving mulitple targets
        Given the deploy strategy is "<strategy>"
        When I run "deploy restart myapp --delay notnum --apptypes appfoo"
        Then the output has "error: argument --delay: invalid int value:"

        Examples:
        | strategy |
        | salt     |

    @delay
    Scenario Outline: restart an application with a valid delay option involving multiple targets
        Given the deploy strategy is "<strategy>"
        When I run "deploy restart myapp --delay 10 --apptypes appfoo"
        Then package "myapp" was restarted on the deploy target
        And the output has "appfoo01:		[success]"
        And the output has "appfoo02:		[success]"
        And it took at least 10 seconds

        Examples:
        | strategy |
        | salt     |

    Scenario Outline: restart an application where at least one of the targets fails when restarting a tier
        Given the deploy strategy is "<strategy>"
        And the host "appfoo01" will fail to restart
        When I run "deploy restart myapp"
        Then the output has "appfoo01:		[failed]"
        And the output has "It done broked!"
        And the output has "appfoo02:		[success]"

        Examples:
        | strategy |
        | salt     |

    Scenario Outline: restart an application where at least one of the targets fails when restarting a target or targets
        Given the deploy strategy is "<strategy>"
        And the host "appfoo01" will fail to restart
        When I run "deploy restart myapp --hosts appfoo01 appfoo02"
        Then the output has "appfoo01:		[failed]"
        And the output has "It done broked!"
        And the output has "appfoo02:		[success]"

        Examples:
        | strategy |
        | salt     |

    Scenario Outline: restart on a tier with no hosts
        Given there is a deploy target with name="anotherapp"
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy targets in the "dev" env
        And the deploy strategy is "<strategy>"
        When I run "deploy restart myapp --apptypes anotherapp"
        Then the output has "No hosts for tier anotherapp in environment development. Continuing..."
        And the output has "Nothing to restart for application myapp in development environment."

        Examples:
        | strategy |
        | salt     |

    Scenario Outline: restart all tiers, including a tier with no hosts
        Given there is a deploy target with name="anotherapp"
        And the deploy target is a part of the project-application pair
        And the package is deployed on the deploy targets in the "dev" env
        And the deploy strategy is "<strategy>"
        When I run "deploy restart myapp --all-apptypes"
        Then the output has "No hosts for tier anotherapp in environment development. Continuing..."
        And package "myapp" was restarted on the host with name="appfoo01"
        And package "myapp" was restarted on the host with name="appfoo02"
        And the output has "appfoo01:		[success]"
        And the output has "appfoo02:		[success]"

        Examples:
        | strategy |
        | salt     |

    Scenario Outline: restart on hosts with just a host deployment
        Given there is a deploy target with name="anotherapp"
        And there are hosts:
            | name          | env   | app_id    |
            | anotherhost01 | dev   | 3         |
            | anotherhost02 | dev   | 3         |
        And the deploy target is a part of the project-application pair
        And the package is deployed on the hosts
        And the deploy strategy is "<strategy>"
        When I run "deploy restart myapp --hosts anotherhost01 anotherhost02"
        Then package "myapp" was restarted on the host with name="anotherhost01"
        And package "myapp" was restarted on the host with name="anotherhost02"
        And the output has "anotherhost01:		[success]"
        And the output has "anotherhost02:		[success]"

        Examples:
        | strategy  |
        | salt      |
