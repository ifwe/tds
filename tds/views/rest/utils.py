"""
REST API utilities.
"""

import hmac
import hashlib
import base64
from datetime import datetime


def _create_digest(username, addr, seconds, settings, is_admin, prepend):
    """
    Create a digest for the given user, remote client address, and integer
    seconds since epoch when the created digest's cookie was created.
    """
    seconds = int(seconds)
    msg = "{prepend}{username}&{addr}&{seconds}&{admin}".format(
        prepend=prepend,
        username=username,
        addr=addr,
        seconds=seconds,
        admin=is_admin,
    )
    dig = hmac.new(
        settings['secret_key'],
        msg=msg,
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()


def _create_cookie(username, addr, settings, is_admin, prepend=None):
    """
    Create a cookie with the given username and remote client address.
    prepend should be a string containing values separated by +s of
    restrictions separated by &s.
    """
    seconds = int(
        (
            datetime.now().replace(microsecond=0) -
            datetime.utcfromtimestamp(0)
        ).total_seconds()
    )
    digest = _create_digest(
        username, addr, seconds, settings, is_admin, prepend
    )

    return "{prepend}issued={issued}&user={user}&digest={digest}".format(
        prepend=prepend,
        issued=seconds,
        user=username,
        digest=digest,
    )


def set_cookie(response, username, addr, settings, is_admin,
               restrictions=None):
    """
    Create and set a cookie for the given username and remote client address
    for the given response.
    """
    prepend = ''
    if restrictions is not None:
        for key in sorted(restrictions.keys()):
            prepend += '{key}={val}&'.format(key=key, val=restrictions[key])

    cookie_value = _create_cookie(username, addr, settings, is_admin, prepend)
    response.set_cookie(
        key='session',
        value=cookie_value,
        max_age=settings['cookie_life'],
        secure=True,
    )


def validate_cookie(request, settings):
    """
    Validate the cookie in the given request.
    Return (present, username, is_admin) where:
    present is whether the cookie is present.
    username is the username in the cookie if present == True and the cookie
    is valid, False otherwise.
    is_admin is True if the cookie is valid and the user has admin permissions,
    False otherwise.
    """
    if not getattr(request, 'cookies', None) or 'session' not in \
            request.cookies:
        return (False, False, False, dict())

    digest = seconds = username = None

    pairs = [p.split('=', 1) for p in request.cookies['session'].split('&')]
    restrictions = dict()
    restrict_keys = ('environments', 'methods',)
    # Change to the following when support for them is added.  --KN
    # restrict_keys = ('applications', 'environments', 'methods', 'projects',
    #                  'tiers')
    for key, val in pairs:
        if key == 'issued':
            seconds = int(val)
        if key == 'user':
            username = val
        if key == 'digest':
            digest = val
        for restrict_key in restrict_keys:
            if key == restrict_key:
                restrictions[key] = val

    prepend = ''
    for key in restrict_keys:
        if key in restrictions:
            prepend += '{key}={val}&'.format(key=key, val=restrictions[key])

    if None in (digest, seconds, username):
        return (True, False, False, restrictions)

    if 'X-Forwarded-For' in request.headers:
        remote_addr = request.headers['X-Forwarded-For'].split(', ')[0]
    else:
        remote_addr = request.remote_addr

    admin_digest = _create_digest(
        username, remote_addr, seconds, settings, True, prepend,
    )
    non_admin_digest = _create_digest(
        username, remote_addr, seconds, settings, False, prepend,
    )
    wildcard_admin_digest = _create_digest(
        username, 'any', seconds, settings, True, prepend,
    )
    wildcard_non_admin_digest = _create_digest(
        username, 'any', seconds, settings, False, prepend,
    )
    if digest not in (
        admin_digest, non_admin_digest, wildcard_admin_digest,
        wildcard_non_admin_digest,
    ):
        return (True, False, False, restrictions)

    if (datetime.now() - datetime.utcfromtimestamp(0)).total_seconds() - \
            seconds - settings['cookie_life'] >= 0:
        return (True, False, False, restrictions)

    is_admin = digest in (admin_digest, wildcard_admin_digest,)

    return (True, username, is_admin, restrictions)
