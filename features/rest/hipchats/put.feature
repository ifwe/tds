Feature: PUT HipChat(s) from the REST API
    As an admin
    I want to change a HipChat object
    So that the database reflects the current state of the environment

    Background:
        Given I have a cookie with admin permissions
        And there is a HipChat with room_name="hipchat1"
        And there is a HipChat with room_name="hipchat2"

    @rest
    Scenario Outline: update a HipChat object that doesn't exist
        When I query PUT "/hipchats/<select>?name=newname"
        Then the response code is 404
        And the response contains errors:
            | location  | name          | description                               |
            | path      | name_or_id    | Hipchat with <descript> does not exist.   |
        And there is no HipChat with room_name="newname"

        Examples:
            | select    | descript      |
            | noexist   | name noexist  |
            | 500       | ID 500        |

    @rest
    Scenario Outline: update a HipChat object
        When I query PUT "/hipchats/<select>?name=newname"
        Then the response code is 200
        And the response is an object with name="newname",id=1
        And there is a HipChat with room_name="newname",id=1

        Examples:
            | select    |
            | hipchat1  |
            | 1         |

    @rest
    Scenario Outline: pass an invalid parameter
        When I query PUT "/hipchats/<select>?<query>"
        Then the response code is 422
        And the response contains errors:
            | location  | name  | description                                           |
            | query     | foo   | Unsupported query: foo. Valid parameters: ['name'].   |
        And there is a HipChat with room_name="hipchat1",id=1

        Examples:
            | select    | query                 |
            | hipchat1  | foo=bar               |
            | 1         | name=newname&foo=bar  |
            | hipchat1  | name=newname&foo=bar  |
            | 1         | name=newname&foo=bar  |
            | hipchat1  | foo=bar&name=newname  |
            | 1         | foo=bar&name=newname  |

    @rest
    Scenario Outline: attempt to violate a unique constraint
        When I query PUT "/hipchats/<select>?name=hipchat2"
        Then the response code is 409
        And the response contains errors:
            | location  | name  | description                                                                   |
            | query     | name  | Unique constraint violated. Another hipchat with this name already exists.    |

        Examples:
            | select    | query         |
            | hipchat1  | name=hipchat2 |
            | 1         | name=hipchat2 |
