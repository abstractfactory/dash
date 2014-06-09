import os
import subprocess

import pifou.lib
import dash.widget


class Dash(object):
    def __init__(self):
        self.user = None
        self.widget = None

    def setup_widget(self, widget):
        widget.launch.connect(self.launch_event)
        self.widget = widget

    def launch_event(self, path):
        """Launch `path`

        `path` points to a live workspace.

        1. Parse workspace
        2. Find app
        3. Find args, kwargs and environment
        4. Run app

        """

        basename = os.path.basename(path)
        app, _ = os.path.splitext(basename)

        binary = pifou.lib.where(app)
        if not binary:
            return False

        print "running %s" % binary
        subprocess.Popen(binary)

if __name__ == '__main__':
    import pigui.pyqt5.util

    with pigui.pyqt5.util.application_context():
        win = dash.widget.Dash()

        application = Dash()
        application.setup_widget(win)

        win.setup('/c/studio/content')
        win.resize(*dash.settings.WINDOW_SIZE)
        win.show()
