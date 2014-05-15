"""Dash graphical user interface"""

from __future__ import absolute_import

# Python standard library
import functools

# pifou library
import pifou
import pifou.pi
import pifou.api
import pifou.lib
import pifou.error
import pifou.signal
import pifou.pom.node
import pifou.pom.domain
import pifou.com.pyzmq.rpc

# pigui library
import pigui
import pigui.style
import pigui.item
import pigui.widgets.pyqt5.application

# pigui dependencies
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets

# local modules
import dash.process

# Loggers
pifou.setup_log()
pigui.setup_log()

# ------------------------- Extensions --------------------------- #

# Add support for Dashboard items
# Note: This replaces the default item for `Node` without suffix.
import dash.item
dash.item.register()

# Add support for the Dashboard `List`
import dash.view
dash.view.register()

# Add support for Option items
# import pigui.widgets.pyqt5.optionitem
# pigui.widgets.pyqt5.optionitem.register()

pigui.style.register('dash')


@pifou.lib.log
class Dash(pigui.widgets.pyqt5.application.Base):
    """Graphical layer of Dashboard

    Events
        quitted         -- `Dash` requests shutdown

    Requests
        remove          -- `node` requests to be removed
        launch          -- `node` requests to be launched
        add_workspace   -- Add `workspace`

    """

    # Triggered remotely to wake-up this widget.
    # I.e.
    #   1. To restore from tray.
    #   2. To restore existing Dashboard when attempting to run a new
    wakeup = QtCore.pyqtSignal()

    WINDOW_SIZE = (700, 400)  # w/h
    WINDOW_POSITION = None
    WINDOW_MINIMUM_SIZE = (400, 300)
    MARGIN = 7  # px
    SPACING = 5  # px

    def __init__(self, parent=None):
        super(Dash, self).__init__(parent)
        self.setWindowTitle('Pipi Dashboard')

        # Events
        self.quitted = pifou.signal.Signal()

        # Requests
        self.remove = pifou.signal.Request(node=object)
        self.launch = pifou.signal.Request(workspace=object)
        self.get_available_applications = pifou.signal.Request(node=object)
        self.add_workspace = pifou.signal.Request(parent=object,
                                                  application=object)

        def setup_header():
            header = super(Dash, self).findChild(QtWidgets.QWidget, 'Header')
            close_button = header.findChild(QtWidgets.QWidget, 'CloseButton')
            close_button.released.disconnect()
            close_button.released.connect(self.close)

        def setup_body():
            body = QtWidgets.QWidget()

            miller = pigui.widgets.pyqt5.miller.view.DefaultMiller()
            placeholder_slot = lambda x: self.notify(title="Oops..", message=x)

            miller.error.connect(placeholder_slot)
            miller.message.connect(self.notify)
            miller.event.connect(self.event_handler)

            layout = QtWidgets.QHBoxLayout(body)
            layout.addWidget(miller)
            layout.setContentsMargins(self.MARGIN, 0,
                                      self.MARGIN, self.MARGIN)

            for __widget, __name in {
                    body:           'Body',
                    miller:     'MillerView'
                    }.iteritems():
                __widget.setObjectName(__name)

            return body

        # Add to container of Base.
        # We could use `self`, but calling the
        # superclass makes it more explicit.
        container = super(Dash, self).findChild(
            QtWidgets.QWidget, 'Container')

        # setup_menu()
        setup_header()
        body = setup_body()

        layout = container.layout()
        layout.addWidget(body)

        # Let the RPC know about the method .show()
        self.wakeup.connect(self.restore)

        self.resize(*Dash.WINDOW_SIZE)
        self.setMinimumSize(*Dash.WINDOW_MINIMUM_SIZE)

        self.setup_tray()

    def event_handler(self, name, data):
        """
        Process events coming up from within the
        hierarchy of widgets.
                          _______________
                         |               |
                         |     Event     |
                         |_______________|
                                 |
                          _______v_______
                         |               |
                         |    Handler    |
                         |_______________|
                                 |
                 ________________|_______________
                |                |               |
         _______v______   _______v______   ______v_______
        |              | |              | |              |
        |   Response   | |   Response   | |   Response   |
        |______________| |______________| |______________|

        """

        #  _____________
        # |             |
        # |   Command   |
        # |_____________|
        #
        if name == 'command':
            item = data[0]
            subject = item.data.get('subject')
            # listwidget = subject.data.get('__views__')[0]

            command = item.data.get('command')

            #  ____________
            # |            |
            # |   Launch   |
            # |____________|
            #
            if command == 'launch':
                workspace = subject.node

                if self.confirm('Launching %s' %
                                workspace.url.path.name,
                                'Continue?'):
                    ret = self.launch(workspace=workspace)

                    if ret is None:
                        self.confirm('Warning', 'This is a bug')

                    if ret is False:
                        title = 'Alert'
                        message = '"%s" not available on this system'
                        message %= pifou.api.getpath(workspace).name
                        self.notify(title, message)

            #  ____________
            # |            |
            # |   Remove   |
            # |____________|
            #
            if command == 'remove':
                node = subject.node

                # Confirm operation
                if self.confirm('Removing workspace', 'Continue?'):
                    if not self.remove(node=node):
                        self.notify('Oops', 'Could not remove %s' %
                                    node.url.path.name)
                    else:
                        # listwidget.remove_item(subject)
                        self.notify('Success', 'Successfully removed %s'
                                    % node.url.path.name)

        #  _____________
        # |             |
        # |     New     |
        # |_____________|
        #
        if name == 'new':
            item, listwidget = data[:2]
            item = item.data.get('parent')
            node = item.node
            apps = self.get_available_applications(node=node) or []
            self.new_workspace_menu(parent=item, apps=apps)

    def new_workspace_menu(self, parent, apps):
        """
         _______________
        |    workspace1 |
        |---------------|
        |    workspace2 |
        |---------------|
        |    ....       |
        |---------------|
        |               |
        |---------------|
        |               |
        |_______________|

        """

        menu = QtWidgets.QMenu(self)

        for app in apps:
            def request(parent, app):
                try:
                    self.add_workspace(
                        parent=parent.node,
                        application=app)

                except pifou.error.Exists:
                    self.notify('Already exists',
                                '%s already exists' % app.path.name)

            # Perform magic voodoo-dance to work with QAction.
            add_workspace = functools.partial(request, parent, app)

            name = app.node.url.path.name
            action = QtWidgets.QAction(name,
                                       self,
                                       triggered=add_workspace)
            menu.addAction(action)

        if not apps:
            action = QtWidgets.QAction('None available', self)
            menu.addAction(action)

        menu.exec_(QtGui.QCursor.pos())

    def added_event(self, node, parent):
        """`node` was added"""
        assert isinstance(node, pifou.pom.node.Node)

        parent_path = pifou.api.getpath(parent)
        miller = self.findChild(QtWidgets.QWidget, 'MillerView')
        column = miller.find_column(parent_path.as_str)

        assert column, "No column was found"

        item = pigui.item.Item.from_node(node)
        column.add_item(item)

        self.notify('Added', "Added %s %r to %s" % (
                    item.type, item.name, parent_path.name))

    def loaded_event(self, node):
        item = pigui.item.Item.from_node(node)
        miller = self.findChild(QtWidgets.QWidget, 'MillerView')
        miller.load(item)

    def setup_tray(self):
        tray = QtWidgets.QSystemTrayIcon(self)
        tray.setIcon(QtGui.QIcon('icon_dash_16x16'))

        tray.activated.connect(self.tray_activated_event)

        restore = QtWidgets.QAction('&Restore', self, triggered=self.restore)
        quit_ = QtWidgets.QAction('&Quit', self, triggered=self.quit)

        menu = QtWidgets.QMenu(self)
        for action in (restore, quit_):
            menu.addAction(action)

        tray.setContextMenu(menu)
        tray.setObjectName('Tray')
        tray.show()

    def remove_tray(self):
        tray = self.findChild(QtWidgets.QSystemTrayIcon, 'Tray')
        if tray:
            tray.hide()

    def tray_activated_event(self, reason):
        """Tray icon was clicked"""
        if reason != QtWidgets.QSystemTrayIcon.Trigger:
            return

        if self.isVisible():
            return self.raise_()

        self.restore()

    def restore(self):
        """Restore window"""
        self.raise_()
        self.activateWindow()
        self.showNormal()
        self.animated_show()

    def quit(self):
        """Right-clicking on tray-icon and quitting permanently"""
        self.log.info("Removing tray icon")
        tray = self.findChild(QtWidgets.QSystemTrayIcon, 'Tray')
        tray.hide()

        self.log.info("Quitting Dashboard")
        animation = self.window_fade_out()
        animation.finished.connect(QtWidgets.QApplication.instance().quit)

        self.close()
        self.quitted.emit()

    def closeEvent(self, event):
        """Window fades out and closes by default (as per Dash impl)"""
        tray = self.findChild(QtWidgets.QSystemTrayIcon, 'Tray')
        if tray.isVisible():
            self.animated_hide()
            event.ignore()

            if not self.property('userKnows'):
                tray.showMessage('Information', 'Dashboard is still running!')
            self.setProperty('userKnows', True)
        else:
            super(Dash, self).closeEvent(event)


