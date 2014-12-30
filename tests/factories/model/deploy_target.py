"""
Bacic factories for apptype deployment and host deployment targets.
"""

import factory
import tds.model.deploy_target as d
import tagopsdb as t


class AppTargetFactory(factory.Factory):
    '''
    Basic factory for apptype deployment target
    '''
    FACTORY_FOR = d.AppTarget


class HostTargetFactory(factory.Factory):
    '''
    Basic factory for host deployment target
    '''

    FACTORY_FOR = d.HostTarget


class HipchatFactory(factory.Factory):
    """
    Basic factory for HipChat object.
    """

    FACTORY_FOR = t.Hipchat
