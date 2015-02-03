"""
REST API for TDS.
"""

from pyramid.config import Configurator
from .projects import ProjectView


config = Configurator()
config.include("cornice")
config.scan()
