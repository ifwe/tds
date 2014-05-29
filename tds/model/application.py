'''Model module for application object'''

from .base import Base
import tagopsdb


class Application(Base, tagopsdb.PackageDefinition):
    'Represents a single application'
    # name
    # path
    # build_host
    # environment
    # packages / versions
