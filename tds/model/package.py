import tagopsdb.database.model as model

class Package(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

    def __eq__(self, other):
        return self.__dict__.__eq__(other.__dict__)


class PackageLocationsModel(model.PackageLocations):
    def __init__(self):
        self.id = 1
        self.project_type = 'application'
        self.pkg_type = 'jenkins'
        self.pkg_name = 'fake_package'
        self.app_name = 'fake_project'
        self.path = 'fake_path'
        self.arch = 'noarch'
        self.build_host = 'fake_host.tagged.com'
        self.environment = 'fake_env'
        super(PackageLocationsModel, self).__init__(
            self.project_type,
            self.pkg_type,
            self.pkg_name,
            self.app_name,
            self.path,
            self.arch,
            self.build_host,
            self.environment
        )


class PackagesModel(model.Packages):
    def __init__(self):
        self.id = 1
        self.pkg_def_id = 1
        self.pkg_name = 'fake_package'
        self.version = 'badf00d'
        self.revision = 1
        self.status = 'completed'
        self.created = ''
        self.creator = 'fake_user'
        self.builder = 'jenkins'
        self.project_type = 'application'
        super(PackagesModel, self).__init__(
            self.pkg_def_id,
            self.pkg_name,
            self.version,
            self.revision,
            self.status,
            self.created,
            self.creator,
            self.builder,
            self.project_type
        )
