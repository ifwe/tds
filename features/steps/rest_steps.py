"""
Steps for the REST API.
"""


import requests

from behave import given, then, when

from .model_steps import parse_properties


@when(u'I query {method} "{path}"')
def when_i_query(context, method, path):
    """
    Query the rest API at the given URL path with the given method.
    """
    http_method = getattr(requests, method.lower(), None)
    if http_method is None:
        assert False, "Unkown method: {method}".format(method=method)
    context.response = http_method("http://{addr}:{port}{path}".format(
        addr=context.rest_server.server_name,
        port=context.rest_server.server_port,
        path=path,
    ))


@then(u'the response code is {code}')
def then_the_response_code_is(context, code):
    assert int(code) == context.response.status_code, (
        context.response.status_code, code
    )


@then(u'the response is a list of {num} items')
def then_the_response_contains_a_list_of_items(context, num):
    assert len(context.response.json()) == int(num), (
        int(num),
        len(context.response.json())
    )


@then(u'the response list contains an object with {properties}')
def then_the_response_contains_a_project_with(context, properties):
    properties = parse_properties(properties)
    assert any(all(properties[prop] == proj[prop] for prop in properties)
               for proj in context.response.json())


@then(u'the response list contains objects')
def then_the_response_list_contains_objects(context):
    assert all(any(all(row[heading] == obj[heading] for heading in
                       context.table.headings) for obj in
                   context.response.json()) for row in
               context.table.rows), context.response.json()


@then(u'the response is an object with {properties}')
def then_the_response_is_a_project_with(context, properties):
    properties = parse_properties(properties)
    assert all(properties[prop] == context.response.json()[prop] for prop in
               properties), (context.response.json(), properties)


@then(u'the response list contains id range {minimum} to {maximum}')
def then_the_response_list_contains_id_range(context, minimum, maximum):
    """
    Make sure there is an object in the response for each ID
    in [minimum, maximum].
    """
    minimum = int(minimum)
    maximum = int(maximum)
    assert all(any(obj['id'] == x for obj in context.response.json()) for
               x in range(minimum, maximum+1))


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
    assert False, context.response.text
    assert message in context.response.text, (message, context.response.text)
