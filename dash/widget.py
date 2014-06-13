from __future__ import absolute_import

import getpass

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
import dash.item
import dash.view
import dash.model
import dash.settings

pigui.style.register('dash')

dash.view.monkey_path()


class Dash(pigui.pyqt5.widgets.application.widget.ApplicationBase):
    """Dash view"""

    launch = QtCore.pyqtSignal(str)  # index
    remove = QtCore.pyqtSignal(str)  # index
    add_workspace = QtCore.pyqtSignal(str)  # index
    _restore = QtCore.pyqtSignal()  # Restore UI from tray

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

        self._restore.connect(self.restore)

    def set_model(self, model):
        self.view.set_model(model)
        self.model = model

    # def setup(self, uri):
    #     self.model.setup(uri)

    def event(self, event):
        type = event.type()

        if type == dash.event.Type.OpenInExplorerEvent:
            item = self.model.item(event.index)
            pigui.service.open_in_explorer(item.path)

        elif type == pigui.pyqt5.event.Type.AddItemEvent:
            self.new_workspace_menu(event.index)

        elif type == dash.event.Type.CommandEvent:
            item = self.model.item(event.index)
            args, kwargs = item.options
            command = kwargs.get('command')

            if command == 'launch':
                if self.confirm("{}\n\nLaunch?".format(item.path)):
                    self.launch.emit(event.index)

            if command == 'configure':
                pass

            if command == 'remove':
                if self.confirm("{}\n\nRemove?".format(item.path)):
                    self.remove.emit(event.index)

        return super(Dash, self).event(event)

    def new_workspace_menu(self, index):
        menu = QtWidgets.QMenu(self)

        # Temporarily hard-coded, until Content Object Model*
        for app in ('maya2014-x64', 'nuke-8.0', 'ae-cc', 'zbrush-r6'):
            action = QtWidgets.QAction(app, self)
            menu.addAction(action)

        if not True:
            action = QtWidgets.QAction('None available', self)
            menu.addAction(action)

        action = menu.exec_(QtGui.QCursor.pos())
        if action:
            app = action.text()

            item = self.model.item(index)
            item.set_data(role='user', value=getpass.getuser())
            item.set_data(role='app', value=app)
            self.add_workspace.emit(index)

    def restore(self):
        """Restore window"""
        self.raise_()
        self.activateWindow()
        self.showNormal()

        if not self.isVisible():
            self.animated_show()


if __name__ == '__main__':
    import pigui.pyqt5.util

    with pigui.pyqt5.util.application_context():
        win = Dash()

        # win.setup(uri=r'disk:c:\studio\content')
        win.resize(*dash.settings.WINDOW_SIZE)
        win.show()
