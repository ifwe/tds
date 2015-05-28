"""
The login URL for the TDS REST API.
"""

import ldap

from cornice.resource import resource, view

from . import settings, utils
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
            l = ldap.open(settings.LDAP_SERVER)
            password = self.request.validated_params['password']
            dn = "uid={username},ou=People,dc=tagged,dc=com".format(
                username=self.request.validated_params['user']
            )
            print l.simple_bind(dn, password)
        except ldap.LDAPError, e:
            self.request.errors.add(
                'query', 'user',
                "Authentication failed. If this problem persists, please"
                " contact SiteOps."
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
