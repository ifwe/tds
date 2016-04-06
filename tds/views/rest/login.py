"""
The login URL for the TDS REST API.
"""

import json
import ldap

from cornice.resource import resource, view

import tagopsdb.model

from . import utils
from .base import BaseView
from .urls import ALL_URLS


@resource(path=ALL_URLS['login'])
class LoginView(BaseView):
    """
    View to log in and get a cookie for use later.
    """

    name = 'login'

    types = {}

    individual_allowed_methods = dict(
        POST=dict(
            description="Authenticate and get a session cookie using a JSON "
                "body with attributes 'username' and 'password'.",
            returns="Session cookie attached at cookies->session.",
            permissions='none',
            parameters=dict(
                username="LDAP username",
                password="LDAP password",
                wildcard="Whether you would like an IP-wildcard cookie (if "
                    "authorized)",
                environments="List of environment IDs separated by + signs of "
                    "environments that the cookie will be allowed to modify",
            )
        ),
    )

    def validate_login(self, request):
        """
        Authenticate the user.
        """
        if request.errors:
            return
        try:
            body = json.loads(request.body)
            password = body['password']
            username = body['username']
            restrictions = dict()
            self.user = username
            self.body = body
        except (ValueError, KeyError):
            request.errors.add(
                'body', '',
                'Could not parse body as valid JSON. Body must be a JSON '
                'object with attributes "username" and "password".'
            )
            request.errors.status = 400
            return
        try:
            ldap_conn = ldap.initialize(self.settings['ldap_server'])
            domain_name = "uid={username},ou=People,dc=tagged,dc=com".format(
                username=username,
            )
            ldap_conn.bind_s(domain_name, password)
            results = ldap_conn.search_s(
                "cn=siteops,ou=Groups,dc=tagged,dc=com",
                ldap.SCOPE_BASE
            )
            try:
                request.is_admin = (
                    username in [member for result in results for member in
                                 result[1]['memberUid']]
                )
            except (KeyError, IndexError):
                request.is_admin = False
            ldap_conn.unbind()
        except ldap.SERVER_DOWN:
            request.errors.add('url', '',
                                    "Could not connect to LDAP server.")
            request.errors.status = 500
        except ldap.LDAPError:
            request.errors.add(
                'query', 'user',
                "Authentication failed. Please check your username and "
                "password and try again."
            )
            request.errors.status = 401

    def validate_restrictions(self, request):
        """
        Determinte whether restrictions are valid and set them to
        self.restrictions if they are.
        """
        if getattr(self, 'body', None) is None:
            return
        self.restrictions = dict()
        self.request.wildcard = False
        self.request.eternal = False
        for key in self.body:
            if key in ('password', 'username'):
                continue
            elif key == 'methods':
                valid_methods = ('DELETE', 'GET', 'POST', 'PUT',)
                invalid_method = False
                for method in self.body[key].split('+'):
                    if method not in valid_methods:
                        request.errors.add(
                            "body", key,
                            "Unsupported method: {val}. Supported methods: "
                            "{methods}".format(
                                val=self.body[key],
                                methods=valid_methods,
                            )
                        )
                        request.errors.status = 422
                        invalid_method = True
                if not invalid_method:
                    self.restrictions[key] = self.body[key]
            elif key in ('wildcard', 'eternal'):
                if type(self.body[key]) != bool:
                    request.errors.add(
                        'body', key,
                        "Value {val} for argument {key} is not a Boolean."
                        .format(
                            val=self.body[key],
                            key=key,
                        )
                    )
                    request.errors.status = 400
                elif key == 'wildcard' and (self.settings.get(
                    'wildcard_users', None
                ) is None or self.user not in self.settings['wildcard_users']):
                    request.errors.add(
                        'body', key,
                        "Insufficient authorization. You are not authorized to"
                        " get wildcard cookies."
                    )
                    request.errors.status = 403
                elif key == 'eternal' and (self.settings.get(
                    'eternal_users', None
                ) is None or self.user not in self.settings['eternal_users']):
                    request.errors.add(
                        'body', key,
                        "Insufficient authorization. You are not authorized to"
                        " get eternal cookies."
                    )
                    request.errors.status = 403
                setattr(request, key, self.body[key])
            else:
                self._validate_id_list(key, self.body[key])

    def _validate_id_list(self, obj_type, id_list):
        """
        Validate the list of IDs as valid objects of type obj_type.
        """
        obj_mapping = {
            # Uncomment when support for these is added.  --KN
            # 'applications': tds.model.Application,
            'environments': tagopsdb.model.Environment,
            # 'projects': tagopsdb.model.Project,
            # 'tiers': tds.model.AppTarget,
        }
        if obj_type not in obj_mapping:
            self.request.errors.add(
                'body', obj_type,
                "Unsupported query: {obj_type}. Valid parameters: {params}."
                .format(
                    obj_type=obj_type,
                    params=sorted(obj_mapping.keys()),
                )
            )
            self.request.errors.status = 422
            return
        model = obj_mapping[obj_type]
        parsed_id_list = id_list.split('+')
        bad_entry = False
        for obj_id in parsed_id_list:
            try:
                int(obj_id)
            except ValueError:
                self.request.errors.add(
                    'body', obj_type,
                    "Could not parse as integer: {id_list}.".format(
                        id_list=id_list,
                    )
                )
                self.request.errors.status = 422
                bad_entry = True
            if self.query(model).get(id=obj_id) is None:
                self.request.errors.add(
                    'body', obj_type,
                    "Could not find {obj_type} with ID {obj_id}.".format(
                        obj_type=obj_type[:-1],
                        obj_id=obj_id,
                    )
                )
                self.request.errors.status = 400
                bad_entry = True
        if not bad_entry:
            self.restrictions[obj_type] = id_list

    @view(validators=('validate_put_post', 'validate_post_required',
                      'validate_login', 'validate_restrictions'))
    def post(self):
        """
        Handle a POST request after the parameters are marked valid JSON.
        """
        if 'X-Forwarded-For' in self.request.headers:
            remote_addr = \
                self.request.headers['X-Forwarded-For'].split(', ')[0]
        elif self.request.wildcard:
            remote_addr = 'any'
        else:
            remote_addr = self.request.remote_addr
        response = self.make_response("SUCCESS")
        utils.set_cookie(
            response,
            self.user,
            remote_addr,
            self.settings,
            self.request.is_admin,
            self.restrictions,
            self.request.eternal,
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
