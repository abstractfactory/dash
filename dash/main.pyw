"""Main entry point for build"""

# standard library
import logging
import argparse

# local library
import dash.version
import dash.presentation

log = logging.getLogger('dash')
log.setLevel(logging.WARNING)

message = '''
____________
|            |
| Dash {} |
|____________|

Press CTRL-C to quit..

-----------------------
'''.format(dash.version.version)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help="Absolute path to root directory")

    args = parser.parse_args()

    print message
    print "I: running Dash @ %r" % args.path

    dash.presentation.main(path=args.path)
