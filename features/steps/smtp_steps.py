"""Modified SMTP server for feature tests"""

import email
import json
import os
import pwd
import re
import yaml

from behave import given, then

from ..environment import add_config_val
from .model_steps import parse_properties


@given(u'email notification is enabled')
def email_notification_is_enabled(context):
    add_config_val(context, 'notifications',
                   dict(enabled_methods=['email']),
                   use_list=True)


@given(u'the email server is broken')
def email_server_is_broken(context):
    add_config_val(context, 'notifications.email',
                   dict(receiver='serverfail@example.com'))


def compare_values(src, dest, key):
    assert(src[key] == dest[key]), (src[key], dest[key])


def verify_email_contents(context, attrs):
    with open(os.path.join(context.EMAIL_SERVER_DIR, 'message.json')) as fh:
        email_data_list = json.loads(fh.read())

    with open(context.TDS_CONFIG_FILE) as fh:
        deploy_info = yaml.load(fh.read())

    curr_user = pwd.getpwuid(os.getuid())[0]
    attrs['curr_user'] = curr_user
    curr_receiver = deploy_info['notifications']['email']['receiver']

    original_data = dict(
        sender=curr_user,
        receiver=[curr_user + '@ifwe.co', curr_receiver],
    )

    for email_data in email_data_list:
        for key in ['sender', 'receiver']:
            compare_values(original_data, email_data, key)

        email_content = email.message_from_string(email_data['contents'])
        email_headers = dict(email_content._headers)
        email_subject = ''.join(email_headers['Subject'].split('\n'))
        email_body = ''.join(email_content._payload.split('\n'))

        if 'unvalidated' in attrs:
            subject_re = re.compile(
                r'\[TDS\] ATTENTION: %(name)s in %(environment)s for '
                r'%(targets)s app tier needs validation\!' % attrs, flags=re.I
            )
            body_re = re.compile(
                r'Version %(version)s of package %(name)s in %(targets)s '
                r'app tier\\nhas not been validated. Please validate it.\\n'
                r'Without this, Puppet cannot manage the tier correctly.'
                % attrs, flags=re.S
            )
        else:
            subject_re = re.compile(
                r'\[TDS\] %(deptype)s of version %(version)s of %(name)s '
                r'on %(targtype)s %(targets)s in %(env)s' % attrs, flags=re.I
            )
            body_re = re.compile(
                r'%(curr_user)s performed a "tds deploy %(deptype)s" for the '
                r'following %(targtype)s in %(env)s:    %(targets)s' % attrs,
                flags=re.S
            )

        assert subject_re.match(email_subject), \
            (email_subject, subject_re.pattern, subject_re.flags)
        assert body_re.match(email_body), \
            (email_body, body_re.pattern, body_re.flags)


@then(u'no email is sent')
def no_email_is_sent(context):
    assert not os.path.isfile(
        os.path.join(context.EMAIL_SERVER_DIR, 'message.json')
    )


@then(u'an email is sent with the relevant information for {properties}')
def email_is_sent_with_relevant_information(context, properties):
    attrs = parse_properties(properties)
    attrs.update({
        'version': context.tds_packages[-1].version,
        'name': context.tds_packages[-1].pkg_name,
        'env': context.tds_env,
        'environment': context.tds_environment,
    })

    if attrs.get('apptypes', None) is not None:
        attrs.update({
            'targtype': r'app tier\(s\)',
            'targets': ', '.join(attrs['apptypes'].split(':')),
        })
    elif attrs.get('hosts', None) is not None:
        attrs.update({
            'targtype': r'hosts',
            'targets': ', '.join(attrs['hosts'].split(':')),
        })
    else:
        assert False, 'Should never reach this'

    verify_email_contents(context, attrs)


@then(u'there is a failure message for the email send')
def there_is_failure_message_for_email_send(context):
    stderr = context.process.stderr

    assert 'Mail server failure' in stderr, stderr


@then(u'an email is sent with repo update info with {properties}')
def then_an_email_is_sent_with_repo_update_info_with(context, properties):
    attrs = parse_properties(properties)
    with open(os.path.join(context.EMAIL_SERVER_DIR, 'message.json')) as fh:
        email_data_list = json.loads(fh.read())

    if attrs.get('sender', None) is not None:
        sender = attrs.pop('sender')
        assert any(email['sender'] == sender for email in email_data_list), (sender, email_data_list)
    if attrs.get('receiver', None) is not None:
        receiver = attrs.pop('receiver')
        assert any(receiver in email['receiver'] for email in email_data_list), (receiver, email_data_list)
    if attrs.keys():
        assert False, "Unable to process attrs: {keys}".format(keys=attrs.keys())


@then(u'an email is sent with repo update contents containing "{text}"')
def then_an_email_is_sent_with_repo_update_contents_containing(context, text):
    with open(os.path.join(context.EMAIL_SERVER_DIR, 'message.json')) as fh:
        email_data_list = json.loads(fh.read())

    try:
        assert any(text in email['contents'] for email in email_data_list), (text, email_data_list)
    except KeyError as err:
        assert False, "Key error: {err}, {l}".format(err=err, l=email_data_list)
