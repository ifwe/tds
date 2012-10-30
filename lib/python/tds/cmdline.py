import argparse

from ordereddict import OrderedDict as odict

repository_data = odict([
    ('add', odict([
        ('help', 'Add new project to the repository information'),
        ('subargs', odict([
            (('-c', '--config'), odict([
                ('help', 'Config project associated with project'),
             ])),
            (('-e', '--env-specific'), odict([
                ('help', 'Project\'s packages are environment-specific'),
                ('action', 'store_true'),
             ])),
            (('project',), odict([
                ('help', 'Name of project in system'),
             ])),
            (('pkgname',), odict([
                ('help', 'Name of package (RPM)'),
             ])),
            (('pkgpath',), odict([
                ('help', 'Path to built packages on build system'),
             ])),
            (('buildhost',), odict([
                ('help', 'System that packages are built on'),
             ])),
            (('buildtype',), odict([
                ('help', 'Type of build (hudson, jenkins, etc.)'),
             ])),
            (('apptypes',), odict([
                ('help', 'Specific apptype(s) associated with project'),
                ('metavar', 'apptype'),
                ('nargs', '+'),
             ])),
         ])),
     ])),
    ('delete', odict([
        ('help', 'Remove given project from repository information'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in system'),
             ])),
         ])),
     ])),
    ('list', odict([
        ('help', 'List all current projects in repository'),
        ('subargs', odict([  # Currently none
         ])),
     ])),
])

package_data = odict([
    ('add', odict([
        ('help', 'Add new package to deployment system'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('version',), odict([
                ('help', 'Release version number for project'),
                ('type', int),
             ])),
         ])),
     ])),
    ('delete', odict([
        ('help', 'Remove given package from deployment system'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('version',), odict([
                ('help', 'Release version number for project'),
                ('type', int),
             ])),
         ])),
     ])),
    ('list', odict([
        ('help', 'List all current package in deployment system'),
        ('subargs', odict([   # Currently none
         ])),
     ])),
])

config_data = odict([
    ('add-apptype', odict([
        ('help', 'Add app type to a config project'),
        ('subargs', odict([
            (('apptype',), odict([
                ('help', 'App type to add to config project'),
             ])),
            (('project',), odict([
                ('help', 'Name of config project in system'),
             ])),
         ])),
     ])),
    ('create', odict([
        ('help', 'Create a new config project'),
        ('subargs', odict([
            (('-e', '--env-specific'), odict([
                ('help', 'Project\'s packages are environment-specific'),
                ('action', 'store_true'),
             ])),
            (('project',), odict([
                ('help', 'Name of config project in system'),
             ])),
            (('pkgname',), odict([
                ('help', 'Name of package (RPM)'),
             ])),
            (('pkgpath',), odict([
                ('help', 'Path to built packages on build system'),
             ])),
            (('buildhost',), odict([
                ('help', 'System that packages are built on'),
             ])),
            (('buildtype',), odict([
                ('help', 'Type of build (hudson, jenkins, etc.)'),
             ])),
         ])),
     ])),
    ('delete', odict([
        ('help', 'Remove an existing config project'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of config project in system'),
             ])),
         ])),
     ])),
    ('delete-apptype', odict([
        ('help', 'Remove app type from a config project'),
        ('subargs', odict([
            (('apptype',), odict([
                ('help', 'App type to remove from config project'),
             ])),
            (('project',), odict([
                ('help', 'Name of config project in system'),
             ])),
         ])),
     ])),
    ('invalidate', odict([
        ('help', 'Mark a given config deployment as not working'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('version',), odict([
                ('help', 'Release version number for project'),
                ('type', int),
             ])),
            (('--apptypes',), odict([
                ('help', 'Specific app type(s) for invalidation'),
                ('metavar', 'APPTYPE'),
                ('nargs', '*'),
             ])),
            (('--all-apptypes',), odict([
                ('help', 'Handle all app types for invalidation'),
                ('action', 'store_true'),
             ])),
         ])),
     ])),
    ('push', odict([
        ('help', 'Deploy a given version of config project'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of config project in system'),
             ])),
            (('version',), odict([
                ('help', 'Release version number for config project'),
             ])),
            (('--hosts',), odict([
                ('help', 'Specific host(s) for deployment'),
                ('metavar', 'HOST'),
                ('nargs', '*'),
             ])),
            (('--apptypes',), odict([
                ('help', 'Specific app type(s) for deployment'),
                ('metavar', 'APPTYPE'),
                ('nargs', '*'),
             ])),
            (('--all-apptypes',), odict([
                ('help', 'Handle all app types for deployment'),
                ('action', 'store_true'),
             ])),
         ])),
     ])),
    ('repush', odict([
        ('help', 'Redeploy current version of config project'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('--hosts',), odict([
                ('help', 'Specific host(s) for redeployment'),
                ('metavar', 'HOST'),
                ('nargs', '*'),
             ])),
            (('--apptypes',), odict([
                ('help', 'Specific app type(s) for redeployment'),
                ('metavar', 'APPTYPE'),
                ('nargs', '*'),
             ])),
            (('--all-apptypes',), odict([
                ('help', 'Handle all app types for redeployment'),
                ('action', 'store_true'),
             ])),
         ])),
     ])),
    ('revert', odict([
        ('help', 'Revert to previous version of config project'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('--apptypes',), odict([
                ('help', 'Specific app type(s) for reversion'),
                ('metavar', 'APPTYPE'),
                ('nargs', '*'),
             ])),
            (('--all-apptypes',), odict([
                ('help', 'Handle all app types for reversion'),
                ('action', 'store_true'),
             ])),
         ])),
     ])),
    ('validate', odict([
        ('help', 'Verify a given config deployment is working'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('version',), odict([
                ('help', 'Release version number for project'),
                ('type', int),
             ])),
            (('--force',), odict([
                ('help', 'Do validation even when there are bad hosts'),
                ('action', 'store_true'),
             ])),
            (('--apptypes',), odict([
                ('help', 'Specific app type(s) for validation'),
                ('metavar', 'APPTYPE'),
                ('nargs', '*'),
             ])),
            (('--all-apptypes',), odict([
                ('help', 'Handle all app types for validation'),
                ('action', 'store_true'),
             ])),
         ])),
     ])),
])

