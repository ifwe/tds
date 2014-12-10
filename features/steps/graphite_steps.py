"""Graphite steps for feature tests."""

from behave import given, then

from ..environment import add_config_val


@given(u'graphite notifications are enabled')
def given_graphite_notifications_are_enabled(context):
    add_config_val(context, 'notifications',
                   dict(enabled_methods=['graphite']))


@then(u'there is a graphite notification with {snippets}')
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
    assert len(notifications) == number
