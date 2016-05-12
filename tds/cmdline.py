"""Data for command line arguments, subarguments and options."""

from collections import OrderedDict as odict

PROJECT_DATA = odict([
    ('add', odict([
        ('help', 'Add new project to deployment system'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project'),
            ])),
        ])),
    ])),
    ('delete', odict([
        ('help', 'Remove given project from deployment system'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project'),
            ])),
        ])),
    ])),
    ('list', odict([
        ('help', 'List some/all current projects in deployment system'),
        ('subargs', odict([
            (('projects',), odict([
                ('help', 'Specific projects to list'),
                ('metavar', 'PROJECT'),
                ('nargs', '*'),
            ])),
        ])),
    ])),
])

APPLICATION_DATA = odict([
    ('add', odict([
        ('help', 'Add new application to deployment system'),
        ('subargs', odict([
            (('application',), odict([
                ('help', 'Name of application'),
            ])),
            (('job_name',), odict([
                ('help', 'Jenkins job name'),
            ])),
            (('--deploy-type',), odict([
                ('help', 'Format of application deployment (default: rpm)'),
                ('default', 'rpm'),
            ])),
            (('--arch',), odict([
                ('help', 'Architecture of application (default: noarch)'),
                ('default', 'noarch'),
            ])),
            (('--build-type',), odict([
                ('help', 'Build system for application (default: jenkins)'),
                ('default', 'jenkins'),
            ])),
            (('--build-host',), odict([
                ('help', 'Build host for application (default: '
                         'ci.tagged.com)'),
                ('default', 'ci.tagged.com'),
            ])),
        ])),
    ])),
    ('add-apptype', odict([
        ('help', 'Add apptype(s) to a project/application pair'),
        ('subargs', odict([
            (('application',), odict([
                ('help', 'Name of application'),
            ])),
            (('project',), odict([
                ('help', 'Name of project'),
            ])),
            (('apptypes',), odict([
                ('help', 'Apptype(s) to add'),
                ('metavar', 'APPTYPE'),
                ('nargs', '+'),
            ])),
        ])),
    ])),
    ('delete', odict([
        ('help', 'Remove given application from deployment system'),
        ('subargs', odict([
            (('application',), odict([
                ('help', 'Name of application'),
            ])),
        ])),
    ])),
    ('delete-apptype', odict([
        ('help', 'Remove apptype(s) from a project/application pair'),
        ('subargs', odict([
            (('application',), odict([
                ('help', 'Name of application'),
            ])),
            (('project',), odict([
                ('help', 'Name of project'),
            ])),
            (('apptypes',), odict([
                ('help', 'Apptype(s) to remove'),
                ('metavar', 'APPTYPE'),
                ('nargs', '+'),
            ])),
        ])),
    ])),
    ('list', odict([
        ('help', 'List some/all current applications in deployment system'),
        ('subargs', odict([
            (('applications',), odict([
                ('help', 'Specific applications to list'),
                ('metavar', 'APPLICATION'),
                ('nargs', '*'),
            ])),
        ])),
    ])),
    ('update', odict([
        ('help', 'Update an existing application'),
        ('subargs', odict([
            (('application',), odict([
                ('help', 'Name of the existing application'),
            ])),
            (('properties',), odict([
                ('help', ('New properties. E.g., job_name=jenkins_job '
                          'repository=https://code.ifwe.co/projects/tds/repos'
                          '/tds. For admins: name=myapp '
                          'job_name=jenkins_job deploy_type=rpm arch=noarch '
                          'build_type=jenkins build_host=ci.tagged.com '
                          'repository=https://code.ifwe.co/projects/tagopsdb'
                          '/repos/tagopsdb.')),
                ('metavar', 'PROPERTY'),
                ('nargs', '*'),
            ])),
        ])),
    ])),
])

PACKAGE_DATA = odict([
    ('add', odict([
        ('help', 'Add new package to deployment system'),
        ('subargs', odict([
            (('application',), odict([
                ('help', 'Name of application'),
            ])),
            (('version',), odict([
                ('help', 'Release version number for application'),
                ('type', str),
            ])),
            (('--job',), odict([
                ('help', 'Jenkins job name (default: application job name)'),
                ('type', str),
            ])),
            (('--force', '-f'), odict([
                ('help', 'Allow an existing package to be re-added'),
                ('action', 'store_true'),
            ])),
            (('--detach',), odict([
                ('help', 'Disconnect client after preparing package'),
                ('action', 'store_true'),
            ])),
        ])),
    ])),
    ('delete', odict([
        ('help', 'Remove given package from deployment system'),
        ('subargs', odict([
            (('application',), odict([
                ('help', 'Name of application'),
            ])),
            (('version',), odict([
                ('help', 'Release version number for application'),
                ('type', str),
            ])),
        ])),
    ])),
    ('list', odict([
        ('help', 'List all current packages in deployment system'),
        ('subargs', odict([
            (('applications',), odict([
                ('help', 'Specific applications to list'),
                ('metavar', 'APPLICATION'),
                ('nargs', '*'),
            ])),
        ])),
    ])),
])

