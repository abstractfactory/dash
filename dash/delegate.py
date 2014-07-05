
"""Dashboard-specific delegates"""

# pifou library
import pifou
import pifou.metadata
import pifou.signal

# pifou dependencies
from PyQt5 import QtWidgets

# pigui library
import pigui.service
import pigui.pyqt5.widgets.delegate

# local library
import dash.event


class FolderDelegate(pigui.pyqt5.widgets.delegate.FolderDelegate):
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


class FileDelegate(pigui.pyqt5.widgets.delegate.FileDelegate):
    pass


class WorkspaceDelegate(FolderDelegate):
    pass


class CommandDelegate(FolderDelegate):
    pass

    def selected_event(self):
        event = pigui.pyqt5.event.CommandEvent(index=self.index)
        QtWidgets.QApplication.postEvent(self, event)


if __name__ == '__main__':
    import pigui.pyqt5.util

    # register()

    with pigui.pyqt5.util.application_context():
        path = r'S:\content\jobs\skydivers'
        delegate = FolderDelegate(path, index='hello')

        delegate.show()
