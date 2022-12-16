from kivy.properties import ObjectProperty 
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from devicelist import DeviceList

Builder.load_file('devicelistbox.kv')

class DeviceListBox(BoxLayout):
    settingView = ObjectProperty(None)
    deviceListLayout = ObjectProperty(None)
    serverBox = ObjectProperty(None)
    settingContentBox = ObjectProperty(None)
    btnDeviceAdd = ObjectProperty(None)
    btnRefresh = ObjectProperty

    def button_press_callback(self, button):
        if button == self.btnDeviceAdd:
            button.source = 'images/settingview/btn_add_icon_down.png'
        elif button == self.btnRefresh:
            button.source = 'images/settingview/btn_refresh_down.png'

    def button_release_callback(self, button):
        if button == self.btnDeviceAdd:
            button.source = 'images/settingview/btn_add_icon.png'
            self.settingContentBox.change_config(self)
            # Clear selection on serverBox or deviceListLayout
            self.serverBox.deselect_serverItem()
            self.deviceListLayout.clear_selection()
        elif button == self.btnRefresh:
            button.source = 'images/settingview/btn_refresh.png'
            self.settingView.init_views()