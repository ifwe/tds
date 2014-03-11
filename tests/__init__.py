'Tests and supporting files for TDS'

from os.path import join, dirname, abspath

FIXTURES_PATH = join(dirname(abspath(__file__)), 'fixtures')

__all__ = ['FIXTURES_PATH']
