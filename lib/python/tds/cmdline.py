from ordereddict import OrderedDict as odict

repository_data = odict([
    ('add', odict([
        ('help', 'Add new project to the repository information'),
        ('subargs', odict([
            (('-e', '--environment'), odict([
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
            (('buildtype',), odict([
                ('help', 'Type of build (hudson, jenkins, tagconfg, etc.)'),
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
            (('revision',), odict([
                ('help', 'Revision number for project'),
             ])),
         ])),
     ])),
    ('delete', odict([
        ('help', 'Remove given package from deployment system'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('revision',), odict([
                ('help', 'Revision number for project'),
             ])),
         ])),
     ])),
    ('list', odict([
        ('help', 'List all current package in deployment system'),
        ('subargs', odict([   # Currently none
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
            (('revision',), odict([
                ('help', 'Revision number for project'),
             ])),
            (('apptype',), odict([
                ('help', 'Application type for project'),
             ])),
         ])),
     ])),
    ('force-staging', odict([
        ('help', 'Overriding deployment direct to staging'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('revision',), odict([
                ('help', 'Revision number for project'),
             ])),
            (('apptype',), odict([
                ('help', 'Application type for project'),
             ])),
         ])),
     ])),
    ('invalidate', odict([
        ('help', 'Mark a given deployment as not working'),
        ('subargs', odict([
            (('deployid',), odict([
                ('help', 'ID number for deployment'),
                ('type', int),
             ])),
         ])),
     ])),
    ('promote', odict([
        ('help', 'Promote project to next environment'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('revision',), odict([
                ('help', 'Revision number for project'),
             ])),
            (('apptype',), odict([
                ('help', 'Application type for project'),
             ])),
         ])),
     ])),
    ('redeploy', odict([
        ('help', 'Redeploy project to current environment'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('revision',), odict([
                ('help', 'Revision number for project'),
             ])),
            (('apptype',), odict([
                ('help', 'Application type for project'),
             ])),
         ])),
     ])),
    ('rollback', odict([
        ('help', 'Revert deployment'),
        ('subargs', odict([
            (('--remain-valid',), odict([
                ('help', 'Do not invalidate deployment'),
                ('action', 'store_true'),
             ])),
            (('deployid',), odict([
                ('help', 'ID number for deployment'),
                ('type', int),
             ])),
         ])),
     ])),
    ('show', odict([
        ('help', 'Show information for a given project release'),
        ('subargs', odict([
            (('project',), odict([
                ('help', 'Name of project in repository'),
             ])),
            (('revision',), odict([
                ('help', 'Revision number for project'),
             ])),
         ])),
     ])),
    ('validate', odict([
        ('help', 'Verify a given deployment is working'),
        ('subargs', odict([
            (('deployid',), odict([
                ('help', 'ID number for deployment'),
                ('type', int),
             ])),
         ])),
     ])),
])

parser_data = odict([
    ('repository', repository_data),
    ('package', package_data),
    ('deploy', deploy_data),
])


def parser_info():
    """Return the constructed data for the command line parser"""

    return parser_data
