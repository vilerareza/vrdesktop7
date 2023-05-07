from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.clock import Clock

from settingview import SettingView
from multiview import MultiView
from databaseview import DatabaseView
from logview import LogView

from threading import Thread

Builder.load_file('maintabs.kv')

class MainTabs(TabbedPanel):

    multiView = ObjectProperty(None)
    settingView = ObjectProperty(None)
    databaseView = ObjectProperty(None)
    logView = ObjectProperty(None)

    tabMultiView = ObjectProperty(None)
    tabSettingView = ObjectProperty(None)
    tabDatabaseView = ObjectProperty(None)
    tabLogView = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pass
    
    # Note: Not used anywhere
    def tabLogViewPressed(self, tab):
        if tab.state == "down":
            # Stop the multiview
            self.multiView.stop()
            # Stop the settingview
            self.settingView.stop()
            self.logView.get_server_address()
            
    def stop(self):
        self.multiView.stop()
        self.settingView.stop()

    def tab_state_callback(self, tab):
        if tab.state == 'down':
            if tab == self.tabSettingView:
                # Stop the multiview
                self.multiView.stop()
                # Get the setting view
                Clock.schedule_once(self.settingView.init_views, 0.5)
            elif tab == self.tabMultiView:
                # Stop the settingview
                self.settingView.stop()
                # Get the multi view
                Clock.schedule_once(self.multiView.init_views, 0.5)
            elif tab == self.tabDatabaseView:
                # Stop the multiview
                self.multiView.stop()
                # Stop the settingview
                self.settingView.stop()
                # Init the databaseview
                Clock.schedule_once(self.databaseView.init_view, 0.5)
            elif tab == self.tabLogView:
                # Stop the multiview
                self.multiView.stop()
                # Stop the settingview
                self.settingView.stop()
                # Init the databaseview
                Clock.schedule_once(self.logView.init_view, 0.5)

                