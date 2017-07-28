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

"""Signalfx steps for feature tests."""

from behave import given, then

from .model_steps import parse_properties
from ..environment import add_config_val


@given(u'signalfx notifications are enabled')
def given_signalfx_notifications_are_enabled(context):
    add_config_val(context, 'notifications',
                   dict(enabled_methods=['signalfx']),
                   use_list=True)


@then(u'there was a signalfx notification with {properties}')
def then_there_is_a_signalfx_notification_with(context, properties):
    notifications = context.signalfx_server.get_notifications()
    assert notifications is not None
    assert len(notifications) > 0

    attrs = parse_properties(properties)

    try:
        assert any(all(req[attr] == attrs[attr] for attr in attrs)
                   for (req, _resp) in notifications)
    except KeyError as e:
        assert False, e

@then(u'there are {number} signalfx notifications')
def then_there_are_signalfx_notifications(context, number):
    number = int(number)

    notifications = context.signalfx_server.get_notifications()
    assert notifications is not None
    assert len(notifications) == number

@then(u'there is a signalfx failure')
def then_there_is_a_signalfx_failure(context):
    notifications = context.signalfx_server.get_notifications()
    assert notifications is not None
    assert any(resp != 200 for (_req, resp) in notifications)
