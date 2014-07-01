'''Model module for deployment object'''

from .base import Base
import tagopsdb

class Deployment(Base):
    'Model class for deployment object'

class TDSAppDeployment(Deployment, tagopsdb.AppDeployment):
    'Model class for deployment of an application'


# Class name shuffle to make sqlalchemy happy
AppDeployment = TDSAppDeployment
