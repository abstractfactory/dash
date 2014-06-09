
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


class List(pigui.pyqt5.widgets.list.view.DefaultList):

    def __init__(self, *args, **kwargs):
        super(List, self).__init__(*args, **kwargs)
        self._existing_workspaces = []

    def item_added_event(self, item):
        super(List, self).item_added_event(item)

    def load(self, item):
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
            node = pifou.pom.node.Node.from_str(path)

            workspace = item.from_node(node)
            workspace.data['parent'] = item

            self.add_item(workspace)
            self._existing_workspaces.append(node)

    def append_new_item(self, item):
        """
         _____________________
        |                     |
        |  Add new workspace  |
        |_____________________|

        """

        new_item = pigui.item.Item.from_name('new.+')
        new_item.data['parent'] = item
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
            command_item.data['command'] = command
            command_item.data['subject'] = item
            pol = command_item.sortpolicy
            pol.position = pol.AlwaysAtBottom
            self.add_item(command_item)

            if command == 'configure':
                command_item.widget.setEnabled(False)


def register():
    pigui.widgets.pyqt5.miller.view.DefaultMiller.register(List)


if __name__ == '__main__':
    from pifou.com import source
    import pifou.pom.node
    import pigui.util.pyqt5

    # import dash.item
    dash.item.register()

    with pigui.util.pyqt5.app_context():
        register()

        node = pifou.pom.node.Node.from_str(r'S:\content\jobs\skydivers\content\assets\diver\model_animation_default')
        source.disk.pull(node)

        item = pigui.item.Item.from_node(node)
        view = pigui.widgets.pyqt5.miller.view.DefaultMiller()
        view.load(item)
        view.resize(600, 300)
        view.show()
