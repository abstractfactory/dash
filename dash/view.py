import dash.item
import pigui.pyqt5.widgets.list.view

DefaultList = pigui.pyqt5.widgets.list.view.DefaultList


def create_item(self, label, index, parent=None):
    model_item = self.model.item(index)

    args, kwargs = model_item.options

    if 'workspace' in args:
        item = dash.item.WorkspaceItem(label, index, parent)
        model_item.set_data(role='type', value='workspace')
        return item

    if 'command' in kwargs:
        command = kwargs.get('command')
        item = dash.item.CommandItem(command, index, parent)
        model_item.set_data(role='type', value='command')
        model_item.set_data(role='command', value=command)
        return item

    item = dash.item.TreeItem(label, index, parent)
    return item


def monkey_patch():
    """The alteration is minimal enough for
    a monkey-patch to suffice"""
    DefaultList.create_item = create_item
