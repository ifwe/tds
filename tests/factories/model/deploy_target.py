import factory
import tds.model.deploy_target as d


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
