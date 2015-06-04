"""
The login URL for the TDS REST API.
"""

import ldap

from cornice.resource import resource, view

from . import utils
from .base import BaseView, init_view

@resource(path="/login")
class LoginView(BaseView):
    """
    View to log in and get a cookie for use later.
    """

    types = {
        'user': 'string',
        'password': 'string',
    }

    required_post_fields = ('user', 'password')

    def validate_login(self, _request):
        """
        Authenticate the user.
        """
        if self.request.errors:
            return
        try:
            l = ldap.initialize(self.settings['ldap_server'])
            password = self.request.validated_params['password']
            dn = "uid={username},ou=People,dc=tagged,dc=com".format(
                username=self.request.validated_params['user']
            )
            l.simple_bind(dn, password)
        except ldap.SERVER_DOWN:
            self.request.errors.add('url', '',
                                    "Could not connect to LDAP server.")
            self.request.errors.status = 500
        except ldap.LDAPError, e:
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
        response = self.make_response("SUCCESS")
        utils.set_cookie(
            response,
            self.request.validated_params['user'],
            self.request.remote_addr,
        )
        return response
