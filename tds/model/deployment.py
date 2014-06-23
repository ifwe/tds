'''Model module for deployment object'''

from .base import Base
import tagopsdb

class Deployment(Base):
    'Model class for deployment object'

class AppDeployment(Deployment, tagopsdb.AppDeployment):
    'Model class for deployment of an application'
