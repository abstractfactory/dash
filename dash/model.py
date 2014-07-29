"""Custom model for Dash

Attributes:
    COMMAND: The command-item type
    Workspace: The workspace-item type

"""

# standard library
import os

# pigui library
import pifou.com
import pifou.metadata
import pifou.domain.workspace

# pigui library
import pigui.pyqt5.model

COMMAND = 'command'
WORKSPACE = 'workspace'


class Iterator(pifou.com.Iterator):
    """Custom iterator for Dash

    Dash traverses the COM differently from ``os.walk`` and this iterator
    reflects that.

    """

    def __init__(self, *args, **kwargs):
        super(Iterator, self).__init__(*args, **kwargs)

        if not self.filter:
            self.filter = pifou.com.default_filter


class Item(pigui.pyqt5.model.ModelItem):
    """Custom model-item for Dash"""

    def data(self, key):
        """Custom intercept for Dash"""
        value = super(Item, self).data(key)

        if not value and self.data('type') in (pigui.pyqt5.model.Disk,
                                               COMMAND,
                                               WORKSPACE):
            if key == 'display':
                path = self.data('path')
                basename = os.path.basename(path)
                name, ext = os.path.splitext(basename)
                self.set_data('display', name)
                return name

            if key == 'group':
                path = self.data('path')
                isgroup = os.path.isdir(path)
                self.set_data('group', isgroup)
                return isgroup

        return value


class Model(pigui.pyqt5.model.Model):
    """Dash-specific model

    Dash adds a number of items, most prominently the workspaces
    along with corresponding actions, such as "Launch".

    """

    def setup(self, root):
        """Custom setup for Dash

        Arguments:
            root (str): Absolute path from which to populate model.

        """

        root = self.create_item({'type': 'disk',
                                 'path': root})
        self.root_item = root
        self.model_reset.emit()

    def create_item(self, data, parent=None):
        """Overridden to accommodate for custom Item (see above)"""
        assert isinstance(parent, basestring) or parent is None
        item = Item(data, parent=self.indexes.get(parent))
        self.register_item(item)
        return item

    def set_data(self, index, key, value):
        """Overridden to accommodate for data custom to Dash

        Overridden data:
            Display: When altering the name of any item within the
                model, also alter the physical name on disk. If
                unsuccessful, do not alter item and alert user.

        """

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
        """Remove workspace at index `index`

        .. note:: `index` will point to the action of the workspace

        """

        parent = self.item(index).parent.index
        self.remove_item(parent)
        self.status.emit("Workspace removed")

    def add_workspace(self, root, application, parent):
        """Add workspace at absolute path `root` for application `application`

        Arguments:
            root (str): Path to workspace
            application (str): Name of application
            parent (str): Index of parent to new workspace

        """

        workspace = pifou.domain.workspace.assemble(root=root,
                                                    application=application)

        if os.path.exists(workspace):
            self.error.emit(ValueError("%s already exists" % workspace))

        try:
            # Physically instantiate node
            os.makedirs(workspace)

            # Imprint metadata
            loc = pifou.metadata.Location(workspace)
            pifou.metadata.Entry('Workspace.class', parent=loc)
            pifou.metadata.flush(loc)

        except Exception as e:
            return self.error.emit(e)

        print "Adding item: %s" % root
        self.add_item({'type': 'workspace',
                       'path': workspace}, parent=parent)
        self.status.emit("Workspace added")

    def pull(self, index):
        """Populate item at index `index` with content from disk

        Arguments:
            index (str): Index of item within model, the path
                from which is used as root for read.

        """

        self.add_header(index)

        if self.data(index, 'type') == 'disk':
            path = self.data(index, 'path')

            # Is there a junction involved?
            junction = pifou.metadata.read(path, 'junction.string')
            if junction:
                path = os.path.join(path, junction)

            if os.path.exists(path):
                for basename in Iterator(path):
                    fullpath = os.path.join(path, basename)
                    self.create_item({'type': 'disk',
                                      'path': fullpath}, parent=index)
            else:
                self.status.emit("%s did not exist" % path)

            # Append workspaces
            for workspace in pifou.domain.workspace.ls(path):
                full_path = os.path.join(path, workspace)
                self.create_item({'type': 'workspace',
                                  'path': full_path,
                                  'sortkey': '|'}, parent=index)

            self.add_footer(index)

        # Append commands to workspaces
        elif self.data(index, 'type') == 'workspace':
            path = self.data(index, 'path')
            for command in ('launch', 'configure', 'remove'):
                self.create_item({'type': 'command',
                                  'path': path,
                                  'command': command}, parent=index)

        else:
            self.add_footer(index)
