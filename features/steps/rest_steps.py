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

"""
Steps for the REST API.
"""

import os

from os.path import join as opj

import json
import requests
import yaml

from behave import given, then, when

import tds.utils

from .model_steps import parse_properties


def _get_adminuser_info(context):
    testconf_path = None
    local_path = opj(context.PROJECT_ROOT, 'features', 'testconf.yml')
    global_path = opj(tds.utils.config.TDSConfig.default_conf_dir,
                      'testconf.yml')
    if os.path.exists(local_path):
        testconf_path = local_path
    elif os.path.exists(global_path):
        testconf_path = global_path
    else:
        raise IOError(
            "Could not find test configuration file at {local_path} "
            "or {global_path}.".format(local_path=local_path,
                                       global_path=global_path)
        )

    with open(testconf_path) as testconf_file:
        testconf = yaml.load(testconf_file)
        if ('adminuser' in testconf and 'username' in testconf['adminuser']
                and 'password' in testconf['adminuser']):
            username = testconf['adminuser']['username']
            password = testconf['adminuser']['password']
        else:
            raise KeyError('Test admin username and password not found '
                           'in {testconf_file}'.format(
                testconf_file=testconf_file
            ))

    return username, password


def _set_cookie(context, username, password, query_dict=None):
    if query_dict is None:
        query_dict = dict()
    query_dict['username'] = username
    query_dict['password'] = password
    response = requests.post(
        "http://{addr}:{port}/login".format(
            addr=context.rest_server.server_name,
            port=context.rest_server.server_port,
        ),
        data=json.dumps(query_dict),
    )
    assert 'session' in response.cookies, (
        "Authentication failed: {resp}".format(resp=response)
    )
    context.cookie = response.cookies['session']


@given(u'I have a cookie with {perm_type} permissions')
def given_i_have_a_cookie_with_permissions(context, perm_type):
    """
    Add a cookie at context.cookie with the permission type perm_type.
    """
    if perm_type == 'user':
        _set_cookie(context, 'testuser', 'secret')
    elif perm_type == 'admin':
        admin_name, admin_pw = _get_adminuser_info(context)
        _set_cookie(context, admin_name, admin_pw)
    else:
        assert False, ("Unknown permission type: {p}. "
                       "Valid options: user, admin.".format(p=perm_type))


@given(u'I have a cookie with {perm_type} permissions and {restrictions}')
def given_i_have_a_cookie_with_restrictions(context, perm_type, restrictions):
    """
    Add a cookie at context.cookie with the given permission type and
    restrictions.
    """
    pairs = [pair.split('=', 1) for pair in restrictions.split(',')]
    query_dict = dict()
    for key, val in pairs:
        if key == 'eternal':
            val = val in ('True', 'true', '1')
        query_dict[key] = val
    if perm_type == 'user':
        _set_cookie(context, 'testuser', 'secret', query_dict)
    elif perm_type == 'admin':
        _set_cookie(context, 'testadmin', 'removed', query_dict)
    else:
        assert False, ("Unknown permission type: {p}. "
                       "Valid options: user, admin.".format(p=perm_type))


@given(u'I set the cookie {prop} to {value}')
def given_i_set_the_cookie_prop_to_value(context, prop, value):
    pairs = [pair.split('=', 1) for pair in context.cookie.split('&')]
    cookie_string = ''
    for key, val in pairs:
        if key == prop:
            val = value
        cookie_string += '{key}={val}&'.format(key=key, val=val)
    context.cookie = cookie_string[:-1]


@given(u'I increment the cookie issued stamp by {increment}')
def given_i_increment_the_cookie_issued_stamp_by(context, increment):
    pairs = [pair.split('=', 1) for pair in context.cookie.split('&')]
    cookie_string = ''
    for key, val in pairs:
        if key == 'issued':
            val = str(int(val) + int(increment))
        cookie_string += '{key}={val}&'.format(key=key, val=val)
    context.cookie = cookie_string[:-1]


@given(u'I remove {prop} from the cookie')
def given_i_remove_prop_from_the_cookie(context, prop):
    pairs = [pair.split('=', 1) for pair in context.cookie.split('&')]
    cookie_string = ''
    for key, val in pairs:
        if key == prop:
            continue
        cookie_string += '{key}={val}&'.format(key=key, val=val)
    context.cookie = cookie_string[:-1]


@given(u'I have set the request headers {properties}')
def given_i_have_set_the_request_headers(context, properties):
    properties = parse_properties(properties)
    context.request_headers = properties


