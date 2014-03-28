import tds.scripts.tds_install as tds_install


def _error_except(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SystemExit as e:
            return 'error'
    return wrapper


@_error_except
def restart(self, app):
    return tds_install.do_restart(app)


@_error_except
def install(self, app, version):
    return tds_install.do_install(app, version)
