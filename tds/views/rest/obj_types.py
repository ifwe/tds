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
    'created': 'timestamp',
}

APPLICATION_TIER_TYPES = {
    'project_id': 'integer',
    'application_id': 'integer',
    'tier_id': 'integer',
}

DEPLOYMENT_TYPES = {
    'id': 'integer',
    'user': 'string',
    'status': 'choice',
    'delay': 'integer',
    'duration': 'number',
    'declared': 'timestamp',
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
    'console_port': 'string',
    'state': 'choice',
    'distribution': 'string',
    'environment_id': 'integer',
    'spec_id': 'integer',
    'dc_id': 'integer',
}

HOST_DEPLOYMENT_TYPES = {
    'id': 'integer',
    'deployment_id': 'integer',
    'host_id': 'integer',
    'package_id': 'integer',
    'status': 'choice',
    'user': 'string',
    'duration': 'number',
    'realized': 'timestamp',
}

PACKAGE_TYPES = {
    'id': 'integer',
    'version': 'integer',
    'revision': 'integer',
    'status': 'choice',
    'builder': 'choice',
    'job': 'string',
    'application_id': 'integer',
    'created': 'timestamp',
    'creator': 'string',
    'project_type': 'choice',
}

PROJECT_TYPES = {
    'id': 'number',
    'name': 'string',
}

TIER_TYPES = {
    'id': 'integer',
    'name': 'string',
    'distribution': 'string',
    'puppet_class': 'string',
    'ganglia_id': 'integer',
    'ganglia_name': 'string',
    'status': 'choice',
    'description': 'string',
    'host_base': 'string',
}

TIER_DEPLOYMENT_TYPES = {
    'id': 'integer',
    'deployment_id': 'integer',
    'tier_id': 'integer',
    'package_id': 'integer',
    'status': 'choice',
    'environment_id': 'integer',
    'user': 'string',
    'skewed': 'boolean',
    'duration': 'number',
    'realized': 'timestamp',
}
