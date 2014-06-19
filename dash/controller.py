from __future__ import absolute_import

# standard library
import getpass

# pifou library
import pifou.lib

# pigui library
import pigui.style
import pigui.service
import pigui.pyqt5.event
import pigui.pyqt5.widgets.miller.view
import pigui.pyqt5.widgets.application.widget

# pigui dependency
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets

# local library
import dash.view
import dash.model
import dash.settings

pigui.style.register('dash')

dash.view.monkey_patch()


@pifou.lib.log
class Dash(pigui.pyqt5.widgets.application.widget.ApplicationBase):
    """Dash view"""

    launch = QtCore.pyqtSignal(str)  # index

    def __init__(self, parent=None):
        super(Dash, self).__init__(parent)

        # Pad the view, and inset background via CSS
        canvas = QtWidgets.QWidget()
        canvas.setObjectName('Canvas')

        view = pigui.pyqt5.widgets.miller.view.DefaultMiller()
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

        self.view = view
        self.model = None

    def set_model(self, model):
        self.view.set_model(model)
        self.model = model
        model.status.connect(self.status_event)

    def event(self, event):
        """Event handlers

        Handled events:
            AddItemEvent -- A workspace is being added
            CommandEvent -- A command is being executed
            OpenInExplorerEvent -- An item is being explored
            OpenInAboutEvent -- An item is being explored, in About

        """

        def add_item(index):
            self.add_workspace_menu(event.index)

        def command(index):
            command = self.model.data(event.index, 'command')

            if command == 'launch':
                path = self.model.data(event.index, 'path')
                message = path + "\n\n" + "Launch?"
                if self.confirm(message):
                    self.launch.emit(event.index)

            if command == 'configure':
                path = self.model.data(event.index, 'path')
                pigui.service.open_in_about(path)
                self.notify('Configuring')

            if command == 'remove':
                path = self.model.data(event.index, 'path')
                message = path + "\n\n" + "Remove?"
                if self.confirm(message):
                    self.model.remove_workspace(event.index)

        def open_explorer(index):
            path = self.model.data(event.index, 'path')
            pigui.service.open_in_explorer(path)

        def open_about(index):
            path = self.model.data(event.index, 'path')
            pigui.service.open_in_about(path)

        # Handled events
        AddItemEvent = pigui.pyqt5.event.Type.AddItemEvent
        CommandEvent = dash.event.Type.CommandEvent
        OpenInExplorerEvent = dash.event.Type.OpenInExplorerEvent
        OpenInAboutEvent = dash.event.Type.OpenInAboutEvent

        handler = {AddItemEvent: add_item,
                   CommandEvent: command,
                   OpenInExplorerEvent: open_explorer,
                   OpenInAboutEvent: open_about}.get(event.type())

        if handler:
            handler(event.index)

        return super(Dash, self).event(event)

    def status_event(self, message):
        self.notify(message)

    def add_workspace(self, application, index):
        user = getpass.getuser()
        path = self.model.data(index, 'path')

        node = pifou.pom.node.Node.from_str(path)
        workspace = pifou.pom.domain.Workspace.from_node(
            node=node,
            user=user,
            application=application)

        self.model.add_workspace(path=workspace.path.as_str,
                                 index=index)

    def add_workspace_menu(self, index):
        menu = QtWidgets.QMenu(self)

        path = self.model.data(index, 'path')
        location = pifou.om.Location(path)
        entry = pifou.om.Entry('apps', parent=location)
        pifou.om.inherit(entry)

        actions = list()
        if entry.isparent:
            for app in entry:
                actions.append(app.path.name)

        if not actions:
            actions.append('No apps')

        for action in actions:
            action = QtWidgets.QAction(action, self)
            menu.addAction(action)

        action = menu.exec_(QtGui.QCursor.pos())
        if action and action.text() != 'No apps':
            app = action.text()
            self.add_workspace(app, index)


if __name__ == '__main__':
    import pifou
    import pigui
    pifou.setup_log()
    pigui.setup_log()

    import pigui.pyqt5.util

    with pigui.pyqt5.util.application_context():

        model = dash.model.Model()

        win = Dash()
        win.set_model(model)
        win.resize(*dash.settings.WINDOW_SIZE)
        win.animated_show()

        model.setup(r'c:\studio\content')
