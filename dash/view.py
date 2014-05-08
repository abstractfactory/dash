
"""Dashboard-specific subclass of Listview"""

# pifou library
import pifou.lib
import pifou.pom.node
import pifou.signal

# pigui library
import pigui.item
import pigui.widgets.pyqt5.list.view
import pigui.widgets.pyqt5.miller.view

# local library
import dash.item


class Miller(pigui.widgets.pyqt5.miller.view.DefaultMiller):
    def __init__(self, *args, **kwargs):
        super(Miller, self).__init__(*args, **kwargs)

    def column_added_event(self, column):
        super(Miller, self).column_added_event(column)


class List(pigui.widgets.pyqt5.list.view.DefaultList):

    predicate = Miller

    def __init__(self, *args, **kwargs):
        super(List, self).__init__(*args, **kwargs)
        self._existing_workspaces = []

    def item_added_event(self, item):
        super(List, self).item_added_event(item)

    def load(self, item):
        # print "Loading %s" % item
        super(List, self).load(item)

        self.append_workspace_items(item)

        if isinstance(item, dash.item.DashboardItem):
            self.append_new_item(item)

        if isinstance(item, dash.item.WorkspaceItem):
            self.append_workspace_commands(item)

    def append_workspace_items(self, item):
        """
         _____________________
        |                     |
        | Existing workspaces |
        |_____________________|

        """

        asset = pifou.pom.domain.Entity.from_node(item.node)
        for workspace in asset.workspaces('marcus'):
            path = workspace.url.path.as_str
            node = pifou.pom.node.DirNode.from_str(path)
            workspace = item.from_node(node)
            workspace.setdata('parent', item)

            workspace.preprocess = item.preprocess.copy()
            workspace.postprocess = item.postprocess.copy()

            self.add_item(workspace)
            self._existing_workspaces.append(node)

    def append_new_item(self, item):
        """
         _____________________
        |                     |
        |  Add new workspace  |
        |_____________________|

        """

        new_item = pigui.item.Item.from_name('+')
        new_item.widget.setText('Add workspace')
        new_item.setdata('parent', item)
        self.add_item(new_item)

    def append_workspace_commands(self, item):
        """
         ______________________
        |                      |
        |  Workspace commands  |
        |______________________|

        """

        for command in ('launch', 'configure', 'remove'):
            command_item = pigui.item.Item.from_type('%s.command' % command)
            command_item.setdata('command', command)
            command_item.setdata('subject', item)
            pol = command_item.sortpolicy
            pol.position = pol.AlwaysAtBottom
            self.add_item(command_item)

            if command == 'configure':
                command_item.widget.setEnabled(False)


def register():
    Miller.register(List)


if __name__ == '__main__':
    import pifou.pom.node
    import pigui.util.pyqt5

    # import dash.item
    dash.item.register()

    with pigui.util.pyqt5.app_context():
        register()

        node = pifou.pom.node.DirNode.from_str(r'S:\content\jobs\skydivers\content')
        item = pigui.item.Item.from_node(node)
        view = Miller()
        view.load(item)
        view.resize(300, 500)
        view.show()
