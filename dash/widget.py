from __future__ import absolute_import

import itertools

# pifou library
import pifou.filter
import pifou.pom.node
import pifou.pom.domain

# pigui library
import pigui.style
import pigui.service
import pigui.pyqt5.event
import pigui.pyqt5.model
import pigui.pyqt5.widgets.miller.view
import pigui.pyqt5.widgets.window.widget

# pigui dependency
from PyQt5 import QtCore
from PyQt5 import QtWidgets

# local library
import dash.item
import dash.filter
import dash.settings

pigui.style.register('dash')


class Model(pigui.pyqt5.model.FileSystemModel):
    def children(self, path):

        def workspaces(path):
            node = pifou.pom.node.Node.from_str(path)
            asset = pifou.pom.domain.Entity.from_node(node)
            for workspace in asset.workspaces('marcus'):
                path = workspace.path.as_str
                yield path

        def workspace_commands(path):
            for command in ('launch', 'configure', 'remove'):
                yield "{path}?type=command#command={command}".format(
                    path=path,
                    command=command)

        iterators = [super(Model, self).children(path)]
        iterators.append(workspaces(path))

        if path.endswith('.workspace'):
            iterators.append(workspace_commands(path))

        for child in itertools.chain(*iterators):
            yield child


class List(pigui.pyqt5.widgets.list.view.DefaultList):
    def create_item(self, path):
        item = dash.item.from_path(path)
        return item


class Miller(pigui.pyqt5.widgets.miller.view.DefaultMiller):
    def create_list(self):
        lis = List()
        return lis

    def create_model(self):
        model = Model()
        model.postfilter.add(dash.filter.discard_files)
        model.postfilter.add(pifou.filter.post_hide_hidden)
        return model


class Dash(pigui.pyqt5.widgets.window.widget.WindowBase):
    launch = QtCore.pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(Dash, self).__init__(*args, **kwargs)

        # Pad the view, and inset background via CSS
        canvas = QtWidgets.QWidget()
        canvas.setObjectName('Canvas')

        view = Miller()
        view.setObjectName('View')
        view.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                           QtWidgets.QSizePolicy.MinimumExpanding)

        layout = QtWidgets.QHBoxLayout(canvas)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addWidget(view)

        widget = QtWidgets.QWidget()

        layout = QtWidgets.QHBoxLayout(widget)
        layout.addWidget(canvas)
        layout.setContentsMargins(5, 0, 5, 5)
        layout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

        self.set_widget(widget)

    def setup(self, path):
        view = self.findChild(QtWidgets.QWidget, 'View')
        view.add_list(path)

    def event(self, event):
        type = event.type()

        if type == dash.event.Type.OpenInExplorerEvent:
            pigui.service.open_in_explorer(event.path)

        elif type == dash.event.Type.CommandEvent:
            if event.command == 'launch':
                self.launch.emit(event.path)

        return super(Dash, self).event(event)


if __name__ == '__main__':
    import pigui.pyqt5.util

    with pigui.pyqt5.util.application_context():
        win = Dash()

        win.setup('/c/studio/content')
        win.resize(*dash.settings.WINDOW_SIZE)
        win.show()
