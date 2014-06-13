
# standard library
import os
import subprocess

# pifou library
import pifou.lib
import pifou.pom.node
import pifou.pom.domain

import pifou.com.util
import pifou.com.source

# local library
import dash.model
import dash.widget

# pifou dependency
import zmq
context = zmq.Context.instance()


class Dash(object):
    """Dash controller"""

    def __init__(self):
        self.model = None
        self.widget = None

        self.rep = context.socket(zmq.REP)
        pifou.lib.spawn(self.listen)

    def listen(self):
        endpoint = "tcp://{host}:5555"
        print "Listening on {}".format(
            endpoint.format(host=pifou.com.util.local_ip()))
        self.rep.bind(endpoint.format(host='*'))

        while True:
            message = self.rep.recv_json()
            if 'restore' in message:
                self.widget._restore.emit()
            self.rep.send_json({'status': 'ok'})

    def set_widget(self, widget):
        self.widget = widget

        widget.launch.connect(self.launch_event)
        widget.add_workspace.connect(self.add_workspace_event)

    def set_model(self, model):
        self.model = model

        if self.widget:
            self.widget.set_model(model)

    def launch_event(self, index):
        """Launch `path`

        `path` points to a live workspace.

        1. Parse workspace
        2. Find app
        3. Find args, kwargs and environment
        4. Run app

        """

        item = self.model.item(index)
        path = item.path

        basename = os.path.basename(path)
        app, _ = os.path.splitext(basename)

        exe = pifou.lib.where(app)
        if not exe:
            print "{} could not be found".format(app)
            return False

        print "running %s" % exe
        subprocess.Popen(exe)

    def add_workspace_event(self, index):
        """Add `app` to `user` under `path`

        `path` points to the directory under which a workspace
        is to be instantiated.

        """

        item = self.model.item(index)

        path = item.path
        user = item.data('user')
        app = item.data('app')

        # print "Adding %s to %s, for %s" % (app, path, user)
        parent = pifou.pom.node.Node.from_str(path)
        workspace = pifou.pom.domain.Workspace.from_node(
            node=parent,
            user=user,
            application=app)

        uri = 'disk:{}?workspace'.format(workspace.path.as_str)
        self.model.add_item(uri=uri,
                            parent=item)


if __name__ == '__main__':
    import pigui.pyqt5.util

    with pigui.pyqt5.util.application_context():
        win = dash.widget.Dash()

        model = dash.model.Model()

        app = Dash()
        app.set_widget(win)
        app.set_model(model)

        model.setup(uri=r'disk:c:\studio\content')

        win.resize(*dash.settings.WINDOW_SIZE)
        win.show()
