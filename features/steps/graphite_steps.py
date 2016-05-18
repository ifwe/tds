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

"""Graphite steps for feature tests."""

from behave import given, then

from ..environment import add_config_val


@given(u'graphite notifications are enabled')
def given_graphite_notifications_are_enabled(context):
    add_config_val(context, 'notifications',
                   dict(enabled_methods=['graphite']))


@then(u'there is a graphite notification containing {snippets}')
def then_there_is_a_graphite_notification_with(context, snippets):
    notifications = context.graphite_server.get_notifications()
    assert notifications is not None
    assert len(notifications) > 0

    snippets = snippets.split(',')
    assert any(all(eval(snippet) in data for snippet in snippets)
               for data in notifications), (snippets, notifications)


@then(u'there are {number} graphite notifications')
def then_there_are_graphite_notifications(context, number):
    number = int(number)

    notifications = context.graphite_server.get_notifications()
    assert notifications is not None
    assert len(notifications) == number, notifications
