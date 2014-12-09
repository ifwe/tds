# Salt module for TDS

import tds.scripts.tds_install as tds_install


def _error_except(func):
    """catch sys.exit System Errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SystemExit:
            return 'error'
    return wrapper


@_error_except
def restart(self, app):
    """restart via tds_install"""
    return tds_install.do_restart(app)


@_error_except
def install(self, app, version):
    """install via tds_install"""
    return tds_install.do_install(app, version)
