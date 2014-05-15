
from __future__ import absolute_import

# Python standard library
import threading

# pifou library
import pifou
import pifou.com.error

# pigui library
import pigui
import pigui.item

# local library
import dash.widget
import dash.process
import dash.application

# Loggers
pifou.setup_log()
pigui.setup_log()


def get_root():
    root = pifou.pi.ROOT

    if not root:
        raise pifou.error.Root

    return root


def register_dash(app):
    def task():
        try:
            app.init_service()
        except pifou.com.error.Timeout:
            print ("Couldn't register with nameserver."
                   "Is it running?")

    thread = threading.Thread(target=task)
    thread.dameon = True
    thread.start()


def request_application(path):
    """Look for existing instance of Dashboard"""
    print "I: Requesting a new Widget"

    # Try default address
    service = pifou.com.pyzmq.rpc.ProxyService.from_url(
        'tcp://127.0.0.1:21001')

    try:
        service.wakeup()
        print "I: Successfully restored existing instance of Dashboard"
    except pifou.com.error.Timeout:
        print "W: An existing dash could not be found"
        print "I: Running new instance of Dashboard"
        main(path)


def main(path, debug=False):
    import pigui.util.pyqt5

    node = pifou.pom.node.Node.from_str(path)
    user = pifou.pi.CURRENT_USER

    process = dash.process

    node.children.postprocess.add(process.post_hide_hidden)
    node.children.preprocess.add(process.pre_junction)

    widget = dash.widget.Dash
    app = dash.application.Dash(widget)

    with pigui.util.pyqt5.app_context(use_baked_css=False):
        app.init_widget()
        app.load(node)
        app.user = user

        if debug:
            def closeEvent(event):
                app.widget.remove_tray()
            app.widget.closeEvent = closeEvent
        else:
            register_dash(app)


if __name__ == '__main__':
    path = get_root()
    # main(path, debug=True)
    request_application(path)
