import requests
import pickle
import socket
import time
from functools import partial
from threading import Thread, Condition
from concurrent.futures import ThreadPoolExecutor

from kivy.lang import Builder
from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.uix.popup import Popup

from deviceitem import DeviceItem
from devicelist import DeviceList
from serverbox import ServerBox
from devicelistbox import DeviceListBox
from settingcontentbox import SettingContentBox

Builder.load_file("settingview.kv")

class SettingView(BoxLayout):

    serverBox = ObjectProperty(None)
    devices = ListProperty([])
    deviceList = ObjectProperty(None)
    settingContentBox = ObjectProperty(None)
    processPop = ObjectProperty(None)
    lastConnDevFile = 'data/lastconnecteddev.p'
    stopFlag = False
    condition = Condition()

    def __init__(self, server_address_file='data/serveraddress.p', **kwargs):
        super(SettingView, self).__init__(**kwargs)
        # Getting the server adrress, deserialize the serveraddress.p
        self.serverAddressFile = server_address_file
        self.processPop = ConnectPopup()

    def init_views(self, *args):
        '''Initialize the view of this class'''
        # Refresh from previous state
        self.refresh_devices()
        # Init devices
        self.init_devices()
        # Start server status checker
        self.start_server_checker()

    def init_devices(self):
        '''Get devices from server and show it on the layout'''
        # Get the server IP from the file
        serverIP, serverName = self.get_server_address()
        if serverIP:
            # Get devices from the server
            self.processPop.open()
            #self.devices = self.get_devices(server_ip=serverIP, server_name = serverName)
            self.get_devices(server_ip=serverIP, server_name = serverName)
            #self.processPop.dismiss()
            # Display devices
            #self.populate_items_to_list(self.devices)
        else:
            print ('Unable to get server IP and server name. Nothing to init')

    def start_server_checker(self):
        '''Start the server checker thread'''
        self.serverBox.serverItem.start_server_checker()

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
        except Exception as e:
            print(f'{e}: Failed loading server address from file: {e}')
        finally:
            return [serverIP, serverName]

    #def get_devices(self, server_ip, server_name):
    def get_devices(self, server_ip, server_name, *args):
        print ('get devices')
        '''Retrieve devices from server REST API'''

        def _send_request():
        # Send request to the server
            isSuccess, r = self.send_request(server_ip, server_name, 8000, 'api/device/', 5)
            if isSuccess:
                Clock.schedule_once(partial(callback, r), 0)
            else:
                print ('Get devices timeout')

        def callback(r, *args):
            devices_response = r.json()  # Produce list of dict
            for device in devices_response:
                deviceID = device['id']
                deviceName = device['deviceName']
                hostName = device['hostName']
                wifiName = device['wifiName']
                wifiPass = device['wifiPass']
                deviceVisionAI = device['visionAI']
                # Appending received devices to devices property
                self.devices.append(
                    DeviceItem(
                        deviceID = deviceID,
                        deviceName = deviceName,
                        host_name = hostName,
                        wifi_name = wifiName,
                        wifi_pass = wifiPass,
                        deviceVisionAI = deviceVisionAI
                        )
                    )
            # Storing connected devices into the file
            self.store_connected_device(deviceJSON = devices_response)
        
        # Starting the server checker thread
        t = Thread(target = _send_request)
        t.daemon = True
        t.start()

        #return self.devices

        # Send request to the server
        #isSuccess, r = self.send_request(server_ip, server_name, 8000, 'api/device/', 5)

        # if isSuccess:
        #     devices_response = r.json()  # Produce list of dict
        #     for device in devices_response:
        #         deviceID = device['id']
        #         deviceName = device['deviceName']
        #         hostName = device['hostName']
        #         wifiName = device['wifiName']
        #         wifiPass = device['wifiPass']
        #         deviceVisionAI = device['visionAI']
        #         # Appending received devices to devices property
        #         self.devices.append(
        #             DeviceItem(
        #                 deviceID = deviceID,
        #                 deviceName = deviceName,
        #                 host_name = hostName,
        #                 wifi_name = wifiName,
        #                 wifi_pass = wifiPass,
        #                 deviceVisionAI = deviceVisionAI
        #                 )
        #             )
        #     # Storing connected devices into the file
        #     self.store_connected_device(deviceJSON = devices_response)
        #     #return self.devices
        # else:
        #     print ('Get devices timeout')
        
        # #print ('notify')
        # # with self.condition:
        # #     self.condition.notify_all()
        # return self.devices

    def populate_items_to_list(self, devices):
        # Populate items to a list widget
        for device in devices:
            self.deviceList.deviceListLayout.add_widget(device)

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

    def store_connected_device(self, deviceJSON):
        '''Serialize connected devices address to file'''
        try:
            with open(self.lastConnDevFile, 'wb') as file:
                pickle.dump(deviceJSON, file)
        except Exception as e:
            print (f'Saving last connected device failed: {e}')

    def update_deviceitem(self, updated_device):
        '''Update some device'''
        # Get current devices
        for device in self.devices:
            if device.deviceID == updated_device['id']:
                # Update the device property except its hostname (not changeable)
                device.deviceName = updated_device['deviceName']
                device.wifiName = updated_device['wifiName']
                device.wifiPass = updated_device['wifiPass']
                device.deviceVisionAI = updated_device['visionAI']
                self.settingContentBox.change_config(device)

    def refresh_devices(self):
        # Refresh the device list
        self.devices.clear()
        # Clear device list widgets
        self.deviceList.deviceListLayout.clear_widgets()

    def button_press_callback(self, widget):
        if widget == self.ids.device_delete_button:
            widget.source = "images/settingview/delete_device_down.png"

    def button_release_callback(self, widget):
        if widget == self.ids.device_delete_button:
            widget.source = "images/settingview/delete_device_normal.png"

    def process_start(self, serverIP, serverName, *args):
        with ThreadPoolExecutor() as executor:
            future = executor.submit(self.get_devices, serverIP, serverName)
            self.devices = future.result()
            return self.devices

    def show_popup(self, *args):
        self.processPop.open()

    def process_dismiss(self, *args):
        print ('dismiss')
        self.processPop.dismiss()

    def stop(self):
        '''Stopping the server checker thread'''
        print ('stoping')
        self.stopFlag = True
        self.serverBox.serverItem.stop_server_checker()

class ConnectPopup(Popup):
    pass

