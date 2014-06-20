
from __future__ import absolute_import

# pipi library
import pifou
import pigui

# local library
import dash.controller
import dash.application

pifou.setup_log()
pigui.setup_log()


def main(path):
    import pigui.pyqt5.util

    with pigui.pyqt5.util.application_context():
        win = dash.controller.Dash()
        app = dash.application.Dash()

        model = dash.model.Model()

        app.set_controller(win)
        app.set_model(model)

        model.setup(path)

        win.resize(*dash.settings.WINDOW_SIZE)
        win.animated_show()


if __name__ == '__main__':
    import os
    main(os.path.expanduser('~'))
