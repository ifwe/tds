"""HipChat steps for feature tests."""

from behave import then

from .model_steps import parse_properties
from ..environment import add_config_val


@given(u'hipchat notifications are enabled')
def given_hipchat_notifications_are_enabled(context):
    add_config_val(context, 'notifications',
                   dict(enabled_methods=['hipchat']))


@then(u'there is a hipchat notification')
def then_there_is_a_hipchat_notification(context):
    notifications = context.hipchat_server.get_notifications()
    assert notifications is not None
    assert len(notifications) > 0


@then(u'there is a hipchat notification with {properties}')
def then_there_is_a_hipchat_notification_with_message(context, properties):
    context.execute_steps(u"Then there is a hipchat notification")

    notifications = context.hipchat_server.get_notifications()

    attrs = parse_properties(properties)

    for attr in attrs:
        try:
            assert any(req[attr] == attrs[attr] for (req, _) in notifications)
        except KeyError:
            assert False
