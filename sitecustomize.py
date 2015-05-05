import os.path
import site

script_directory = os.path.dirname(__file__)
module_directory = os.path.join(
    script_directory, 'features', 'helpers', 'lib'
)

site.addsitedir(module_directory)
