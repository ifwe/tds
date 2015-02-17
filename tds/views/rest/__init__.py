"""
REST API for TDS.
"""

from pyramid.config import Configurator


config = Configurator()
config.include("cornice")
config.scan()
