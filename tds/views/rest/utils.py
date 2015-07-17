"""
REST API utilities.
"""

import hmac
import hashlib
import base64
from datetime import datetime, timedelta


def _create_digest(username, addr, seconds, settings):
    """
    Create a digest for the given user, remote client address, and integer
    seconds since epoch when the created digest's cookie was created.
    """
    seconds = int(seconds)
    msg = "{username}&{addr}&{seconds}".format(username=username, addr=addr,
                                               seconds=seconds)
    dig = hmac.new(
        settings['secret_key'],
        msg=msg,
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()


def _create_cookie(username, addr, settings):
    """
    Create a cookie with the given username and remote client address.
    """
    seconds = int(
        (
            datetime.now().replace(microsecond=0) -
            datetime.utcfromtimestamp(0)
        ).total_seconds()
    )
    digest = _create_digest(username, addr, seconds, settings)
    return "issued={issued}&user={user}&digest={digest}".format(
        issued=seconds,
        user=username,
        digest=digest,
    )


def set_cookie(response, username, addr, settings):
    """
    Create and set a cookie for the given username and remote client address
    for the given response.
    """
    cookie_value = _create_cookie(username, addr, settings)
    response.set_cookie(
        key='session',
        value=cookie_value,
        max_age=settings['cookie_life'],
        secure=True,
    )


def validate_cookie(request, settings):
    """
    Validate the cookie in the given request.
    Return (present, username) where:
    present is whether the cookie is present.
    username is the username in the cookie if present == True and the cookie
    is valid, False otherwise.
    """
    if not getattr(request, 'cookies', None) or 'session' not in \
        request.cookies:
            return (False, False)

    digest = seconds = username = None

    pairs = [p.split('=', 1) for p in request.cookies['session'].split('&')]
    for k, v in pairs:
        if k == 'issued':
            seconds = int(v)
        if k == 'user':
            username = v
        if k == 'digest':
            digest = v

    if None in (digest, seconds, username):
        return (True, False)

    if _create_digest(username, request.remote_addr, seconds,
                      settings) != digest:
        return (True, False)

    if (datetime.now() - datetime.utcfromtimestamp(0)).total_seconds() - \
        seconds - settings['cookie_life'] >= 0:
            return (True, False)

    return (True, username)
