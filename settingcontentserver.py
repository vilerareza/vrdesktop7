from threading import Thread
import time
import requests
import socket

from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from mylayoutwidgets import ImageButton, ImageToggle

Builder.load_file("settingcontentserver.kv")

class SettingContentServer(FloatLayout):
    editMode = BooleanProperty(False)
    serverObj = None
    titleLabelText = 'Server Setting'
    titleLabel = ObjectProperty(None)
    serverAddressLabel = ObjectProperty(None)
    serverAddressText = ObjectProperty(None)
    btnSaveEdit = ObjectProperty(None)
    testLabel = ObjectProperty(None)
    testImage = ObjectProperty(None)
    myParent = ObjectProperty(None)
    isReset = False

    serverAddressFile = 'data/serveraddress.p'

    def toggle_press_callback(self, button):
        '''callback function for edit/save button'''
        if button == self.btnSaveEdit:
            if button.state == 'down':
                self.editMode = True
            else:
                self.editMode = False
                if not self.isReset:
                    # Only save the server address when toggle is not triggered by reset method
                    # Serializing server IP and server name
                    print ('save server address')
                    serverIP, serverName = self.save_server_addr(self.serverAddressText)
                    if serverIP:
                        # Test the connection to the server in different thread
                        self.test_server(serverIP)
                        # Refresh the devices
                        #self.parent.reinit_views()

    def save_server_addr(self, entry_widget):
        '''Updating the server IP and server host name'''
        serverName = ''
        serverIP = ''
        try:
            if self.validate_entry(entry_widget):
                # If entry is not empty then process
                serverName = entry_widget.text
                serverIP = self.get_server_ip(serverName)
                if self.serverObj:
                    # serverObj is serveritem
                    self.serverObj.update_server_addr(serverIP, serverName)
        finally:
            return serverIP, serverName

    def validate_entry(self, *args):
        '''Validate if user input is not empty'''
        isValid = True
        for entry in args:
            if entry.text == '':
                isValid = False
                entry.background_color = (0.9, 0.7, 0.7)
            else:
                entry.background_color = (1, 1, 1)
        return isValid

    def get_server_ip(self, server_name):
        '''Get server ip address from entered server hostname'''
        serverIP = ''      
        for i in range(3):
            # Perform 3 times trial
            try:
                serverIP = socket.gethostbyname(server_name)
                break
            except Exception as e:
                print (f'{e}: Failed getting server ip. Retry {i+1}...')
                time.sleep(3)
                continue        
        return serverIP
            
    def fill(self, server_obj):
        # This method is executed when the server item is selected. The serverObj will be serverItem
        if server_obj:
            # Getting the server object
            self.serverObj = server_obj
            # Updating the text with serverObj server address property
            self.serverAddressText.text = server_obj.serverName

    def reset(self):
        print ('reset')
        '''Reset the widgets state'''
        # Setting isReset to True to prevent saving server address when the btnSaveEdit toggle event is fired.
        self.isReset = True
        # Reset the btnSaveEdit toggle button state to normal. This will trigger toggle event when state is changed.
        self.btnSaveEdit.state = 'normal'
        # Setting isReset back to False to enable the saving server name when the btnSaveEdit toggle event is fired.
        self.isReset = False
        self.serverAddressText.background_color = (1, 1, 1)
        self.testLabel.text = ''
        self.testImage.opacity = 0

    def on_parent(self, *args):
        if self.parent:
            self.reset()
            
    def test_server(self, server_ip, port = 8000):
        '''Start the server status checker thread'''

        def callback_ok(*args):
            self.testLabel.text = 'Server OK'
            self.testImage.opacity = 1
            self.testImage.source = 'images/settingview/server_ok.png'
        
        def callback_fail(*args):
            self.testLabel.text = 'Server Not Found'
            self.testImage.opacity = 1
            self.testImage.source = 'images/settingview/server_fail.png'

        def check():
            try:
                r = requests.get(f'http://{server_ip}:{port}/servercheck/', timeout = 5)
                if r.status_code == 200 and r.text == 'ServerOk!':
                    Clock.schedule_once(callback_ok, 0)
                else:
                    Clock.schedule_once(callback_fail, 0)
            except Exception as e:
                Clock.schedule_once(callback_fail, 0)
                print (f'test_server failed :{e}')

        t = Thread(target = check)
        t.daemon = True
        t.start()