DEPLOY_DATA = odict([
    ('fix', odict([
        ('help', 'Correct failed host deployments in current environment'),
        ('subargs', odict([
            (('application',), odict([
                ('help', 'Name of application'),
            ])),
            (('--delay',), odict([
                ('help', 'Time delay (in seconds) between each redeploy'),
                ('type', int),
            ])),
            (('--detach',), odict([
                ('help', 'Disconnect client after preparing deployments'),
                ('action', 'store_true'),
            ])),
            (('--hosts',), odict([
                ('help', 'Specific host(s) for correction'),
                ('metavar', 'HOST'),
                ('nargs', '*'),
            ])),
            (('--apptypes',), odict([
                ('help', 'Specific app type(s) for correction'),
                ('metavar', 'APPTYPE'),
                ('nargs', '*'),
            ])),
            (('--all-apptypes',), odict([
                ('help', 'Handle all app types for correction'),
                ('action', 'store_true'),
            ])),
        ])),
    ])),
    ('invalidate', odict([
        ('help', 'Mark a given deployment as not working'),
        ('subargs', odict([
            (('application',), odict([
                ('help', 'Name of application'),
            ])),
            (('version',), odict([
                ('help', 'Release version number for project'),
                ('type', str),
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
            (('application',), odict([
                ('help', 'Name of application'),
            ])),
            (('version',), odict([
                ('help', 'Release version number for application'),
                ('type', str),
            ])),
            (('--force', '-f'), odict([
                ('help',
                 'Do deployment without need for validated deployment'
                 ' in previous environment'),
                ('action', 'store_true'),
            ])),
            (('--delay',), odict([
                ('help', 'Time delay (in seconds) between each deploy'),
                ('type', int),
            ])),
            (('--detach',), odict([
                ('help', 'Disconnect client after preparing deployments'),
                ('action', 'store_true'),
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
    ('restart', odict([
        ('help', 'Restart deployed application'),
        ('subargs', odict([
            (('application',), odict([
                ('help', 'Name of application'),
            ])),
            (('--delay',), odict([
                ('help', 'Time delay (in seconds) between each restart'),
                ('type', int),
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
            (('application',), odict([
                ('help', 'Name of application'),
            ])),
            (('--delay',), odict([
                ('help', 'Time delay (in seconds) between each rollback'),
                ('type', int),
            ])),
            (('--detach',), odict([
                ('help', 'Disconnect client after preparing deployments'),
                ('action', 'store_true'),
            ])),
            (('--hosts',), odict([
                ('help', 'Specific host(s) for rollback'),
                ('metavar', 'HOST'),
                ('nargs', '*'),
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
        ('help', 'Show information for a given application release'),
        ('subargs', odict([
            (('application',), odict([
                ('help', 'Name of application'),
            ])),
            (('version',), odict([
                ('help', 'Release version number for application'),
                ('type', str),
                ('nargs', '?'),
            ])),
            (('--apptypes',), odict([
                ('help', 'Specific app type(s) to show information'),
                ('metavar', 'APPTYPE'),
                ('nargs', '*'),
            ])),
            (('--all-apptypes',), odict([
                ('help', 'Handle all app types to show information'),
                ('action', 'store_true'),
            ])),
        ])),
    ])),
    ('validate', odict([
        ('help', 'Verify a given deployment is working'),
        ('subargs', odict([
            (('application',), odict([
                ('help', 'Name of application'),
            ])),
            (('version',), odict([
                ('help', 'Release version number for project'),
                ('type', str),
            ])),
            (('--force', '-f'), odict([
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

PARSER_DATA = odict([
    ('project', PROJECT_DATA),
    ('application', APPLICATION_DATA),
    ('package', PACKAGE_DATA),
    ('deploy', DEPLOY_DATA),
])


def parser_info():
    """Return the constructed data for the command line parser"""

    return PARSER_DATA
