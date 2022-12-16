from threading import Thread
import requests
import pickle
import socket
import time
from functools import partial

from kivy.lang import Builder
from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

from deviceicon import DeviceIcon
from livebox import LiveBox
from livegridlayout import LiveGridLayout


Builder.load_file("multiview.kv")

class MultiView(BoxLayout):
    # Grid layout for live stream
    liveGrid = ObjectProperty(None)
    # Layout for device selection to stream
    selectionBox = ObjectProperty(None)
    # Selection scroll view
    selectionScroll = ObjectProperty(None)
    # List for live stream objects
    liveBoxes = ListProperty([])
    # List for device selection icons
    deviceIcons = ListProperty([])
    # Application manager class
    manager = ObjectProperty(None)
    # Device icon selection scroll buttons
    selectionNextButton = ObjectProperty(None)
    selectionBackButton = ObjectProperty(None)
    selectionInterval = 4
    # Server
    serverAddress = []
    # Last connected device
    lastConnDevFile = 'data/lastconnecteddev.p'
    isServerTimeout = False
    stopFlag = False

    def __init__(self, server_address_file='data/serveraddress.p', **kwargs):
        super().__init__(**kwargs)
        # Getting the server adrress, deserialize the serveraddress.p
        self.serverAddressFile = server_address_file
        #self.liveGrid.bind(size = self.adjust_livebox_size)

    def init_views(self, *args):
        '''Initialize the view of this class'''
        # Get the server IP from the file
        serverIP, serverName = self.get_server_address()
        if serverIP:
            # Show popup message
            self.manager.open_popup(self)
            # Get devices from the server - perform in new thread
            self.get_devices(serverIP, serverName)
        else:
            print ('Unable to get server IP and server name. Nothing to init')
            
    def get_server_address(self):
        '''Deserialize server ip and server name from file'''
        serverIP = ''
        serverName = ''
        try:
            # Load the server hostname:port from file
            with open(self.serverAddressFile, 'rb') as file:
                serverAddress = pickle.load(file)
            serverIP = serverAddress[0]
            serverName = serverAddress[1]
            print (serverAddress)
        except Exception as e:
            print(f'{e}: Failed loading server address from file: {e}')
        finally:
            # Setting the class property
            self.serverName = [serverIP, serverName]
            return serverIP, serverName

    def get_devices(self, server_ip, server_name):
        print ('get devices')
        '''Retrieve devices from server REST API'''

        def _send_request():
            '''Thread function'''
            # Resetting the stop flag
            self.stopFlag = False
            # Retrieve devices from server REST API
            isSuccess, r = self.send_request(server_ip, server_name, 8000, 'api/device/', 5)
            # Sending request complete. Run callback function
            Clock.schedule_once(partial(callback, isSuccess, r), 0)

        def callback(isSuccess, r, *args):
            '''Thread callback function'''  
            if isSuccess:
                devices = r.json()  # Produce list of dict
                # Dismissing popup message
                self.manager.popup.dismiss()
                if len(devices) > 0:
                # Create device icon and livebox object
                    if self.create_deviceicon_livebox(devices):
                        self.start_icons()
                        # Showing initLabel
                        self.liveGrid.show_initlabel()
            else:
                if self.stopFlag:
                    # Triggered by cancellation                    
                    self.isServerTimeout = True
                    self.manager.popup.title = 'Cancelled. Use last connected device...'
                    self.manager.popup.button.text = 'OK'
                    # Clearing stop flag
                    self.stopFlag = False
                else:
                    # Timeout. Prompting user to acknowledge
                    self.isServerTimeout = True
                    self.manager.popup.title = 'Timeout. Use last connected device...'
                    self.manager.popup.button.text = 'OK'
                    print ('Get devices timeout')

        # Clearing previous device stream objects and icons if any
        if len(self.deviceIcons) > 0:
            self.stop_streams()
            self.stop_icons()

        # Starting the new thread
        t = Thread(target = _send_request)
        t.daemon = True
        t.start()

    def create_deviceicon_livebox(self, devices):
        '''Create device icon and live box based on 'get devices' response from database'''

        def add_deviceicons_to_selectionbox(device_icons, container):
            for icon in device_icons:
                container.add_widget(icon)

        try:
            for device in devices:
                hostName = device ['hostName']
                deviceName = device['deviceName']
                deviceVisionAI = device['visionAI']
                # Fill device icon list
                self.deviceIcons.append(DeviceIcon(
                    hostName = hostName,
                    deviceName = deviceName,
                    size_hint = (None, None),
                    size = (181, 45)
                    )
                )
                # Fill live box object list
                self.liveBoxes.append(LiveBox(
                    device_name = deviceName
                    )
                )
            # Add deviceIcon content to selection box
            add_deviceicons_to_selectionbox(device_icons = self.deviceIcons,container = self.selectionBox)
            return True
        except Exception as e:
            print (f'multiview:create_device_icon_livebox: {e}')
            return False

    def start_icons(self):
        '''Start the deviceIcon object to get the device IP'''
        if (len(self.deviceIcons) > 0):
            for deviceIcon in self.deviceIcons:
                # Get the device IP
                deviceIcon.get_device_ip()
                # Binding the touch down event
                deviceIcon.bind(on_touch_down=self.icon_touch_action)

    def send_request(self, server_ip, server_name, port, url, timeout = 3):
        '''Send request using server_ip, if it fails try again using server_name'''
        try:
            # Try connecting using IP
            r = requests.get(f'http://{server_ip}:{port}/{url}', timeout = timeout)
            return True, r
        except:
            # Server IP maybe already changed. Try to find the new IP using server_name           
            for i in range(3):
                if not self.stopFlag:
                    try:
                        # Try to get new IP
                        newIP = socket.gethostbyname(server_name)
                        # Try again using new IP
                        r = requests.get(f'http://{newIP}:{port}/{url}', timeout = timeout)
                        # Save new IP to file
                        self.update_server_addr(newIP, server_name)
                        return True, r
                    except Exception as e:
                        print (f'{e}: Failed getting server ip. Retry {i+1}...')
                        time.sleep(3)
                        continue
                else:
                    break
            return False, None

    def update_server_addr(self, server_ip = '', server_name = ''):
        '''Serialize server ip and server name to file'''
        server_address = [server_ip, server_name]
        try:
            with open(self.serverAddressFile, 'wb') as file:
                pickle.dump(server_address, file)
        except Exception as e:
            print (f'Saving server address failed: {e}')

    def icon_touch_action(self, deviceIcon, touch):
        '''When user touch on device icon, show the respective live stream onject (livebox)'''
        if deviceIcon.collide_point(*touch.pos):
            #if deviceIcon.isEnabled:
            if not deviceIcon.disabled:
                if self.liveBoxes[self.deviceIcons.index(deviceIcon)].status != "play":
                    # If the live stream object status is not playing then add #
                    self.show_live_box(deviceIcon)
                else:
                    # If the live stream object status is playing then remove
                    self.remove_live_box(deviceIcon)
            
    def show_live_box(self, deviceIcon):
        '''Show the live stream object based on selected device icon'''
        index = self.deviceIcons.index(deviceIcon)
        deviceIP = deviceIcon.deviceIP
        if self.liveGrid.nLive == 0:
            # Removing initLabel
            self.liveGrid.hide_initlabel()
        # Start the live steaming object
        #self.liveBoxes[index].start_live_stream(deviceIP='vr774c6498')
        self.liveBoxes[index].start_live_stream(deviceIP = deviceIP)   
        # Adjust live grid row and cols for displaying live stream #
        self.adjust_livegrid(action = 'add')
        # Display the live stream object to live grid layout
        self.liveGrid.add_widget(self.liveBoxes[index])
        # Adjust the livestream to the size of livebox
        self.adjust_livebox_size()
        # print (f'ROWS : {self.liveGrid.rows} COLS : {self.liveGrid.cols}')

    def remove_live_box(self, deviceIcon):
        '''Stop live stream object based on selected device icon'''
        self.liveBoxes[self.deviceIcons.index(deviceIcon)].stop_live_stream()
        # Remove live stream object from live grid layout
        self.liveGrid.remove_widget(self.liveBoxes[self.deviceIcons.index(deviceIcon)])
        # Re-adjust live grid rows and cols
        if self.adjust_livegrid(action = 'remove') > 0:
            # Adjust the livestream to the size of livebox
            self.adjust_livebox_size()
        else:
            # Showing initLabel
            self.liveGrid.show_initlabel()
        #print (f'ROWS : {self.liveGrid.rows} COLS : {self.liveGrid.cols}')

    def adjust_livegrid(self, action = 'add'):
        '''Adjust liveGrid rows and collumns based on add / remove of livebox. Return True if success'''
        if action == 'add':
            self.liveGrid.nLive +=1
            rowLimit = self.liveGrid.rows**2 + self.liveGrid.rows
            if self.liveGrid.nLive > rowLimit:
                self.liveGrid.rows +=1
            colLimit = self.liveGrid.cols**2
            if (self.liveGrid.nLive > colLimit):
                self.liveGrid.cols +=1
        elif action == 'remove':
            self.liveGrid.nLive -=1
            if self.liveGrid.nLive > 0:
                rowLimit = (self.liveGrid.rows-1)**2 + (self.liveGrid.rows-1)
                if self.liveGrid.nLive <= rowLimit:
                    self.liveGrid.rows -=1
                colLimit = (self.liveGrid.cols-1)**2
                if (self.liveGrid.nLive <= colLimit):
                    self.liveGrid.cols -=1
        # Return the number of livebox    
        return self.liveGrid.nLive

    def adjust_livebox_size(self, *args):
        '''Adjust the size of individual livebox based on the row and col in the liveGrid'''
        cell_width = ((self.liveGrid.width - self.liveGrid.spacing[0]*(self.liveGrid.cols-1))/
                    self.liveGrid.cols)
        cell_height = ((self.liveGrid.height - self.liveGrid.spacing[0]*(self.liveGrid.rows-1))/
                    self.liveGrid.rows)
        for livebox in self.liveBoxes:
            livebox.adjust_self_size(size = (cell_width, cell_height))
        #print (f'GRID SIZE {self.liveGrid.size}, CELL SIZE {cell_width}, {cell_height}')

    def stop_icons(self):
        '''Trigger deviceIcon objects to stop running thread'''
        for deviceIcon in self.deviceIcons:
            deviceIcon.stop()
        self.selectionBox.clear_widgets()
        self.deviceIcons.clear()

    def stop_streams(self):
        '''Stop live streams anyway'''
        for liveBox in self.liveBoxes:
            liveBox.stop_live_stream()
        # Reset and clearing widgets from liveGrid
        self.liveGrid.clear_widgets()
        self.liveGrid.nLive = 0
        self.liveGrid.rows = 1
        self.liveGrid.cols = 1
        # Clear the list of live stream objects
        self.liveBoxes.clear()

    def stop(self):
        self.stopFlag = True
        self.stop_streams()
        self.stop_icons()
  
    def selection_next_press(self, button):
        if self.selectionScroll.scroll_x < 1:
            self.selectionScroll.scroll_x += 0.1
            if self.selectionScroll.scroll_x >= 1:
                self.selectionScroll.scroll_x = 1

    def selection_back_press(self, button):
        if self.selectionScroll.scroll_x > 0:
            self.selectionScroll.scroll_x -= 0.1
            if self.selectionScroll.scroll_x <= 0:
                self.selectionScroll.scroll_x = 0
    
    def popup_button_callback(self, popup):
        # Callback function for manager popup button
        if not self.isServerTimeout:
            popup.title = 'Cancelling...'
            self.stopFlag = True
        else:
            popup.dismiss()
            # Unable to get devices from server. Try getting the last connected device from file
            with open(self.lastConnDevFile, 'rb') as file:
                devices = pickle.load(file)
            if len(devices) > 0:
                # Create device icon and livebox object
                if self.create_deviceicon_livebox(devices):
                    self.start_icons()
                    # Showing initLabel
                    self.liveGrid.show_initlabel()
            self.isServerTimeout = False


