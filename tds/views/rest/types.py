"""
JSON types for different resources.
"""

APPLICATION_TYPES = {
    'id': 'integer',
    'name': 'string',
    'job': 'string',
    'build_host': 'string',
    'build_type': 'choice',
    'deploy_type': 'string',
    'arch': 'choice',
    'validation_type': 'string',
    'env_specific': 'boolean',
}

DEPLOYMENT_TYPES = {
    'id': 'integer',
    'user': 'string',
    'status': 'choice',
}

ENVIRONMENT_TYPES = {
    'id': 'integer',
    'name': 'string',
    'short_name': 'string',
    'domain': 'string',
    'prefix': 'string',
    'zone_id': 'integer',
}

GANGLIA_TYPES = {
    'id': 'integer',
    'name': 'string',
    'port': 'integer',
}

HIPCHAT_TYPES = {
    'id': 'integer',
    'name': 'string',
}

HOST_TYPES = {
    'id': 'integer',
    'name': 'string',
    'tier_id': 'integer',
    'cage': 'integer',
    'cab': 'string',
    'rack': 'integer',
    'kernel_version': 'string',
    'console_port': 'string',
    'power_port': 'string',
    'power_circuit': 'string',
    'state': 'choice',
    'arch': 'choice',
    'distribution': 'choice',
    'timezone': 'string',
    'environment_id': 'integer',
}

HOST_DEPLOYMENT_TYPES = {
    'id': 'integer',
    'deployment_id': 'integer',
    'host_id': 'integer',
    'package_id': 'integer',
    'status': 'choice',
    'user': 'string',
}

PACKAGE_TYPES = {
    'id': 'integer',
    'version': 'integer',
    'revision': 'integer',
    'status': 'choice',
    'builder': 'choice',
    'job': 'string',
}

PROJECT_TYPES = {
    'id': 'number',
    'name': 'string',
}

TIER_TYPES = {
    'id': 'integer',
    'name': 'string',
    'distribution': 'choice',
    'puppet_class': 'string',
    'ganglia_id': 'integer',
    'ganglia_name': 'string',
    'status': 'choice',
}

TIER_DEPLOYMENT_TYPES = {
    'id': 'integer',
    'deployment_id': 'integer',
    'tier_id': 'integer',
    'package_id': 'integer',
    'status': 'choice',
    'environment_id': 'integer',
    'user': 'string',
}
