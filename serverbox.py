from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.floatlayout import FloatLayout

from serveritem import ServerItem

Builder.load_file("serverbox.kv")

class ServerBox(FloatLayout):

    serverItem = ObjectProperty(None)
    titleLabel = ObjectProperty(None)

    deviceListLayout = ObjectProperty(None)
    settingContentBox = ObjectProperty(None)
    serverItemSelected = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def deselect_serverItem(self):
        #self.serverIcon.state = 'normal'
        self.serverItemSelected = False
        self.serverItem.serverImage.source = "images/settingview/servericon_normal.png"

    def item_touch_down(self, widget, touch):
        if widget.collide_point(*touch.pos):
            if not self.serverItemSelected:
                self.serverItemSelected = True
                widget.serverImage.source = "images/settingview/servericon_down.png"
                # Clearing the selection on device list layout
                self.deviceListLayout.clear_selection()
                # Notify the setting content layout to change the content
                if self.settingContentBox:
                    self.settingContentBox.change_config(widget)