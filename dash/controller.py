"""Dash, software-configuration for artists

Usage:
    This controller is designed to work together with application.py
    which provides higher-level logic such as actially running software.

    application.py is listening on Dash.launch which emits a plain-path

"""

from __future__ import absolute_import

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
    """Dash Controller

    Signals:
        launch (str): Emits plain-path of workspace to launch.

    """

    launch = QtCore.pyqtSignal(str)  # index

    def __init__(self, parent=None):
        """
        Arguments:
            parent (QtWidgets.QWidget): Qt parent of this widget

        """

        super(Dash, self).__init__(parent)
        self.setWindowTitle("Dash")

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
        """Set model for this controller

        Arguments:
            model (pifou.pyqt5.model.Model): Target model

        """

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
            """Footer has been pressed

            Arguments:
                index (str): Index of footer which was pressed

            """

            if self.model.data(index, 'type') == pigui.pyqt5.model.Footer:
                index = self.model.item(index).parent.index

            if self.model.data(index, 'type') == 'workspace':
                # Workspaces only list commands. Clicking the
                # footer within this list shouldn't do anything.
                # TODO: Remove footer from command-lists.
                return

            self.add_workspace_menu(index)

        def command(index):
            """A command delegate was pressed

            Arguments:
                index (str): Index of command

            """

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

        def rename(index):
            label = self.model.data(index=event.index, key='display')
            edited = event.view.indexes[event.index]
            editor = pigui.pyqt5.widgets.delegate.RenamerDelegate(
                label,
                index=event.index,
                parent=edited)

            # Overlap edited
            editor.resize(edited.size())
            editor.show()

        def renamed(index):
            name = event.data
            self.model.set_data(index=event.index,
                                key=pigui.pyqt5.model.Display,
                                value=name)

        def open_explorer(index):
            """Open `index` in file-system explorer

            Arguments:
                index (str): Index to open

            """

            path = self.model.data(event.index, 'path')
            pigui.service.open_in_explorer(path)

        def open_about(index):
            """Open `index` in About

            Arguments:
                index (str): Index to open

            """

            path = self.model.data(event.index, 'path')
            pigui.service.open_in_about(path)

        # Handled events
        AddItemEvent = pigui.pyqt5.event.Type.AddItemEvent
        CommandEvent = dash.event.Type.CommandEvent
        OpenInExplorerEvent = dash.event.Type.OpenInExplorerEvent
        OpenInAboutEvent = dash.event.Type.OpenInAboutEvent
        EditItemEvent = pigui.pyqt5.event.Type.EditItemEvent
        ItemRenamedEvent = pigui.pyqt5.event.Type.ItemRenamedEvent

        handler = {AddItemEvent: add_item,
                   CommandEvent: command,
                   OpenInExplorerEvent: open_explorer,
                   OpenInAboutEvent: open_about,
                   EditItemEvent: rename,
                   ItemRenamedEvent: renamed}.get(event.type())

        if handler:
            handler(event.index)

        return super(Dash, self).event(event)

    def status_event(self, message):
        """Notify user of events from model

        Arguments:
            message (str): Short message for user

        """

        self.notify(message)

    def error_event(self, exception):
        message = str(exception)
        self.notify(message)

    def add_workspace(self, application, index):
        """Add `application` to `index`

        Arguments:
            application (str): Name of application to add
            index (str): Parent of new workspace

        """

        path = self.model.data(index, 'path')

        self.model.add_workspace(root=path,
                                 application=application,
                                 parent=index)

    def add_workspace_menu(self, index):
        """Open menu with possible workspaces for `index`

        Arguments:
            index (str): Source index for available workspaces

        """

        menu = QtWidgets.QMenu(self)

        path = self.model.data(index, 'path')
        assert path, self.model.item(index)._data
        location = pifou.metadata.Location(path)
        entry = pifou.metadata.Entry('apps', parent=location)
        pifou.metadata.inherit(entry)

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
