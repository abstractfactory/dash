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


import logging
log = logging.getLogger('dash')
log.setLevel(logging.WARNING)

if __name__ == '__main__':
    check_dependencies()
    add_to_path()

    import dash.version

    message = '''
 ____________
|            |
| Dash {} |
|____________|

Press CTRL-C to quit..

-----------------------
'''.format(dash.version.version)
    print message

    import dash.presentation
    path = get_path()

    print "I: running Dash @ %r" % path
    dash.presentation.main(path)
