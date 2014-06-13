
import os
import getpass

# pifou library
import pifou.om
import pifou.error
import pifou.pom.node
import pifou.pom.domain
import pifou.com.source

# pigui library
import pigui.pyqt5.model


class Model(pigui.pyqt5.model.UriModel):
    def add_item(self, uri, parent):
        """Physically create `uri` on disk"""

        scheme, path = uri.split(":", 1)

        try:
            path, _ = path.split("?", 1)
        except ValueError:
            pass

        if os.path.exists(path):
            raise pifou.error.Exists('%s already exists' % path)

        try:
            os.makedirs(path)
        except OSError:
            raise

        super(Model, self).add_item(uri, parent)

    def has_data(self, index, role):
        item = self.indexes[index]
        if item.scheme == 'disk':
            return pifou.om.find(item.path, role)
        return super(Model, self).has_data(index, role)

    def children(self, index):
        for child in super(Model, self).children(index):
            if not self.has_data(child.index, 'hidden'):
                yield child

    def pull(self, index):
        """Append Dash items

        Append workspace-items, and workspace commands
        to folders containing workspaces for the currently
        logged on user.

        """

        super(Model, self).pull(index)

        root = self.indexes[index]
        path = root.path
        scheme = root.scheme

        if scheme == 'disk':
            # Add workspaces
            user = getpass.getuser()
            node = pifou.pom.node.Node.from_str(path)
            asset = pifou.pom.domain.Entity.from_node(node)
            for workspace in asset.workspaces(user):
                full_path = workspace.path.as_str
                idx = self.create_index()

                uri = scheme + ":" + full_path + "?workspace"

                item = self.create_item(uri=uri, parent=root)
                item.index = idx

                self.indexes[idx] = item

            # Add workspace commands
            if root.data(role='type') == 'workspace':
                for command in ('launch', 'configure', 'remove'):
                    idx = self.create_index()

                    uri = scheme + ":" + path + '?command=' + command

                    item = self.create_item(uri=uri, parent=root)
                    item.index = idx

                    self.indexes[idx] = item
