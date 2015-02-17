"""
Utility functions for GET requests to the REST API.
"""

import tds.model


def obj_by_name_or_id(obj_type, request):
    """
    Validate that an object of type obj_type with the name_or_id given in the
    request exists and attach it to the request at
    request.validated[obj_type].
    Otherwise, attach an error with location='path', name='name_or_id' and a
    description.
    This error will return a "400 Bad Request" response to this request.
    """
    obj_cls = getattr(tds.model, obj_type.title(), None)
    if obj_cls is None:
        raise tds.exceptions.NotFoundError('Model', [obj_type])
    try:
        obj_id = int(request.matchdict['name_or_id'])
        obj = obj_cls.get(id=obj_id)
        name = False
    except ValueError:
        obj_id = False
        name = request.matchdict['name_or_id']
        obj = obj_cls.get(name=name)
    if obj is None:
        request.errors.add(
            'path', 'name_or_id',
            "{obj_type} with {prop} {val} does not exist.".format(
                obj_type=obj_type.title(),
                prop="ID" if obj_id else "name",
                val=obj_id if obj_id else name,
            )
        )
        request.errors.status = 404
    else:
        request.validated[obj_type] = obj


def pkg_by_version_revision(request):
    """
    Validate that the package with the version, revision, and application in
    the request exists. Attach it at request.validated['package'] if it does.
    Attach an error with location='path', name='revision' and a description
    otherwise.
    This error with return a "400 Bad Request" response to this request.
    """
    try:
        version = int(request.matchdict['version'])
    except ValueError:
        request.errors.add(
            'path', 'version',
            'Version must be an integer'
        )
        return
    try:
        revision = int(request.matchdict['revision'])
    except ValueError:
        request.errors.add(
            'path', 'revision',
            'Revision must be an integer'
        )
        return
    try:
        pkg = tds.model.Package.get(
            application=request.validated['application'],
            version=request.matchdict['version'],
            revision=request.matchdict['revision'],
        )
    except KeyError: # No request.validated['application'] entry
        raise tds.exceptions.TDSException(
            "No validated application when trying to locate package."
        )
    if pkg is None:
        request.errors.add(
            'path', 'revision',
            ("Package with version {v} and revision {r} does"
             " not exist for this application.".format(
                v=version,
                r=revision,
             )
            )
        )
        request.errors.status = 404
    else:
        request.validated['package'] = pkg


def pkgs_by_limit_start(request):
    """
    Get all packages for the application request.validated['application'],
    optionally paginated by request.params['limit'] and
    request.params['start'] if those are non-null.
    """
    try:
        pkgs = tds.model.Package.query().filter(
            tds.model.Package.application==request.validated['application'],
        ).order_by(tds.model.Package.id)
    except KeyError: # No request.validated['application'] entry
        raise tds.exceptions.TDSException(
            "No validated application when trying to locate package."
        )
    else:
        request.validated['packages'] = pkgs
    collection_by_limit_start('package', request)


def collection_by_limit_start(obj_type, request):
    """
    Make sure that the selection parameters are valid for collection GET.
    If they are not, raise "400 Bad Request".
    Else, set request.validated[obj_type + 's'] to objects matching query.
    """
    obj_cls = getattr(tds.model, obj_type.title(), None)
    if obj_cls is None:
        raise tds.exceptions.NotFoundError('Model', [obj_type])
    plural = obj_type + 's'
    all_params = ('limit', 'start',) # for later: 'sort_by', 'reverse')
    for key in request.params:
        if key not in all_params:
            request.errors.add(
                'query', key,
                ("Unsupported query: {param}. Valid parameters: "
                 "{all_params}.".format(param=key, all_params=all_params))
            )

    # This might be used later but isn't currently:
    # if 'sort_by' in request.params:
    #     valid_attrs = ('id', 'name')
    #     if request.params['sort_by'] not in valid_attrs:
    #         request.errors.add(
    #             'query', 'sort_by',
    #             ("Unsupported sort attribute: {val}. Valid attributes: "
    #              "{all_attrs}".format(
    #                 val=request.params['sort_by'],
    #                 all_attrs=valid_attrs,
    #              ))
    #         )
    #     elif request.params['sort_by'] == 'name':
    #         sort_by = tds.model.Project.name
    #     else:
    #         sort_by = tds.model.Project.id
    # request.validated['projects'].order_by(sort_by)

    if plural not in request.validated:
        request.validated[plural] = obj_cls.query().order_by(obj_cls.id)

    if 'start' in request.params and request.params['start']:
        request.validated[plural] = (
            request.validated[plural].filter(
                obj_cls.id >= request.params['start']
            )
        )

    if obj_cls == tds.model.Application:
        request.validated[plural] = (
            request.validated[plural].filter(obj_cls.pkg_name != '__dummy__')
        )

    if 'limit' in request.params and request.params['limit']:
        request.validated[plural] = (
            request.validated[plural].limit(request.params['limit'])
        )

    # This code was designed to allow filtering on attributes.
    # It's preserved here for ideas in case it's relevant elsewhere.
    # names = set(request.params.getall('name'))
    # proj_ids = set(request.params.getall('id'))
    #
    # if proj_ids and names:
    #     request.validated['projects'] = tds.model.Project.query().filter(
    #         tds.model.Project.id.in_(tuple(proj_ids)),
    #         tds.model.Project.name.in_(tuple(names)),
    #     )
    # elif proj_ids:
    #     request.validated['projects'] = tds.model.Project.query().filter(
    #         tds.model.Project.id.in_(tuple(proj_ids)),
    #     )
    # elif names:
    #     request.validated['projects'] = tds.model.Project.query().filter(
    #         tds.model.Project.name.in_(tuple(names)),
    #     )
    # else:
    #     request.validated['projects'] = tds.model.Project.all()
