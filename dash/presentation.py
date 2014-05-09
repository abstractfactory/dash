
from __future__ import absolute_import

# Python standard library
import os
import logging
import functools
import threading
import subprocess

import openmetadata as om

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
class Widget(pigui.widgets.pyqt5.application.ApplicationBase):
    """Graphical layer of Dashboard

    Events
        quitted         -- `Widget` requests shutdown

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
        super(Widget, self).__init__(parent)
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
            header = super(Widget, self).findChild(QtWidgets.QWidget, 'Header')
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

        # Add to container of ApplicationBase.
        # We could use `self`, but calling the
        # superclass makes it more explicit.
        container = super(Widget, self).findChild(
            QtWidgets.QWidget, 'Container')

        # setup_menu()
        setup_header()
        body = setup_body()

        layout = container.layout()
        layout.addWidget(body)

        # Let the RPC know about the method .show()
        self.wakeup.connect(self.restore)

        self.resize(*Widget.WINDOW_SIZE)
        self.setMinimumSize(*Widget.WINDOW_MINIMUM_SIZE)

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
        miller = self.findChild(QtWidgets.QWidget, 'MillerView')
        miller.load(node)

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
        """Window fades out and closes by default (as per Widget impl)"""
        tray = self.findChild(QtWidgets.QSystemTrayIcon, 'Tray')
        if tray.isVisible():
            self.animated_hide()
            event.ignore()

            if not self.property('userKnows'):
                tray.showMessage('Information', 'Dashboard is still running!')
            self.setProperty('userKnows', True)
        else:
            super(Widget, self).closeEvent(event)


@pifou.lib.log
@pifou.com.pyzmq.rpc.object_as_a_service(name='Dashboard', port=21001)
class Application(object):
    """
    Events
        removed(node)     -- `node` has been physically removed
        refreshed(node)   -- `node` has been modified

    Requests
        loaded(node)      -- `node` requests to be loaded

    """

    def __init__(self, widget):
        self.user = None
        self.widget = widget
        self._threads = []

        self.loaded = pifou.signal.Signal(node=object)
        self.added = pifou.signal.Signal(node=object)
        self.removed = pifou.signal.Signal(node=object)

        self.init_widget(widget)

        # Servers initiated via `start_application()`

    def init_widget(self, widget):
        self.added.connect(widget.added_event)
        self.loaded.connect(widget.loaded_event)

        # Requests
        widget.launch.connect(self.launch)
        widget.remove.connect(self.remove)
        widget.add_workspace.connect(self.add_workspace)

        # Events
        widget.quitted.connect(self.quit_event)
        widget.get_available_applications.connect(
            self.get_available_applications)

    def add_workspace(self, application, parent):

        workspace = pifou.pom.domain.Workspace.from_node(
            node=parent,
            application=application)

        if pifou.api.exists(workspace):
            raise pifou.error.Exists('%s already exists' % workspace.path.name)

        node = parent.copy(path=workspace.path)

        if pifou.api.create(workspace):
            self.added.emit(node=node, parent=parent)
            return True

        # # Hide development
        # # development_node = item.node + 'development'
        # # development_node.setdata('dash', 'hidden', True)

    def get_available_applications(self, node):
        entity = pifou.pom.domain.Entity.from_node(node)

        apps = []
        for app in entity.appdata:
            app.setdata('parent', node)
            apps.append(app)

        return apps

    def remove(self, node):
        return pifou.api.remove(node)

    def quit_event(self):
        print "Quitting.."
        # self.widget.close()

    def load(self, node):
        self.loaded.emit(node=node)

    def launch(self, workspace):
        """Run application associated with `item`"""
        print "Application launching"
        application_key = workspace.url.path.name

        application = None
        for app in pifou.pom.domain.yield_applications(workspace):
            if app.key == application_key:
                application = app

        if not application:
            return False

        # Resolve key, e.g. 'maya' into absolute path
        command = pifou.lib.where(application_key)
        if not command:
            return False

        args = om.read(application.path.as_str, 'args') or []
        kwargs = om.read(application.path.as_str, 'kwargs') or []

        for key in kwargs:
            value = om.read(application.path.as_str, 'kwargs/%s' % key)
            if value:
                command += " %s %s" % (key, value)

        for arg in args:
            command += ' ' + arg

        # Resolve keywords, e.g. $WORKSPACE into absolute path
        words = []
        for word in command.split():
            word = word.replace('$WORKSPACE',
                                workspace.url.path.as_str)
            word = word.replace('$APPLICATION',
                                application.path.as_str)
            words.append(word)

        # Rebuild command with arguments
        command = ' '.join(words)

        # Set environment variables
        variables = {}
        environment = om.read(application.path.as_str, 'environment') or []
        for key in environment:
            value = om.read(application.path.as_str, 'environment/%s' % key)
            if value:
                value = value.replace('$APPLICATION',
                                      application.path.as_str)
                variables[key] = value

        modified_environment = os.environ.copy()

        # TODO: Once we've implemented proper list support in
        # Open Metadata, this can become neater.
        separator = ';' if os.name == 'nt' else ':'

        for key, value in variables.iteritems():
            existing_value = modified_environment.get(key)

            if existing_value:
                value = separator.join([existing_value, value])

            modified_environment[str(key)] = str(value)
            print "Adding env variable: %s=%s" % (key, value)

        print "Running %s" % command

        def task(command):
            """
            Run `command` without console.
            (only valid when running Dashboard without a console)

            """

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            return subprocess.Popen(command,
                                    env=modified_environment,
                                    startupinfo=startupinfo)

        thread = threading.Thread(args=(command,), target=task)
        thread.dameon = True
        thread.start()

        # This is how we'll keep tabs on what's running
        self._threads.append(thread)

        self.widget.notify(title='Info',
                           message='Running %s..' % application_key)

        return True

    @pifou.com.pyzmq.rpc.slot
    def wakeup(self):
        """Forward call to Widget which will restore the window"""
        self.widget.wakeup.emit()


# ---------------------------------------------------------------- #


def get_application():
    root_path = pifou.pi.ROOT

    if not root_path:
        raise pifou.error.Root

    node = pifou.pom.node.Node.from_str(root_path)
    item = pigui.item.Item.from_node(node)

    # ---------- Register node-process ------------- #

    user = pifou.pi.CURRENT_USER

    process = dash.process
    process.USER = user

    node.children.postprocess.add(process.post_hide_hidden)
    node.children.preprocess.add(process.pre_junction)

    # print "Loading %s" % node

    # ------------- Instantiate widget ---------------------- #

    widget = Widget()
    application = Application(widget)
    application.load(item)
    application.user = user

    return application


def start_application(debug=False):
    import pigui.util.pyqt5
    pigui.style.register('dash')
    log = logging.getLogger('dash.presentation.request_application')

    with pigui.util.pyqt5.app_context(use_baked_css=False):
        application = get_application()

        if debug:
            def closeEvent(event):
                application.widget.remove_tray()
            application.widget.closeEvent = closeEvent
        else:
            def task():
                # Initialise providers here to facilitate for
                # start_debug which isn't supposed to run any
                # servers.
                try:
                    application.init_service()
                except pifou.com.error.Timeout:
                    log.warning("Couldn't register with nameserver."
                                "Is it running?")

            thread = threading.Thread(target=task)
            thread.dameon = True
            thread.start()

        application.widget.restore()


def request_application():
    """Look for existing instance of Dashboard"""
    from pifou.com import error

    log = logging.getLogger('dash.presentation.request_application')
    log.info("Requesting a new Widget")

    # Try default address
    service = pifou.com.pyzmq.rpc.ProxyService.from_url(
        'tcp://127.0.0.1:21001')

    try:
        service.wakeup()
        log.info("Successfully restored existing instance of Dashboard")
    except error.Timeout:
        log.debug("An existing dash could not be found")
        log.info("Running new instance of Dashboard")
        start_application()


if __name__ == '__main__':
    start_application(debug=True)
    # request_application()