@given(u'I have disabled redirect following')
def given_i_have_disabled_redirect_following(context):
    context.follow_redirects = False


@when(u'I query {method} on the root url')
def when_i_query_on_the_root_url(context, method):
    when_i_query(context, method, '')


@when(u'I query {method} "{path}"')
def when_i_query(context, method, path):
    _execute_query(context, method, path)


@when(u'I POST "{body}" to "{path}"')
def when_i_query_with_body(context, body, path):
    _execute_query(context, 'POST', path, body)


def _execute_query(context, method, path, body=None):
    """
    Query the rest API at the given URL path with the given method.
    """
    http_method = getattr(requests, method.lower(), None)
    if http_method is None:
        assert False, "Unkown method: {method}".format(method=method)

    if not getattr(context, 'request_headers', None):
        context.request_headers = dict()

    if getattr(context, 'follow_redirects', None) is None:
        context.follow_redirects = True

    if getattr(context, 'cookie', None):
        context.response = http_method(
            "http://{addr}:{port}{path}".format(
                addr=context.rest_server.server_name,
                port=context.rest_server.server_port,
                path=path,
            ),
            data=body if body is not None else '',
            allow_redirects=context.follow_redirects,
            headers=context.request_headers,
            cookies=dict(session=context.cookie),
        )
    else:
        context.response = http_method(
            "http://{addr}:{port}{path}".format(
                addr=context.rest_server.server_name,
                port=context.rest_server.server_port,
                path=path,
            ),
            data=body if body is not None else '',
            allow_redirects=context.follow_redirects,
            headers=context.request_headers,
        )


@then(u'the response code is {code}')
def then_the_response_code_is(context, code):
    assert int(code) == context.response.status_code, (
        context.response.status_code, code, context.response.text
    )


@then(u'the response is a list of {num} items')
def then_the_response_contains_a_list_of_items(context, num):
    assert len(context.response.json()) == int(num), (
        int(num),
        len(context.response.json())
    )


@then(u'the response list contains an object with {properties}')
def then_the_response_list_contains_an_object_with(context, properties):
    properties = parse_properties(properties)
    assert any(all(properties[prop] == obj[prop] for prop in properties)
               for obj in context.response.json())


@then(u'the response list contains objects')
def then_the_response_list_contains_objects(context):
    assert all(any(all(row[heading] == obj[heading] for heading in
                       context.table.headings) for obj in
                   context.response.json()) for row in
               context.table.rows), (context.response.json(), context.table.rows)


@then(u'the response is an object with {properties}')
def then_the_response_is_an_object_with(context, properties):
    properties = parse_properties(properties)
    try:
        assert all(properties[prop] == context.response.json()[prop] for prop
                   in properties), (context.response.json(), properties)
    except (KeyError, TypeError) as e:
        assert False, (e, context.response.json())


@then(u'the response object does not contain attributes {attrs}')
def then_the_response_object_does_not_contain_attributes(context, attrs):
    attrs = attrs.split(',')
    assert all(attr not in context.response.json() for attr in attrs), (
        attrs, context.response.json()
    )


@then(u'the response object contains attributes {attrs}')
def then_the_response_object_contains_attributes(context, attrs):
    attrs = attrs.split(',')
    assert all(attr in context.response.json() for attr in attrs), (
        attrs, context.response.json()
    )


@then(u'the response object has keys {keys}')
def then_the_response_object_has_keys(context, keys):
    keys = keys.split(',')
    obj = context.response.json()
    for key in keys:
        assert key in obj, (key, obj)


@then(u'the response list objects do not contain attributes {attrs}')
def then_the_response_list_objects_do_not_contain_attributes(context, attrs):
    attrs = attrs.split(',')
    assert all(all(attr not in obj for attr in attrs) for obj in
               context.response.json()), (attrs, context.response.json())


@then(u'the response list contains id range {minimum} to {maximum}')
def then_the_response_list_contains_id_range(context, minimum, maximum):
    """
    Make sure there is an object in the response for each ID
    in [minimum, maximum].
    """
    minimum = int(minimum)
    maximum = int(maximum)
    assert all(any(obj['id'] == x for obj in context.response.json()) for
               x in range(minimum, maximum + 1))


@then(u'the response contains errors')
def then_the_response_contains_errors(context):
    """
    Check the errors of the response JSON for the given errors.
    """
    errors = context.response.json()['errors']
    props = ('location', 'name', 'description')
    assert all(any(all(row[prop] == err[prop] for prop in props)
                   for err in errors) for row in context.table), errors


