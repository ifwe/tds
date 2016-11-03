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

"""Slack steps for feature tests."""

from behave import given, then

from .model_steps import parse_properties
from ..environment import add_config_val


@given(u'slack notifications are enabled')
def given_slack_notifications_are_enabled(context):
    add_config_val(context, 'notifications',
                   dict(enabled_methods=['slack']),
                   use_list=True)


@then(u'there was a slack notification with {properties}')
def then_there_is_a_slack_notification_with(context, properties):
    notifications = context.slack_server.get_notifications()
    assert notifications is not None
    assert len(notifications) > 0

    attrs = parse_properties(properties)

    try:
        assert any(all(req[attr] == attrs[attr] for attr in attrs)
                   for (req, _resp) in notifications)
    except KeyError as e:
        assert False, e


@then(u'a slack notification message contains {snippets}')
def then_there_is_a_slack_notification_with_message_that_contains(context, snippets):
    notifications = context.slack_server.get_notifications()
    assert notifications is not None
    assert len(notifications) > 0

    snippets = snippets.split(',')

    for snippet in snippets:
        assert any(
            eval(snippet) in req['text'] for (req, _resp) in notifications
        )

@then(u'there are {number} slack notifications')
def then_there_are_slack_notifications(context, number):
    number = int(number)

    notifications = context.slack_server.get_notifications()
    assert notifications is not None
    assert len(notifications) == number

@then(u'there is a slack failure')
def then_there_is_a_slack_failure(context):
    notifications = context.slack_server.get_notifications()
    assert notifications is not None
    assert any(resp != 200 for (_req, resp) in notifications)
