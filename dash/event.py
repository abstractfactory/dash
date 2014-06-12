
from pigui.pyqt5.event import BaseEvent, ItemEvent, Type


# class PathEvent(BaseEvent):
#     def __init__(self, path):
#         super(PathEvent, self).__init__()
#         self.path = path


@Type.register
class OpenInExplorerEvent(ItemEvent):
    pass


@Type.register
class OpenInAboutEvent(ItemEvent):
    pass


@Type.register
class HideEvent(ItemEvent):
    pass


@Type.register
class CommandEvent(ItemEvent):
    pass


@Type.register
class TrayActivatedEvent(BaseEvent):
    pass