deploy_data = odict([
    ('force-production', odict([
        ('help', 'Overriding deployment direct to production'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('version',), odict([
                ('help', 'Release version number for project'),
                ('type', int),
             ])),
            (('--hosts',), odict([
                ('help', 'Specific host(s) for deployment'),
                ('metavar', 'HOST'),
                ('nargs', '*'),
             ])),
            (('--apptypes',), odict([
                ('help', 'Specific app type(s) for deployment'),
                ('metavar', 'APPTYPE'),
                ('nargs', '*'),
             ])),
            (('--all-apptypes',), odict([
                ('help', 'Handle all app types for deployment'),
                ('action', 'store_true'),
             ])),
         ])),
     ])),
    ('force-staging', odict([
        ('help', 'Overriding deployment direct to staging'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('version',), odict([
                ('help', 'Release version number for project'),
                ('type', int),
             ])),
            (('--hosts',), odict([
                ('help', 'Specific host(s) for deployment'),
                ('metavar', 'HOST'),
                ('nargs', '*'),
             ])),
            (('--apptypes',), odict([
                ('help', 'Specific app type(s) for deployment'),
                ('metavar', 'APPTYPE'),
                ('nargs', '*'),
             ])),
            (('--all-apptypes',), odict([
                ('help', 'Handle all app types for deployment'),
                ('action', 'store_true'),
             ])),
         ])),
     ])),
    ('invalidate', odict([
        ('help', 'Mark a given deployment as not working'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('version',), odict([
                ('help', 'Release version number for project'),
                ('type', int),
             ])),
            (('--apptypes',), odict([
                ('help', 'Specific app type(s) for invalidation'),
                ('metavar', 'APPTYPE'),
                ('nargs', '*'),
             ])),
            (('--all-apptypes',), odict([
                ('help', 'Handle all app types for invalidation'),
                ('action', 'store_true'),
             ])),
         ])),
     ])),
    ('promote', odict([
        ('help', 'Promote project to next environment'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('version',), odict([
                ('help', 'Release version number for project'),
                ('type', int),
             ])),
            (('--hosts',), odict([
                ('help', 'Specific host(s) for deployment'),
                ('metavar', 'HOST'),
                ('nargs', '*'),
             ])),
            (('--apptypes',), odict([
                ('help', 'Specific app type(s) for deployment'),
                ('metavar', 'APPTYPE'),
                ('nargs', '*'),
             ])),
            (('--all-apptypes',), odict([
                ('help', 'Handle all app types for deployment'),
                ('action', 'store_true'),
             ])),
         ])),
     ])),
    ('redeploy', odict([
        ('help', 'Redeploy project to current environment'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('--hosts',), odict([
                ('help', 'Specific host(s) for redeployment'),
                ('metavar', 'HOST'),
                ('nargs', '*'),
             ])),
            (('--apptypes',), odict([
                ('help', 'Specific app type(s) for redeployment'),
                ('metavar', 'APPTYPE'),
                ('nargs', '*'),
             ])),
            (('--all-apptypes',), odict([
                ('help', 'Handle all app types for redeployment'),
                ('action', 'store_true'),
             ])),
         ])),
     ])),
    ('restart', odict([
        ('help', 'Restart deployed application'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('--hosts',), odict([
                ('help', 'Specific host(s) for restart'),
                ('metavar', 'HOST'),
                ('nargs', '*'),
             ])),
            (('--apptypes',), odict([
                ('help', 'Specific app type(s) for restart'),
                ('metavar', 'APPTYPE'),
                ('nargs', '*'),
             ])),
            (('--all-apptypes',), odict([
                ('help', 'Handle all app types for restart'),
                ('action', 'store_true'),
             ])),
         ])),
     ])),
    ('rollback', odict([
        ('help', 'Revert deployment'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('--apptypes',), odict([
                ('help', 'Specific app type(s) for rollback'),
                ('metavar', 'APPTYPE'),
                ('nargs', '*'),
             ])),
            (('--all-apptypes',), odict([
                ('help', 'Handle all app types for rollback'),
                ('action', 'store_true'),
             ])),
         ])),
     ])),
    ('show', odict([
        ('help', 'Show information for a given project release'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('version',), odict([
                ('help', 'Release version number for project'),
                ('type', int),
                ('nargs', '?'),
             ])),
         ])),
     ])),
    ('validate', odict([
        ('help', 'Verify a given deployment is working'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('version',), odict([
                ('help', 'Release version number for project'),
                ('type', int),
             ])),
            (('--force',), odict([
                ('help', 'Do validation even when there are bad hosts'),
                ('action', 'store_true'),
             ])),
            (('--apptypes',), odict([
                ('help', 'Specific app type(s) for validation'),
                ('metavar', 'APPTYPE'),
                ('nargs', '*'),
             ])),
            (('--all-apptypes',), odict([
                ('help', 'Handle all app types for validation'),
                ('action', 'store_true'),
             ])),
         ])),
     ])),
])

parser_data = odict([
    ('repository', repository_data),
    ('package', package_data),
    ('config', config_data),
    ('deploy', deploy_data),
])


def parser_info():
    """Return the constructed data for the command line parser"""

    return parser_data
