"""
The login URL for the TDS REST API.
"""

import ldap

from cornice.resource import resource, view

from . import utils
from .base import BaseView
from .urls import ALL_URLS


@resource(path=ALL_URLS['login'])
class LoginView(BaseView):
    """
    View to log in and get a cookie for use later.
    """

    name = 'login'

    types = {
        'user': 'string',
        'password': 'string',
    }

    individual_allowed_methods = dict(
        POST=dict(
            description="Authenticate and get a session cookie.",
            returns="Session cookie attached at cookies->session.",
            permissions='none',
        ),
    )

    param_descriptions = {
        'user': 'LDAP username to use for authentication',
        'password': 'String password to use for authentication',
    }

    required_post_fields = ('user', 'password')

    def validate_login(self, _request):
        """
        Authenticate the user.
        """
        if self.request.errors:
            return
        try:
            ldap_conn = ldap.initialize(self.settings['ldap_server'])
            password = self.request.validated_params['password']
            domain_name = "uid={username},ou=People,dc=tagged,dc=com".format(
                username=self.request.validated_params['user']
            )
            ldap_conn.bind_s(domain_name, password)
            results = ldap_conn.search_s(
                "cn=siteops,ou=Groups,dc=tagged,dc=com",
                ldap.SCOPE_BASE
            )
            try:
                self.request.is_admin = (
                    self.request.validated_params['user'] in
                    [member for result in results for member in
                     result[1]['memberUid']]
                )
            except (KeyError, IndexError):
                self.request.is_admin = False
            ldap_conn.unbind()
        except ldap.SERVER_DOWN:
            self.request.errors.add('url', '',
                                    "Could not connect to LDAP server.")
            self.request.errors.status = 500
        except ldap.LDAPError:
            self.request.errors.add(
                'query', 'user',
                "Authentication failed. Please check your username and "
                "password and try again."
            )
            self.request.errors.status = 401

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_login'))
    def post(self):
        """
        Handle a POST request after the parameters are marked valid JSON.
        """
        if 'X-Forwarded-For' in self.request.headers:
            remote_addr = \
                self.request.headers['X-Forwarded-For'].split(', ')[0]
        else:
            remote_addr = self.request.remote_addr
        response = self.make_response("SUCCESS")
        utils.set_cookie(
            response,
            self.request.validated_params['user'],
            remote_addr,
            self.settings,
            self.request.is_admin,
        )
        return response

    @view(validators=('method_not_allowed',))
    def delete(self):
        pass

    @view(validators=('method_not_allowed',))
    def put(self):
        pass

    @view(validators=('method_not_allowed',))
    def get(self):
        pass
