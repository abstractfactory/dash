
# standard library
import os
import getpass
import subprocess

# pifou library
import pifou.lib
import pifou.pom.node
import pifou.pom.domain

import pifou.com.util
import pifou.com.source

# local library
import dash.model
import dash.controller

# pifou dependency
import zmq
context = zmq.Context.instance()


class Dash(object):
    """Dash controller"""

    def __init__(self):
        self.model = None
        self.controller = None

    def set_controller(self, controller):
        self.controller = controller
        controller.launch.connect(self.launch_event)

    def set_model(self, model):
        self.model = model

        if self.controller:
            self.controller.set_model(model)

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


if __name__ == '__main__':
    import pigui.pyqt5.util

    with pigui.pyqt5.util.application_context():
        win = dash.controller.Dash()

        model = dash.model.Model()

        app = Dash()
        app.set_controller(win)
        app.set_model(model)

        model.setup('c:\studio\content')

        win.resize(*dash.settings.WINDOW_SIZE)
        win.show()
