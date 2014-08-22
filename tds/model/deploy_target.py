'''Model module for deployment target object'''

from .base import Base
import tagopsdb


class DeployTarget(Base):
    '''
    A deploy target is something that can be deployed to
    examples:
        host
        apptype
        a list of hosts or apptypes
    '''
    # name / app_type
    # distribution
    # host_base
    # puppet_class
    # ganglia
    # ganglia_group_name  # XXX: this should be part of ganglia object
    # app_deployments
    # hipchats
    # hosts
    # host_specs
    # applications (aka package_definitions)
    # nag_app_services
    # nag_host_services
    # package_definitions
    # projects
    #

    # TODO: make subclasses where only one is an AppDefinition
    delegate = tagopsdb.AppDefinition
