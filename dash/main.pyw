#!python

"""Main entry point for build"""

import os


# ------------------------------------------------------------


import pifou
if pifou.missing_dependencies:
    import pifou.error
    raise pifou.error.Dependency(pifou.missing_dependencies)

from dash import presentation

# Make working directory local to Dashboard,
# regardless of where this executable is being run from.
# (This is important for local stylesheets to have any effect)
working_directory = os.path.dirname(presentation.__file__)
os.chdir(working_directory)

import logging
log = logging.getLogger('dash')
log.setLevel(logging.WARNING)

if __name__ == '__main__':
    presentation.request_application()
    # presentation.start_application(debug=True)
    # presentation.start_debug()
