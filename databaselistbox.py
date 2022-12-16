from kivy.properties import ObjectProperty 
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from databaselistlayout import DatabaseListLayout
from databaseitem import DatabaseItem
from databasecontentbox import DatabaseContentBox

Builder.load_file('databaselistbox.kv')

class DatabaseListBox(BoxLayout):

    databaseView = ObjectProperty(None)
    databaseContentBox = ObjectProperty(None)
    databaseListLayout = ObjectProperty(None)
    btnAdd = ObjectProperty(None)
    btnRefresh = ObjectProperty
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def button_press_callback(self, widget):
        if widget == self.btnAdd:
            widget.source = "images/databaseview/btn_add_icon_down.png"
        elif widget == self.btnRefresh:
            widget.source = "images/databaseview/btn_refresh_down.png"

    def button_release_callback(self, widget):
        if widget == self.btnAdd:
            widget.source = "images/databaseview/btn_add_icon.png"
            self.databaseListLayout.clear_selection()
            self.databaseContentBox.change_config(self)
        elif widget == self.btnRefresh:
            widget.source = "images/databaseview/btn_refresh.png"
            self.parent.init_view()