Form:

    http://deploy.tagged.com/api/v1/<command>/<subcommand>?<options>


Repository:

    /repository/add

    Options:
        project - Name of project
        pkgname - Name of package
        pkgpath - Path to built packages on build system
        buildhost - System that packages are built on
        buildtype - Type of build (hudson, jenkins, etc.)
        apptype - Specific apptype(s) associated with project
        config (optional) - config project associated with project

    Example:
        /repository/add?project=spambuild&pkgname=spambuild&pkgpath=spambuild&buildhost=djavabuild01.tag-dev.com&buildtype=jenkins&apptype=spambuild&config=tagconfig

    /repository/delete

    Options:
        project - Name of project

    Example:
        /repository/delete?project=spambuild

    /repository/list

    Options:
        projects (optional, multiple) - Specific project(s) to list

    Examples:
        /repository/list
        /repository/list?projects=spambuild
        /repository/list?projects=riskbuild&projects=risk-scan


Packages:

    /package/add

    Options:
        project - Name of project in repository
        version - Release verison number for project

    Example:
        /package/add?project=spambuild&version=143

    /package/delete

    Options:
        project - Name of project in repository
        version - Release verison number for project

    Example:
        /package/delete?project=spambuild&version=132

    /package/list

    Options:
        projects (optional, multiple) - Specific project(s) to list

    Examples:
        /package/list
        /package/list?projects=spambuild
        /package/list?projects=riskbuild&projects=risk-scan


Configuration project (e.g. tagconfig):

    /config/add-apptype

    Options:
        apptype - Application type to add to config project
        project - Name of config project in system

    Example:
        /config/add-apptype?apptype=spambuild&project=tagconfig

    /config/create

    Options:
        project - Name of config project in system
        pkgname - Name of package
        pkgpath - Path to built packages on build system
        buildhost - System that packages are built on
        buildtype - Type of build (hudson, jenkins, etc.)

    Example:
        /config/create?project=tagconfig&pkgname=tagconfig&pkgpath=tagconfig&buildhost=djavabuild01.tag-dev.com&buildtype=jenkins

    /config/delete

    Options:
        project - Name of config project in system

    Example:
        /config/delete?project=tagconfig

    /config/delete-apptype

    Options:
        apptype - Application type to remove from config project
        project - Name of config project in system

    Example:
        /config/delete-apptype?apptype=spambuild&project=tagconfig

    /config/invalidate

    Options:
        project - Name of project in repository
        version - Release verison number for project
        apptype (multiple, exclusive) - Specific application types for invalidateion
        all-apptypes (exclusive) - Handle all app types for invalidation

        'apptype' and 'all-apptypes' are exclusive

    Examples:
        /config/invalidate?project=tagconfig&version=78&apptype=spambuild
        /config/invalidate?project=tagconfig&version=78&all-apptypes

    /config/push

    Options:
        project - Name of project in repository
        version - Release verison number for project
        delay (optional) - Time delay (in seconds) between each push
        host (multiple, exclusive) - Specific host(s) for deployment
        apptype (multiple, exclusive) - Specific application types for deployment
        all-apptypes (exclusive) - Handle all app types for deployment

        'host', 'apptype' and 'all-apptypes' are exclusive

    Examples:
        /config/push?project=tagconfig&version=78&apptype=spambuild
        /config/push?project=tagconfig&version=78&host=dspambuild01
        /config/push?project=tagconfig&version=78&apptype=pets&delay=20

    /config/repush

    Options:
        project - Name of project in repository
        delay (optional) - Time delay (in seconds) between each push
        host (multiple, exclusive) - Specific host(s) for redeployment
        apptype (multiple, exclusive) - Specific application types for redeployment
        all-apptypes (exclusive) - Handle all app types for redeployment

        'host', 'apptype' and 'all-apptypes' are exclusive

    Examples:
        /config/repush?project=tagconfig&apptype=spambuild
        /config/repush?project=tagconfig&host=dspambuild01
        /config/repush?project=tagconfig&apptype=pets&delay=20

    /config/revert

    Options:
        project - Name of project in repository
        delay (optional) - Time delay (in seconds) between each push
        host (multiple, exclusive) - Specific host(s) for redeployment
        apptype (multiple, exclusive) - Specific application types for redeployment
        all-apptypes (exclusive) - Handle all app types for redeployment

        'host', 'apptype' and 'all-apptypes' are exclusive

    Examples:
        /config/revert?project=tagconfig&apptype=spambuild
        /config/revert?project=tagconfig&host=dspambuild01
        /config/revert?project=tagconfig&apptype=pets&delay=20

    /config/show

    Options:
        project - Name of project in repository
        version - Release verison number for project
        apptype (multiple, exclusive) - Specific application types for reversion
        all-apptypes (exclusive) - Handle all app types for reversion

        'apptype' and 'all-apptypes' are exclusive

    Examples:
        /config/show?project=tagconfig&version=78&apptype=spambuild
        /config/show?project=tagconfig&version=78&all-apptypes

    /config/validate

    Options:
        project - Name of project in repository
        version - Release verison number for project
        force (optional) - Do validation even when there are bad hosts
        apptype (multiple, exclusive) - Specific application types for validation
        all-apptypes (exclusive) - Handle all app types for validation

        'apptype' and 'all-apptypes' are exclusive

    Examples:
        /config/validate?project=tagconfig&version=78&apptype=spambuild
        /config/validate?project=tagconfig&version=78&apptype=subpoena&force


Application project (e.g. spambuild):

    /deploy/add-apptype

    Options:

    /deploy/delete-apptype

    Options:

    /deploy/force-production

    Options:

    /deploy/force-staging

    Options:

    /deploy/invalidate

    Options:

    /deploy/promote

    Options:

    /deploy/redeploy

    Options:

    /deploy/restart

    Options:

    /deploy/rollback

    Options:

    /deploy/show

    Options:

    /deploy/validate

    Options:

