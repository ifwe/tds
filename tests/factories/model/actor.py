'''
Factories to create various tds.model.deployment.Actor instances
'''
import factory
import tds.model.actor as a


class ActorFactory(factory.Factory):
    '''
    Basic user factory
    '''
    FACTORY_FOR = a.Actor

    name = 'fake_user'
    groups = ['engteam']
