from kivy.graphics import Color, Rectangle
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout

from databaseitem import DatabaseItem, FaceObjectWidget
from databasecontentface import DatabaseContentFace
from databaseaddface import DatabaseAddFace
from databasenoselection import DatabaseNoSelection

Builder.load_file("databasecontentbox.kv")

class DatabaseContentBox(BoxLayout):
    databaseView = ObjectProperty(None)
    databaseListBox = ObjectProperty(None)
    noSelectionLabel = DatabaseNoSelection()
    databaseContentFace = DatabaseContentFace()
    databaseAddFace = DatabaseAddFace()

    def change_config(self, obj = None):
        self.clear_widgets()
        if type(obj) == FaceObjectWidget:
            # Filling the databaseContentFace with face database object
            self.databaseContentFace.fill(obj)
            self.add_widget(self.databaseContentFace)
        elif obj == self.databaseListBox:
            # Add new face to database. Show databaseaddface
            self.add_widget(self.databaseAddFace)

    def no_selection_config(self, text=''):
        #Clearing widgets
        self.clear_widgets()
        if text != '':
           self.noSelectionLabel.text = text
        self.add_widget(self.noSelectionLabel)

    def request_parent_refresh(self):
        # Refresh face list
        self.databaseView.init_view()

    def update_database_item(self, new_data):
        # Update the edited data.
        self.databaseView.update_database_item(new_data)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