@then(u'the response body contains "{message}"')
def then_the_response_body_contains(context, message):
    assert message in context.response.text, (message, context.response.text)


@then(u'the response body does not contain "{message}"')
def then_the_response_body_does_not_contain(context, message):
    assert message not in context.response.text, (message,
                                                  context.response.text)


@then(u'the response body is empty')
def then_the_response_body_is_empty(context):
    assert len(context.response.text) == 0, context.response.text


@then(u'the response contains a cookie')
def then_the_response_contains_a_cookie(context):
    assert len(context.response.cookies) > 0, context.response.cookies


@then(u'the response contains a cookie with {properties}')
def then_the_response_contains_a_cookie_with(context, properties):
    assert len(context.response.cookies) > 0, context.response.cookies
    assert properties in context.response.cookies['session'], (
        context.response.cookies['session']
    )


@then(u'the response does not contain a cookie')
def then_the_response_does_not_contain_a_cookie(context):
    assert len(context.response.cookies) == 0, context.response.cookies


@then(u'the response header contains a location with "{snippet}"')
def then_the_response_header_contains_a_location_with(context, snippet):
    assert snippet in context.response.headers['location'], (
        context.response.headers['location']
    )


@then(u'the response header contains "{name}" set to "{value}"')
def then_the_response_header_contains_name_set_to_value(context, name, value):
    assert value == context.response.headers[name], (
        context.response.headers[name]
    )


@then(u'the response list has an object with property "{prop}" which lists')
def then_the_response_list_contains_object_property_listing(context, prop):
    matched = False
    for obj in context.response.json():
        if prop in obj and type(obj[prop]) == list:
            if all(
                x[0] in obj[prop] for x in context.table
            ):
                matched = True
                break
    assert matched, context.response.text


def _set_user_type(context, username, user_type):
    user_type = '{user_type}_users'.format(user_type=user_type)
    with open(opj(context.PROJECT_ROOT, 'tds', 'views', 'rest',
                  'settings.yml'), 'r+') as f:
        if user_type not in context.rest_settings:
            context.rest_settings[user_type] = list()
        context.rest_settings[user_type].append(username)
        f.truncate()
        f.write(
            yaml.dump(context.rest_settings, default_flow_style=False)
        )


@given(u'"{username}" is a {user_type} user in the REST API')
def given_username_is_a_user_type_user_in_the_rest_api(
    context, username, user_type
):
    _set_user_type(context, username, user_type)


@given(u'"{username}" is an {user_type} user in the REST API')
def given_username_is_an_user_type_user_in_the_rest_api(
    context, username, user_type
):
    _set_user_type(context, username, user_type)


@given(u'I change cookie life to {val}')
def given_i_change_cookie_life_to(context, val):
    val = int(val)
    with open(opj(context.PROJECT_ROOT, 'tds', 'views', 'rest',
                  'settings.yml'), 'r+') as f:
        context.rest_settings['cookie_life'] = val
        f.truncate()
        f.write(
            yaml.dump(context.rest_settings, default_flow_style=False)
        )


