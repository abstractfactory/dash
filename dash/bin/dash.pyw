#!python

"""Main entry point for build"""

import os
import sys


def add_to_path():
    root = os.path.abspath(__file__)
    for x in range(3):
        root = os.path.dirname(root)
    sys.path.insert(0, root)
    print "I: adding %r to PYTHONPATH" % root


def check_dependencies():
    import pifou
    if pifou.missing_dependencies:
        import pifou.error
        raise pifou.error.Dependency(pifou.missing_dependencies)


def get_path():
    try:
        path = sys.argv[1]
        print "I: Using ARGS"
    except:
        path = os.getcwd()
        print "I: Using CWD"
    return path


def init_cwd():
    # Make working directory local to Dash,
    # regardless of where this executable is being run from.
    # (This is important for local stylesheets to have any effect)
    working_directory = os.path.dirname(dash.presentation.__file__)
    os.chdir(working_directory)


import logging
log = logging.getLogger('dash')
log.setLevel(logging.WARNING)

if __name__ == '__main__':
    message = '''
 ____________
|            |
| Dash 0.5.2 |
|____________|

Press CTRL-C to quit..

-----------------------
'''
    print message
    check_dependencies()
    add_to_path()

    import dash.presentation
    path = get_path()
    init_cwd()

    print "I: running Dash @ %r" % path
    dash.presentation.main(path)

    path = dash.presentation.get_root()
    dash.presentation.request_application(path)
