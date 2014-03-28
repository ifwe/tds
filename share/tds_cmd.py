import tds.scripts.tds_install as tds_install


def restart(self, app):
    return tds_install.do_restart(app)


def install(self, app, version):
    return tds_install.do_install(app, version)
