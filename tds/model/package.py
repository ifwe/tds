'''Model module for package object'''

from .base import Base
import tagopsdb

class Package(Base):
    'Represents a deployable package for a version of an application'
    # name
    # version
    # application

    delegate = tagopsdb.Package
