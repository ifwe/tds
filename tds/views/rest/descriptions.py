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
}

APPLICATION_TIER_DESCRIPTIONS = {
    'project_id': 'Unique integer identifier for the project',
    'application_id': 'Unique integer identifier for the application',
    'tier_id': 'Unique integer indentifier for the tier',
}

DEPLOYMENT_DESCRIPTIONS = {
    'id': 'Unique integer identifier',
    'user': 'Username of creator',
    'status': 'Current status of the deployment',
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
    'kernel_version': 'Version string of OS kernel',
    'console_port': 'Console port used',
    'power_port': 'Power port used',
    'power_circuit': 'Power circuit used',
    'state': 'Current state',
    'arch': 'Binary architecture supported',
    'distribution': 'Distribution used',
    'timezone': 'Timezone of residence',
    'environment_id': 'ID of environment of residence',
}

HOST_DEPLOYMENT_DESCRIPTIONS = {
    'id': 'Unique integer identifier',
    'deployment_id': 'ID of containing deployment',
    'host_id': 'ID of host target for deployment',
    'package_id': 'ID of the package being deployed',
    'status': 'Current status',
    'user': 'Username of creator',
}

PACKAGE_DESCRIPTIONS = {
    'id': 'Unique integer identifier',
    'version': 'Version number',
    'revision': 'Revision number',
    'status': 'Current status',
    'builder': 'Entity that built the package',
    'job': 'Name of Jenkins job',
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
}

TIER_DEPLOYMENT_DESCRIPTIONS = {
    'id': 'Unique integer identifier',
    'deployment_id': 'ID of containing deployment',
    'tier_id': 'ID of tier target for deployment',
    'package_id': 'ID of the package being deployed',
    'status': 'Current status',
    'environment_id': 'ID of environment location for deployment',
    'user': 'Username of creator',
}
