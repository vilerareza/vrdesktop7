import os
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.metrics import dp

import pickle

import sqlite3

Builder.load_file('manager.kv')

class Manager(BoxLayout):

    headerBar = ObjectProperty(None)
    mainTabs = ObjectProperty (None)
    popup = ObjectProperty(None)
    popupRequester = ObjectProperty(None)
    
    aiModel = None

    faceDatabase = {}
    faceDbPath = 'data/databasepath.pckl'

    logDb = {'dbName': 'log.db', 'tableName': 'facelog'}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.move_main_tabs()
        self.popup = ConnectPopup()
        #self.popup.button.bind(on_press = self.popup_button_press)
        self.popup.button.bind(on_release = self.popup_button_release)

    def move_main_tabs(self):
        ''' Move main tabs to header bar'''
        # Copy the original tabs
        self.newTabs = self.mainTabs.tab_list.copy()
        # Remove the original tabs
        self.mainTabs.clear_tabs()
        self.mainTabs.tab_height = 0
        # Put the copy of original tabs in the header bar
        for newTab in reversed(self.newTabs):
            # Styling
            if newTab == self.mainTabs.tabSettingView: #ids.id_tab_setting_view:
                # New setting tab
                newTab.size_hint = (None, None)
                newTab.size = (dp(40), dp(40))
                newTab.background_normal = 'images/tab_setting_normal.png'
                newTab.background_down = 'images/tab_setting_down.png'
                self.headerBar.tabStrip.add_widget(newTab)
            elif newTab == self.mainTabs.tabMultiView: #ids.id_tab_multi_view:
                # New multiview tab
                newTab.size_hint = (None, None)
                newTab.size = (dp(40), dp(40))
                newTab.background_normal = 'images/tab_multiview_normal.png'
                newTab.background_down = 'images/tab_multiview_down.png'
                self.headerBar.tabStrip.add_widget(newTab)
            elif newTab == self.mainTabs.tabDatabaseView: 
                # New database tab
                newTab.size_hint = (None, None)
                newTab.size = (dp(40), dp(40))
                newTab.background_normal = 'images/tab_database_normal.png'
                newTab.background_down = 'images/tab_database_down.png'
                self.headerBar.tabStrip.add_widget(newTab)
            elif newTab == self.mainTabs.tabLogView: 
                # New database tab
                newTab.size_hint = (None, None)
                newTab.size = (dp(40), dp(40))
                newTab.background_normal = 'images/tab_log_normal.png'
                newTab.background_down = 'images/tab_log_down.png'
                self.headerBar.tabStrip.add_widget(newTab)
    
    def get_vision_ai(self):
        return self.aiModel
    
    # def log_detection(self, face_id, detection_id, time_stamp= ['', ''], device_name=''):
    #     con = sqlite3.connect(self.logDb['dbName'])
    #     cur = con.cursor()
    #     sql = "INSERT INTO "+self.logDb['tableName']+" (faceID, camera, date, time, detectionID) VALUES ('"+face_id+"', '"+device_name+"', '"+time_stamp[0]+"', '"+time_stamp[1]+"', '"+detection_id+"')"
    #     cur.execute(sql)
    #     con.commit()
    #     con.close()

    # def clear_log(self):
    #     con = sqlite3.connect(self.logDb['dbName'])
    #     cur = con.cursor()
    #     sql = "DELETE FROM "+self.logDb['tableName']
    #     cur.execute(sql)
    #     con.commit()
    #     con.close()
    #     # Clear images
    #     images = os.listdir('logs/images/faces/')
    #     for image in images:
    #             os.remove(os.path.join('logs/images/faces/', image))
    #     images = os.listdir('logs/images/frames/')
    #     for image in images:
    #             os.remove(os.path.join('logs/images/frames/', image))

    # def get_log(self):
    #     con = sqlite3.connect(self.logDb['dbName'])
    #     cur = con.cursor()
    #     sql = "SELECT * FROM "+self.logDb['tableName']
    #     cur.execute(sql)
    #     log = []
    #     for record in cur:
    #         log.append(record)
    #     con.close()
    #     #print (log)
    #     return log

    def open_popup(self, requester):
        self.popupRequester = requester
        self.popup.title = 'Connecting to Server...'
        self.popup.button.text = 'Cancel'
        self.popup.open()

    def popup_button_release(self, button):
        self.popupRequester.popup_button_callback(self.popup)
        # if self.popupRequester.serverTimeOut:
        #     self.popup.dismiss()
        # else:
        #     self.popup.title = 'Cancelling...'
        #     self.popupRequester.stopFlag = True
        #button.source = 'images/settingview/btn_popup_cancel.png'

    #def popup_button_press(self, button):
        #button.source = 'images/settingview/btn_popup_cancel_down.png'

    def stop(self):
        self.mainTabs.stop()

class ConnectPopup(Popup):
    pass