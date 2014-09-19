'''
Factories to create various tds.model.application.Application instances
'''
import factory
import tds.model.application as a


class ApplicationFactory(factory.Factory):
    '''
    Application
    '''
    FACTORY_FOR = a.Application

    name = 'fake_package'
    path = '/job/fake_package'
    build_host = 'ci.fake.com'
    environment = False
