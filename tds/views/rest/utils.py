"""
REST API utilities.
"""

import hmac
import hashlib
import base64
import tds.views.rest.settings
from datetime import datetime, timedelta


def _create_digest(username, addr, seconds):
    """
    Create a digest for the given user, remote client address, and integer
    seconds since epoch when the created digest's cookie will expire.
    """
    seconds = int(seconds)
    msg = "{username}&{addr}&{seconds}".format(username=username, addr=addr,
                                               seconds=seconds)
    dig = hmac.new(
        tds.views.rest.settings.SECRET_KEY,
        msg=msg,
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()


def set_cookie(response, username, addr):
    """
    Create and set a cookie for the given username and remote client address
    for the given response.
    """
    seconds = int(
        (
            datetime.now().replace(microsecond=0) -
            datetime.utcfromtimestamp(0)
        ).total_seconds() +
        tds.views.rest.settings.COOKIE_LIFE
    )
    digest = _create_digest(username, addr, seconds)
    cookie_value = "exp={exp}&user={user}&digest={digest}".format(
        exp=seconds,
        user=username,
        digest=digest,
    )
    response.set_cookie(
        key='session',
        value=cookie_value,
        max_age=tds.views.rest.settings.COOKIE_LIFE,
        secure=True,
    )


def validate_cookie(request):
    """
    Validate the cookie in the given request. Return True if the cookie is
    present, the digest is valid, and the cookie is not expired.
    Return False otherwise.
    """
    if not getattr(request, 'cookies', None) or 'session' not in \
        request.cookies:
            return False

    digest = seconds = username = None

    pairs = [p.split('=', 1) for p in response.cookies['session'].split('&')]
    for k, v in pairs:
        if k == 'exp':
            seconds = int(v)
        if k == 'user':
            username = v
        if k == 'digest':
            digest = v

    if None in (digest, seconds, username):
        return False

    if _create_digest(username, request.remote_addr, seconds) != digest:
        return False

    if (datetime.now() - datetime.utcfromtimestamp(0)).total_seconds() - \
        seconds >= 0:
            return False

    return True
