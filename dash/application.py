
# standard library
import os
import subprocess

# pifou library
import pifou.lib
import pifou.metadata

# local library
import dash.model
import dash.controller


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

        path = self.model.data(index, 'path')
        self.launch_path(path)

    def launch_path(self, path):
        basename = os.path.basename(path)
        application, _ = os.path.splitext(basename)

        cmd = list()

        exe = pifou.lib.where(application)
        if not exe:
            print "{} could not be found".format(application)
            return False

        cmd.append(exe)

        location = pifou.metadata.Location(path)

        # Get arguments
        args = pifou.metadata.Entry("apps/" + application + "/args",
                                    parent=location)
        pifou.metadata.inherit(args)

        for arg in args:
            pifou.metadata.pull(arg)
            cmd.append(arg.path.name)

        # Get keyword arguments
        args = pifou.metadata.Entry("apps/" + application + "/kwargs",
                                    parent=location)
        pifou.metadata.inherit(args)

        for arg in args:
            pifou.metadata.pull(arg)
            cmd.append(arg.path.name)
            cmd.append(arg.value)

        # Resolve keywords
        keywords = {
            '$workspace': path,
        }

        for part in cmd:
            part = part.lower()

            try:
                keyword = keywords[part]
                index = cmd.index(part)
                cmd[index] = keyword

            except KeyError:
                pass

        print "Running %s" % cmd
        subprocess.Popen(cmd)

    def kwargs_from_workspace(self, root, application):
        """Fetch keyword arguments from `root` for `application`

        Arguments:
            root (str): Absolute path to workspace

        """

        raise NotImplemented

    def args_from_workspace(self, root, application):
        """Fetch arguments from `root` for `application`

        Arguments:
            root (str): Absolute path to workspace

        """

        raise NotImplemented

    def environment_from_workspace(self, root, application):
        """Fetch environment settings from `root` for `application`

        Arguments:
            root (str): Absolute path to workspace

        """

        raise NotImplemented


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
        win.animated_show()
