
"""Dashboard-specific items"""

import openmetadata as om

# pifou library
import pifou
import pifou.signal
import pifou.pom.domain

# pifou dependencies
from PyQt5 import QtWidgets
# from PyQt5 import QtCore

# pigui library
import pigui.item
import pigui.service
import pigui.widgets.pyqt5.item


@pifou.lib.Process.cascading
def discard_files(node):
    if node.isparent:
        return node

# ------------------------- Items ---------------------------------- #


class DashboardItem(pigui.widgets.pyqt5.item.TreeItem):
    def __init__(self, *args, **kwargs):
        super(DashboardItem, self).__init__(*args, **kwargs)

        self.node.children.postprocess.add(discard_files)

        self.widget.open_in_about.connect(self.open_in_about)
        self.widget.open_in_explorer.connect(self.open_in_explorer)
        self.widget.hide.connect(self.hide_event)
        # self.widget.setText(self.name)

    def open_in_about(self):
        path = self.node.url.path.as_str
        pigui.service.open_in_about(path)

    def open_in_explorer(self):
        self.data['debug'] = 'explore'
        self.event.emit(name='debug', data=[self])

        path = self.node.url.path.as_str
        pigui.service.open_in_explorer(str(path))

    def hide_event(self):
        path = self.node.url.path.as_str
        om.write(path, 'hidden', None)


class WorkspaceItem(pigui.widgets.pyqt5.item.TreeItem):
    def __init__(self, *args, **kwargs):
        super(WorkspaceItem, self).__init__(*args, **kwargs)
        self.widget.setText(self.name)
        pol = self.sortpolicy
        pol.position = pol.AlwaysOnTop

        self.widget.open_in_about.connect(self.open_in_about)
        self.widget.open_in_explorer.connect(self.open_in_explorer)

        self.__application = None

    def open_in_about(self):
        if self.application:
            path = self.application.path.as_str
            pigui.service.open_in_about(path)

    def open_in_explorer(self):
        if self.application:
            path = self.application.path.as_str
            pigui.service.open_in_explorer(path)

    @property
    def application(self):
        if not self.__application:
            workspace = self.node
            application_key = workspace.url.path.name

            application = None
            for app in pifou.pom.domain.yield_applications(workspace):
                if app.key == application_key:
                    application = app

            self.__application = application

        return self.__application


class AppItem(pigui.widgets.pyqt5.item.TreeItem):
    pass


class AppWidget(pigui.widgets.pyqt5.item.ItemWidget):
    pass

# --------------------- Widgets -------------------------- #


class DashboardWidget(pigui.widgets.pyqt5.item.TreeWidget):
    def __init__(self, *args, **kwargs):
        super(DashboardWidget, self).__init__(*args, **kwargs)

        self.open_in_about_action = None
        self.open_in_explorer_action = None
        self.hide_action = None

        # Signals
        self.open_in_about = pifou.signal.Signal()
        self.open_in_explorer = pifou.signal.Signal()
        self.hide = pifou.signal.Signal()

        self.init_actions()

    def init_actions(self):
        # QActions transmit their checked-state, but we won't
        # make use of it in Item. We use lambda to silence that.
        oia_signal = lambda state: self.open_in_about.emit()
        oie_signal = lambda state: self.open_in_explorer.emit()
        hide_signal = lambda state: self.hide.emit()

        oia_action = QtWidgets.QAction("&Open in About", self,
                                       statusTip="Open in About",
                                       triggered=oia_signal)
        oie_action = QtWidgets.QAction("&Open in Explorer", self,
                                       statusTip="Open in Explorer",
                                       triggered=oie_signal)
        hide_action = QtWidgets.QAction("&Hide", self,
                                        statusTip="Hide folder",
                                        triggered=hide_signal)

        self.open_in_explorer_action = oie_action
        self.open_in_about_action = oia_action
        self.hide_action = hide_action

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)

        for action in (self.open_in_about_action,
                       self.open_in_explorer_action,
                       self.hide_action):

            if not action:
                continue

            menu.addAction(action)
        menu.exec_(event.globalPos())


class WorkspaceWidget(DashboardWidget):
    def __init__(self, *args, **kwargs):
        super(WorkspaceWidget, self).__init__(*args, **kwargs)
        self.hide_action = None


# ------------------------- Families ----------------------------- #


class DashboardFamily(object):
    """Replace default item"""
    predicate = None
    ItemClass = DashboardItem
    WidgetClass = DashboardWidget


class WorkspaceFamily(object):
    predicate = 'workspace'
    ItemClass = WorkspaceItem
    WidgetClass = WorkspaceWidget


class AppFamily(object):
    predicate = 'app'
    ItemClass = AppItem
    WidgetClass = AppWidget


def register():
    pigui.item.Item.register(DashboardFamily)
    pigui.item.Item.register(WorkspaceFamily)
    pigui.item.Item.register(AppFamily)
    # print "registry: %s" % pigui.item.Item.registry
    # pigui.item.Item.register(NewWorkspaceFamily)


if __name__ == '__main__':
    # from pifou.pom.node import ConcreteNode
    import pifou.pom.node

    register()

    import pigui.util.pyqt5
    with pigui.util.pyqt5.app_context():
        path = r'S:\content\jobs\skydivers'
        node = pifou.pom.node.Node.from_str(path)
        item = pigui.item.Item.from_node(node)
        
        for child in item:
            pass

        # print [c for c in item]
        # print repr(item)
        item.widget.show()
