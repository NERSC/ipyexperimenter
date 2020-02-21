from ._version import version_info, __version__

from .experimenter import *

def _jupyter_nbextension_paths():
    return [{
        'section': 'notebook',
        'src': 'static',
        'dest': 'ipyexperimenter',
        'require': 'ipyexperimenter/extension'
    }]
