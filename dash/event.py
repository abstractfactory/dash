
from pigui.pyqt5.event import BaseEvent, Type


class PathEvent(BaseEvent):
    def __init__(self, path):
        super(PathEvent, self).__init__()
        self.path = path


@Type.register
class OpenInExplorerEvent(PathEvent):
    pass


@Type.register
class OpenInAboutEvent(PathEvent):
    pass


@Type.register
class HideEvent(PathEvent):
    pass


@Type.register
class CommandEvent(PathEvent):
    def __init__(self, path, command):
        super(CommandEvent, self).__init__(path)
        self.command = command


@Type.register
class TrayActivatedEvent(BaseEvent):
    pass
