"""Dash business logic"""

from __future__ import absolute_import

# Python standard library
import os
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
import pifou.com.source
import pifou.com.pyzmq.rpc


@pifou.lib.log
@pifou.com.pyzmq.rpc.object_as_a_service(name='Dash', port=21001)
class Dash(object):
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

        # self.init_widget(widget)

        # Servers initiated via `main()`

    def init_widget(self):
        widget = self.widget()

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

        widget.restore()

        self.widget = widget

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
        print "Dash launching"
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
            (only valid when running Dash without a console)

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