
import pifou.metadata
import pifou.filter

from pifou.com import source


@pifou.filter.Operator.cascading
def post_hide_hidden(node):
    """Hide `hidden` elements"""
    if not pifou.metadata.find(node.path.as_str, 'hidden'):
        return node


@pifou.filter.Operator.cascading
def pre_junction(node):
    """Forward junctions to target `goto`
        _________
       |         |
       |         v
       o    o    o

    """

    junction = pifou.metadata.read(node.path.as_str, 'junction')

    if junction:
        assert isinstance(junction, basestring)
        junction_path = node.path + junction
        junction_node = node.copy(path=junction_path)

        source.disk.pull(junction_node)

        node = junction_node

    return node


@pifou.filter.Operator.cascading
def discard_files(node):
    if node.isparent:
        return node
