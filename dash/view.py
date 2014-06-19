import dash.delegate
import pigui.pyqt5.widgets.list.view

import pigui.pyqt5.model

DefaultList = pigui.pyqt5.widgets.list.view.DefaultList


def create_delegate(self, index):
    typ = self.model.data(index, 'type')

    if typ == 'disk':
        label = self.model.data(index, 'display')
        if self.model.data(index, key='group'):
            return dash.delegate.FolderDelegate(label, index)
        else:
            return dash.delegate.FileDelegate(label, index)

    if typ == 'workspace':
        label = self.model.data(index, 'display')
        return dash.delegate.WorkspaceDelegate(label, index)

    if typ == 'command':
        label = self.model.data(index, 'command')
        return dash.delegate.CommandDelegate(label, index)

    else:
        return super(DefaultList, self).create_delegate(index)


def monkey_patch():
    """The alteration is minimal enough for
    a monkey-patch to suffice"""
    DefaultList.create_delegate = create_delegate
