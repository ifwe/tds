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


@then(u'the response contains a list of {num} items')
def then_the_response_contains_a_list_of_items(context, num):
    assert len(context.response.json()) == int(num), context.response


@then(u'the response contains a project with {properties}')
def then_the_response_contains_a_project_with(context, properties):
    properties = parse_properties(properties)
    assert any(all(properties[prop] == proj[prop] for prop in properties)
               for proj in context.response.json())


@then(u'the response is a project with {properties}')
def then_the_response_is_a_project_with(context, properties):
    properties = parse_properties(properties)
    assert all(properties[prop] == context.response.json()[prop] for prop in
               properties), (context.response.json(), properties)
