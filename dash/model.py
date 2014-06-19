
import getpass

# pigui library
import pifou.pom.node
import pifou.pom.domain
import pifou.com.source

# pigui library
import pigui.pyqt5.model


class Item(pigui.pyqt5.model.ModelItem):
    """Wrap pifou.pom.node in ModelItem

     _______________________
    |   pigui.pyqt5.model   |
    |   ____________________|
    |  |__________________
    | |-                  |
    | |-  pifou.pom.node  |
    | |-__________________|
    |__|

    """

    def data(self, key):
        value = super(Item, self).data(key)

        if not value:
            if key == 'path':
                node = self.data('node')
                return node.path.as_str

            if key == 'display':
                node = self.data('node')
                return node.path.name

            if key == 'group':
                node = self.data('node')
                return node.isparent

        return value


class Model(pigui.pyqt5.model.Model):
    def setup(self, path):
        node = pifou.pom.node.Node.from_str(path)
        root = self.create_item({'type': 'disk',
                                 'node': node})
        self.root_item = root
        self.model_reset.emit()

    def create_item(self, data, parent=None):
        item = Item(data, parent)
        self.register_item(item)
        return item

    def remove_workspace(self, index):
        """`index` will point to the action of the workspace"""
        parent = self.item(index).parent.index
        self.remove_item(parent)
        self.status.emit("Workspace removed")

    def add_workspace(self, path, index):
        parent = self.item(index)
        node = pifou.pom.node.Node.from_str(path)
        self.add_item({'type': 'workspace',
                       'node': node}, parent=parent)
        self.status.emit("Workspace added")

    def pull(self, index):
        if self.data(index, 'type') == 'disk':
            parent = self.item(index)
            node = self.data(index, 'node')

            try:
                pifou.com.source.disk.pull(node)
            except pifou.error.Exists:
                pass

            for child in node.children:
                self.create_item({'type': 'disk',
                                  'node': child}, parent=parent)

            # Append workspaces
            user = getpass.getuser()
            asset = pifou.pom.domain.Entity.from_node(node)
            for workspace in asset.workspaces(user):
                self.create_item({'type': 'workspace',
                                  'node': workspace}, parent=parent)

        # Append commands to workspaces
        if self.data(index, 'type') == 'workspace':
            parent = self.item(index)
            node = self.data(index, 'node')
            for command in ('launch', 'configure', 'remove'):
                self.create_item({'type': 'command',
                                  'node': node,
                                  'command': command}, parent=parent)

        super(Model, self).pull(index)
