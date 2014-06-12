
"""Dashboard-specific items"""

# pifou library
import pifou
import pifou.om
import pifou.signal
import pifou.pom.domain

# pifou dependencies
from PyQt5 import QtWidgets

# pigui library
import pigui.service
import pigui.pyqt5.widgets.item

# local library
import dash.event


class TreeItem(pigui.pyqt5.widgets.item.TreeItem):
    """Append context-menu"""

    def action_event(self, state):
        action = self.sender()
        label = action.text()

        if label == "Open in About":
            event = dash.event.OpenInAboutEvent(index=self.index)
            QtWidgets.QApplication.postEvent(self, event)

        elif label == "Open in Explorer":
            event = dash.event.OpenInExplorerEvent(index=self.index)
            QtWidgets.QApplication.postEvent(self, event)

        elif label == "Hide":
            event = dash.event.HideEvent(index=self.index)
            QtWidgets.QApplication.postEvent(self, event)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)

        for label in ("Open in About",
                      "Open in Explorer",
                      "Hide"):
            action = QtWidgets.QAction(label,
                                       self,
                                       triggered=self.action_event)
            menu.addAction(action)

        menu.exec_(event.globalPos())


class WorkspaceItem(TreeItem):
    @property
    def sort_key(self):
        return '{'


class CommandItem(TreeItem):
    @property
    def sort_key(self):
        return '{'

    # def __init__(self, path, command):
    #     super(CommandItem, self).__init__(path)
    #     self.setText(command)
    #     self.command = command

    def selected_event(self):
        event = dash.event.CommandEvent(index=self.index)
        QtWidgets.QApplication.postEvent(self, event)


def from_path(path):
    # Parse keyword-arguments
    kwargs = list()

    if "?" in path:
        path, args_string = path.rsplit("?")
        args_list = args_string.split("#")

        args = list()
        kwargs = dict()
        for arg in args_list:
            if "=" in arg:
                key, value = arg.split("=")
                kwargs[key] = value
            else:
                args.append(arg)

    # Determine item-type
    item = None

    if 'type' in kwargs:
        typ = kwargs.get('type')

        if typ == 'command':
            command = kwargs.get('command')
            item = CommandItem(path, command)

    if not item:
        if path.endswith('.workspace'):
            item = WorkspaceItem(path)

        elif path.endswith('$command'):
            item = CommandItem(path)

        else:
            item = TreeItem(path)

    return item


if __name__ == '__main__':
    import pifou.pom.node
    import pigui.pyqt5.util

    # register()

    with pigui.pyqt5.util.application_context():
        path = r'S:\content\jobs\skydivers'
        node = pifou.pom.node.Node.from_str(path)
        # item = pigui.pyqt5.widgets.item.Item.from_node(node)
        item = TreeItem(node.path.as_str)

        # for child in item:
            # pass

        item.show()
