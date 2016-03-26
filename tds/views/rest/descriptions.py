"""
Descriptions for parameters for OPTIONS requests.
"""

APPLICATION_DESCRIPTIONS = {
    'id': 'Unique integer identifier',
    'name': 'Unique string identifier',
    'job': 'Name of Jenkins job',
    'build_host': 'Host that created the build',
    'build_type': 'Build process used',
    'deploy_type': 'Deployment process used',
    'arch': 'Binary architecture used',
    'validation_type': 'Validation process used',
    'env_specific': 'Whether the application is environment specific',
    'created': 'When this application was created',
}

APPLICATION_TIER_DESCRIPTIONS = {
    'project_id': 'Unique integer identifier for the project',
    'application_id': 'Unique integer identifier for the application',
    'tier_id': 'Unique integer identifier for the tier',
}

DEPLOYMENT_DESCRIPTIONS = {
    'id': 'Unique integer identifier',
    'user': 'Username of creator',
    'status': 'Current status of the deployment',
    'delay': 'Delay in integer seconds between restarts',
    'duration': 'Float seconds the installer daemon worked on this deployment',
    'declared': 'When this deployment was created',
}

ENVIRONMENT_DESCRIPTIONS = {
    'id': 'Unique integer identifier',
    'name': 'Unique string identifier',
    'short_name': 'Unique shorter string identifier',
    'domain': 'Address domain for the environment',
    'prefix': 'Host name prefix',
    'zone_id': 'ID of the zone for the environment',
}

GANGLIA_DESCRIPTIONS = {
    'id': 'Unique integer identifier',
    'name': 'Unique string identifier',
    'port': 'Networking port used',
}

HIPCHAT_DESCRIPTIONS = {
    'id': 'Unique integer identifier',
    'name': 'Unique string identifier',
}

HOST_DESCRIPTIONS = {
    'id': 'Unique integer identifier',
    'name': 'Unique string identifier',
    'tier_id': 'ID of the tier of the host',
    'cage': 'Cage location',
    'cab': 'Cab location',
    'rack': 'Rack location',
    'console_port': 'Console port used',
    'state': 'Current state',
    'distribution': 'Distribution used',
    'environment_id': 'ID of environment of residence',
    'spec_id': 'ID of the specification of this host',
    'dc_id': 'ID of the data center where this host resides',
}

HOST_DEPLOYMENT_DESCRIPTIONS = {
    'id': 'Unique integer identifier',
    'deployment_id': 'ID of containing deployment',
    'host_id': 'ID of host target for deployment',
    'package_id': 'ID of the package being deployed',
    'status': 'Current status',
    'user': 'Username of creator',
    'duration': 'Float seconds the installer daemon worked on this host '
        'deployment',
    'realized': 'When this host deployment was created',
}

PACKAGE_DESCRIPTIONS = {
    'id': 'Unique integer identifier',
    'version': 'Version number',
    'revision': 'Revision number',
    'status': 'Current status',
    'builder': 'Entity that built the package',
    'job': 'Name of Jenkins job',
    'application_id': "Unique integer identifier for the package's "
        "application",
    'created': 'When this package was created',
    'user': 'User who added this package',
    'name': 'Name of the application of this package',
    'project_type': 'The type of project to which this package belongs',
}

PROJECT_DESCRIPTIONS = {
    'id': 'Unique integer identifier',
    'name': 'Unique string identifier',
}

TIER_DESCRIPTIONS = {
    'id': 'Unique integer identifier',
    'name': 'Unique string identifier',
    'distribution': 'Distribution used',
    'puppet_class': 'Puppet class used',
    'ganglia_id': 'ID of Ganglia group',
    'ganglia_name': 'Name of Ganglia group',
    'status': 'Current status',
    'description': 'Description of this tier',
    'host_base': 'Base for hosts in this tier',
}

TIER_DEPLOYMENT_DESCRIPTIONS = {
    'id': 'Unique integer identifier',
    'deployment_id': 'ID of containing deployment',
    'tier_id': 'ID of tier target for deployment',
    'package_id': 'ID of the package being deployed',
    'status': 'Current status',
    'environment_id': 'ID of environment location for deployment',
    'user': 'Username of creator',
    'skewed': "Whether the application has different host deployment versions",
    'duration': 'Float seconds the installer daemon worked on this tier '
        'deployment',
    'realized': 'When this tier deployment was created',
}
