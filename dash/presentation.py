
from __future__ import absolute_import

# pifou library
import pifou
import pifou.com.error

# pigui library
import pigui

# local library
import dash.widget
import dash.application

# pifou dependency
import zmq

# Loggers
pifou.setup_log()
pigui.setup_log()


def get_root():
    root = pifou.pi.ROOT

    if not root:
        raise pifou.error.Root

    return root


def request_application():
    """Look for existing instance of Dashboard"""
    print "I: Requesting a new Widget"

    # Try default address
    context = zmq.Context.instance()
    query = context.socket(zmq.REQ)
    query.connect("tcp://127.0.0.1:5555")
    query.send_json({'restore': True})

    poll = zmq.Poller()
    poll.register(query, zmq.POLLIN)

    sockets = poll.poll(timeout=200)
    if query in dict(sockets):
        message = query.recv_json()
        if message.get('status') == 'ok':
            return True
    else:
        poll.unregister(query)
        query.close()
        return False


def main(path):
    import pigui.pyqt5.util

    if not request_application():
        with pigui.pyqt5.util.application_context():
            win = dash.widget.Dash()

            model = dash.model.Model()

            app = dash.application.Dash()
            app.set_widget(win)
            app.set_model(model)

            model.setup(uri='disk:' + path)

            win.resize(*dash.settings.WINDOW_SIZE)
            win.show()


if __name__ == '__main__':
    path = get_root()
    main(path)
