from __future__ import absolute_import

import getpass

# pifou library
import pifou.om
import pifou.filter
import pifou.pom.node
import pifou.pom.domain

# pigui library
import pigui.style
import pigui.service
import pigui.pyqt5.event
import pigui.pyqt5.model
import pigui.pyqt5.widgets.item
import pigui.pyqt5.widgets.list.view
import pigui.pyqt5.widgets.miller.view
import pigui.pyqt5.widgets.application.widget

# pigui dependency
from PyQt5 import QtCore
from PyQt5 import QtWidgets

# local library
import dash.item
import dash.filter
import dash.settings

pigui.style.register('dash')


class Model(pigui.pyqt5.model.UriModel):
    def pull(self, index):
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
            if path.endswith('.workspace'):
                for command in ('launch', 'configure', 'remove'):
                    idx = self.create_index()

                    uri = 'command:' + path + '?' + command

                    item = self.create_item(uri=uri, parent=root)
                    item.index = idx
                    self.indexes[idx] = item


def create_item(self, label, index, parent=None):
    model_item = self.model.item(index)

    scheme = model_item.scheme
    args, kwargs = model_item.options

    if 'workspace' in args:
        return dash.item.WorkspaceItem(label, index, parent)

    if scheme == 'command':
        command = args[0]
        return dash.item.CommandItem(command, index, parent)

    item = dash.item.TreeItem(label, index, parent)
    return item


# Monkey-patch ListView
pigui.pyqt5.widgets.list.view.DefaultList.create_item = create_item


class Dash(pigui.pyqt5.widgets.application.widget.ApplicationBase):
    launch = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(Dash, self).__init__(parent)

        # Pad the view, and inset background via CSS
        canvas = QtWidgets.QWidget()
        canvas.setObjectName('Canvas')

        # model = pigui.pyqt5.model.UriModel()
        model = Model()

        view = pigui.pyqt5.widgets.miller.view.DefaultMiller()
        view.setObjectName('View')
        view.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                           QtWidgets.QSizePolicy.MinimumExpanding)

        view.set_model(model)

        layout = QtWidgets.QHBoxLayout(canvas)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addWidget(view)

        widget = QtWidgets.QWidget()

        layout = QtWidgets.QHBoxLayout(widget)
        layout.addWidget(canvas)
        layout.setContentsMargins(5, 0, 5, 5)
        layout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

        self.set_widget(widget)

        self.view = view
        self.model = model

    def setup(self, uri):
        self.model.setup(uri)

    def event(self, event):
        type = event.type()

        if type == dash.event.Type.OpenInExplorerEvent:
            item = self.model.item(event.index)
            pigui.service.open_in_explorer(item.path)

        elif type == dash.event.Type.CommandEvent:
            item = self.model.item(event.index)
            print item.path
            # if event.command == 'launch':
            #     if self.confirm("{}\n\nLaunch?".format(event.path)):
            #         self.launch.emit(event.path)

        return super(Dash, self).event(event)


if __name__ == '__main__':
    import pigui.pyqt5.util

    with pigui.pyqt5.util.application_context():
        win = Dash()

        win.setup(uri=r'disk:c:\studio\content')
        win.resize(*dash.settings.WINDOW_SIZE)
        win.show()
