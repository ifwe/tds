"""
REST API utilities.
"""

import hmac
import hashlib
import base64
from datetime import datetime


def _create_digest(username, addr, seconds, settings, is_admin):
    """
    Create a digest for the given user, remote client address, and integer
    seconds since epoch when the created digest's cookie was created.
    """
    seconds = int(seconds)
    msg = "{username}&{addr}&{seconds}&{admin}".format(
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


def _create_cookie(username, addr, settings, is_admin):
    """
    Create a cookie with the given username and remote client address.
    """
    seconds = int(
        (
            datetime.now().replace(microsecond=0) -
            datetime.utcfromtimestamp(0)
        ).total_seconds()
    )
    digest = _create_digest(username, addr, seconds, settings, is_admin)
    return "issued={issued}&user={user}&digest={digest}".format(
        issued=seconds,
        user=username,
        digest=digest,
    )


def set_cookie(response, username, addr, settings, is_admin):
    """
    Create and set a cookie for the given username and remote client address
    for the given response.
    """
    cookie_value = _create_cookie(username, addr, settings, is_admin)
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
        return (False, False, False)

    digest = seconds = username = None

    pairs = [p.split('=', 1) for p in request.cookies['session'].split('&')]
    for key, val in pairs:
        if key == 'issued':
            seconds = int(val)
        if key == 'user':
            username = val
        if key == 'digest':
            digest = val

    if None in (digest, seconds, username):
        return (True, False, False)

    if 'X-Forwarded-For' in request.headers:
        remote_addr = request.headers['X-Forwarded-For'].split(', ')[0]
    else:
        remote_addr = request.remote_addr

    admin_digest = _create_digest(username, remote_addr, seconds, settings,
                                  True)
    non_admin_digest = _create_digest(username, remote_addr, seconds, settings,
                                      False)

    if digest not in (admin_digest, non_admin_digest):
        return (True, False, False)

    if (datetime.now() - datetime.utcfromtimestamp(0)).total_seconds() - \
            seconds - settings['cookie_life'] >= 0:
        return (True, False, False)

    is_admin = digest == admin_digest

    return (True, username, is_admin)