@then(u'the response object conforms to the bystander expectation')
def then_the_test_conforms_to_the_bystander_expectation(context):
    obj = context.response.json()
    app_mapping = {'2': "app1", '3': "app2", '4': "app3"}
    tier_mapping = {'2': "tier1", '3': "tier2", '4': "tier3"}
    for tier_id in ['2', '3', '4']:
        assert tier_id in obj, obj
        assert obj[tier_id]['name'] == tier_mapping[tier_id]
        assert obj[tier_id]['status'] == 'active'
        assert tier_id in obj[tier_id], obj[tier_id]
        assert obj[tier_id][tier_id]['name'] == app_mapping[tier_id]
        env_dict = obj[tier_id][tier_id]
        if tier_id == '2':
            assert env_dict['1']['package_id'] == 1
            assert env_dict['2']['package_id'] == 2
            assert env_dict['3']['package_id'] == 3
            assert env_dict['1']['package_revision'] == '1'
            assert env_dict['2']['package_revision'] == '2'
            assert env_dict['3']['package_revision'] == '3'
            assert env_dict['1']['package_version'] == '1'
            assert env_dict['2']['package_version'] == '2'
            assert env_dict['3']['package_version'] == '3'
            assert env_dict['1']['name'] == 'dev'
            assert env_dict['2']['name'] == 'stage'
            assert env_dict['3']['name'] == 'prod'
            assert env_dict['prod_ahead']
            assert env_dict['stage_ahead']
        elif tier_id == '3':
            assert env_dict['1']['package_id'] == 4
            assert env_dict['2']['package_id'] == 6
            assert env_dict['3']['package_id'] == 5
            assert env_dict['1']['package_revision'] == '4'
            assert env_dict['2']['package_revision'] == '6'
            assert env_dict['3']['package_revision'] == '5'
            assert env_dict['1']['package_version'] == '1'
            assert env_dict['2']['package_version'] == '3'
            assert env_dict['3']['package_version'] == '2'
            assert env_dict['1']['name'] == 'dev'
            assert env_dict['2']['name'] == 'stage'
            assert env_dict['3']['name'] == 'prod'
            assert not env_dict['prod_ahead']
            assert env_dict['stage_ahead']
        else:
            assert env_dict['1']['package_id'] == 9
            assert env_dict['2']['package_id'] == 8
            assert env_dict['3']['package_id'] == 7
            assert env_dict['1']['package_revision'] == '9'
            assert env_dict['2']['package_revision'] == '8'
            assert env_dict['3']['package_revision'] == '7'
            assert env_dict['1']['package_version'] == '3'
            assert env_dict['2']['package_version'] == '2'
            assert env_dict['3']['package_version'] == '1'
            assert env_dict['1']['name'] == 'dev'
            assert env_dict['2']['name'] == 'stage'
            assert env_dict['3']['name'] == 'prod'
            assert not env_dict['prod_ahead']
            assert not env_dict['stage_ahead']


@then(u'the response object conforms to the performance expectation')
def then_the_response_conforms_to_the_performance_expectation(context):
    returned = context.response.json()
    models = (
        'packages', 'tier_deployments', 'host_deployments', 'deployments',
    )
    month = '2016-01'
    for model in models:
        assert any(obj['month'] == month for obj in returned[model])
    assert returned['packages'][0]['failed'] == 1
    assert returned['packages'][0]['completed'] == 1
    assert returned['packages'][0]['removed'] == 1
    assert returned['packages'][0]['pending'] == 1
    assert returned['packages'][0]['processing'] == 1
    assert returned['packages'][0]['total'] == 5
    assert returned['deployments'][0]['pending'] == 2
    assert returned['deployments'][0]['failed'] == 1
    assert returned['deployments'][0]['inprogress'] == 1
    assert returned['deployments'][0]['queued'] == 1
    assert returned['deployments'][0]['total'] == 5
    assert returned['tier_deployments'][0]['complete'] == 1
    assert returned['tier_deployments'][0]['incomplete'] == 1
    assert returned['tier_deployments'][0]['inprogress'] == 1
    assert returned['tier_deployments'][0]['pending'] == 1
    assert returned['tier_deployments'][0]['validated'] == 1
    assert returned['tier_deployments'][0]['total'] == 5
    assert returned['host_deployments'][0]['ok'] == 3
    assert returned['host_deployments'][0]['failed'] == 1
    assert returned['host_deployments'][0]['pending'] == 1
    assert returned['host_deployments'][0]['total'] == 5
    assert returned['packages'][1]['failed'] == 0
    assert returned['packages'][1]['completed'] == 0
    assert returned['packages'][1]['removed'] == 0
    assert returned['packages'][1]['pending'] == 0
    assert returned['packages'][1]['processing'] == 0
    assert returned['packages'][1]['total'] == 0
    assert returned['deployments'][1]['pending'] == 0
    assert returned['deployments'][1]['failed'] == 0
    assert returned['deployments'][1]['inprogress'] == 0
    assert returned['deployments'][1]['queued'] == 0
    assert returned['deployments'][1]['total'] == 0
    assert returned['tier_deployments'][1]['complete'] == 0
    assert returned['tier_deployments'][1]['incomplete'] == 0
    assert returned['tier_deployments'][1]['inprogress'] == 0
    assert returned['tier_deployments'][1]['pending'] == 0
    assert returned['tier_deployments'][1]['validated'] == 0
    assert returned['tier_deployments'][1]['total'] == 0
    assert returned['host_deployments'][1]['ok'] == 0
    assert returned['host_deployments'][1]['failed'] == 0
    assert returned['host_deployments'][1]['pending'] == 0
    assert returned['host_deployments'][1]['total'] == 0
