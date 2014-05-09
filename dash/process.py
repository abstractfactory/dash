
import pifou.lib
import pifou.pom.domain
import pifou.pom.node

from pifou.com import source

import openmetadata as om


# ---------------------- Node Processes ------------------------- #


@pifou.lib.Process.cascading
def post_hide_hidden(node):
    """Hide `hidden` elements"""
    # location = om.Location(node.url.path.as_str)
    if not om.find(node.path.as_str, 'hidden'):
        return node


@pifou.lib.Process.cascading
def pre_junction(node):
    """Forward junctions to target `goto`
        _________
       |         |
       |         v
       o    o    o

    """

    junction = om.read(node.path.as_str, 'junction')

    if junction:
        assert isinstance(junction, basestring)
        junction_path = node.path + junction
        junction_node = node.copy(path=junction_path)

        source.disk.pull(junction_node)

        node = junction_node

    return node


# if __name__ == '__main__':
#     om.read(path)