"""HipChat steps for feature tests."""

from behave import then

from .model_steps import parse_properties
from ..environment import add_config_val


@given(u'hipchat notifications are enabled')
def given_hipchat_notifications_are_enabled(context):
    add_config_val(context, 'notifications',
                   dict(enabled_methods=['hipchat']))


@then(u'there is a hipchat notification with {properties}')
def then_there_is_a_hipchat_notification_with(context, properties):
    notifications = context.hipchat_server.get_notifications()
    assert notifications is not None
    assert len(notifications) > 0

    attrs = parse_properties(properties)

    for attr in attrs:
        try:
            assert any(req[attr] == attrs[attr] for (req, _) in notifications)
        except KeyError:
            assert False


@then(u'a hipchat notification message contains {snippets}')
def then_there_is_a_hipchat_notification_with_message_that_contains(context, snippets):
    notifications = context.hipchat_server.get_notifications()
    assert notifications is not None
    assert len(notifications) > 0

    snippets = snippets.split(',')

    for snippet in snippets:
        assert any(
            eval(snippet) in req['message'] for (req, _) in notifications
        )

@then(u'there are {number} hipchat notifications')
def then_there_are_hipchat_notifications(context, number):
    number = int(number)

    notifications = context.hipchat_server.get_notifications()
    assert notifications is not None
    assert len(notifications) == number
