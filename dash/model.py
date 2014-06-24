
# standard library
import os
import getpass

# pigui library
import pifou.pom.node
import pifou.pom.domain
import pifou.com.source

# pigui library
import pigui.pyqt5.model

Command = 'command'
Workspace = 'workspace'


class Item(pigui.pyqt5.model.ModelItem):
    """Wrap pifou.pom.node in ModelItem

     _______________________
    |          Item         |
    |   ____________________|
    |  |__________________
    | |-                  |
    | |-  pifou.pom.node  |
    | |-__________________|
    |__|

    """

    def data(self, key):
        """Intercept queries custom to Dash

        Interceptions:
            disk: Disk queries are wrapped in pifou.pom.node
            command: Commands contain the extra key "command"
            workspace: Workspaces wrap nodes similar to disk

        """

        value = super(Item, self).data(key)

        if not value and self.data('type') in (pigui.pyqt5.model.Disk,
                                               Command,
                                               Workspace):
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
        assert isinstance(parent, basestring) or parent is None
        item = Item(data, parent=self.indexes.get(parent))
        self.register_item(item)
        return item

    def set_data(self, index, key, value):
        if key == pigui.pyqt5.model.Display:
            """Rename `index` to `value`"""
            path = self.data(index, 'path')
            suffix = self.data(index, 'suffix')

            basename = value
            suffix = suffix

            if suffix:
                basename += '.' + suffix

            dirname = os.path.dirname(path)

            old_path = path
            new_path = os.path.join(dirname, basename)

            try:
                os.rename(old_path, new_path)
            except OSError as e:
                self.log.error(str(e))
                return self.error.emit(e)
            else:
                old = os.path.basename(old_path)
                new = os.path.basename(new_path)
                self.status.emit("Renamed {} to {}".format(old, new))

            # Update node with new name
            self.set_data(index, key='path', value=basename)

        super(Model, self).set_data(index, key, value)

    def remove_workspace(self, index):
        """`index` will point to the action of the workspace"""
        parent = self.item(index).parent.index
        self.remove_item(parent)
        self.status.emit("Workspace removed")

    def add_workspace(self, path, parent):
        """

        Arguments:
            path (str): Path to workspace
            parent (str): Index of new workspace

        """

        node = pifou.pom.node.Node.from_str(path)
        path = node.path.as_str
        assert not os.path.exists(path)

        try:
            # Physically instantiate node
            os.makedirs(path)

            # Imprint metadata
            loc = pifou.om.Location(path)
            pifou.om.Entry('Workspace.class', parent=loc)
            pifou.om.flush(loc)

        except Exception as e:
            # Basic error "handling"
            return self.error.emit(e)

        self.add_item({'type': 'workspace',
                       'node': node}, parent=parent)
        self.status.emit("Workspace added")

    def pull(self, index):
        if self.data(index, 'type') == 'disk':
            node = self.data(index, 'node')

            try:
                pifou.com.source.disk.pull(node)
            except pifou.error.Exists:
                self.status.emit("%s did not exist" % node.path)

            for child in node.children:
                self.create_item({'type': 'disk',
                                  'node': child}, parent=index)

            # Append workspaces
            user = getpass.getuser()
            asset = pifou.pom.domain.Entity.from_node(node)
            for workspace in asset.workspaces(user):
                self.create_item({'type': 'workspace',
                                  'node': workspace,
                                  'sortkey': '|'}, parent=index)

        # Append commands to workspaces
        if self.data(index, 'type') == 'workspace':
            node = self.data(index, 'node')
            for command in ('launch', 'configure', 'remove'):
                self.create_item({'type': 'command',
                                  'node': node,
                                  'command': command}, parent=index)

        super(Model, self).pull(index)
