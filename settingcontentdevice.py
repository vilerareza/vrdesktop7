import os
import requests
import socket
import pickle
import qrcode
import uuid
import json
import time

from kivy.lang import Builder
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from mylayoutwidgets import ImageButton, ImageToggle

Builder.load_file("settingcontentdevice.kv")

class SettingContentDevice(FloatLayout):
    editMode = BooleanProperty(False)
    titleLabel = ObjectProperty(None)
    deviceNameLabel = ObjectProperty(None)
    deviceNameText = ObjectProperty(None)
    wifiNameLabel = ObjectProperty(None)
    wifiNameText = ObjectProperty(None)
    wifiPassLabel = ObjectProperty(None)
    wifiPassText = ObjectProperty(None)
    visionAILabel = ObjectProperty(None)
    visionAISwitch = ObjectProperty(None)
    btnSaveEdit = ObjectProperty(None)
    btnRemove = ObjectProperty(None)
    qrImage = ObjectProperty(None)
    isReset = False

    def __init__(self, server_address_file='data/serveraddress.p', qr_save_dir ='images/temp/qr/', **kwargs):
        super().__init__(**kwargs)
        # Getting the server adrress
        self.serverAddressFile = server_address_file
        self.qrSaveDir = qr_save_dir

    def save_device_to_db(self, *args):
        '''Save attribute to selected device'''
        if self.validate_entry(*args):
            # User pressed "Save"
            deviceID = self.deviceObjID
            newDeviceName = self.deviceNameText.text
            newWifiName = self.wifiNameText.text
            newWifiPass = self.wifiPassText.text
            newVisionAI = self.visionAISwitch.active
            deviceData = {'deviceName': newDeviceName, 'showName': '', 'wifiName': newWifiName, 'wifiPass': newWifiPass, 'visionAI' : newVisionAI}
            serverIP, serverName = self.get_server_address()
            isSuccess, r = self.send_request('put', serverIP, serverName, 8000, f'api/device/{deviceID}/', deviceData, 5)
            if isSuccess:
                print (r.status_code)
                if r.status_code == 200:
                    # Get the new device attribute (json) form the sever
                    newDevice = self.get_device_detail(serverIP, serverName, deviceID)
                    # Update the current deviceitem
                    self.parent.update_deviceitem(newDevice)

    def validate_entry(self, *args):
        isValid = True
        for entry in args:
            if entry.text == '':
                isValid = False
                entry.background_color = (0.9, 0.7, 0.7)
            else:
                entry.background_color = (1, 1, 1)
        return isValid

    def get_device_detail(self, server_ip, server_name, device_id):
        '''Get device with specific device ID from server REST API'''
        try:
            _, r = self.send_request('get', server_ip, server_name, 8000, f'api/device/{device_id}/', None, 5)
            device = r.json()
            return device
        except Exception as e:
            print (e)
            return {}

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

    def send_request(self, method, server_ip, server_name, port, url, data = None, timeout = 3):
        '''Send request using server_ip, if it fails try again using server_name'''
        try:
            # Try connecting using IP
            if method ==  'get':
                # GET
                r = requests.get(f'http://{server_ip}:{port}/{url}', timeout = timeout)
            elif method == 'post':
                # POST
                r = requests.post(f'http://{server_ip}:{port}/{url}', data = data, timeout = timeout)
            elif method == 'put':
                # PUT
                r = requests.put(f'http://{server_ip}:{port}/{url}', data = data, timeout = timeout)
            elif method == 'delete':
                # DELETE
                r = requests.delete(f'http://{server_ip}:{port}/{url}', timeout = timeout)
            return True, r
        
        except:
            # Server IP maybe already changed. Try to find the new IP using server_name           
            for i in range(3):
                try:
                    # Try to get new IP
                    newIP = socket.gethostbyname(server_name)
                    # Try again using new IP
                    if method ==  'get':
                        # GET
                        r = requests.get(f'http://{newIP}:{port}/{url}', timeout = timeout)
                    elif method == 'post':
                        # POST
                        r = requests.post(f'http://{server_ip}:{port}/{url}', data = data, timeout = timeout)
                    elif method == 'put':
                        # PUT
                        r = requests.put(f'http://{server_ip}:{port}/{url}', data = data, timeout = timeout)
                    elif method == 'delete':
                        # DELETE
                        r = requests.delete(f'http://{server_ip}:{port}/{url}', timeout = timeout)
                    # Save new IP to file
                    self.update_server_addr(newIP, server_name)
                    return True, r
                except Exception as e:
                    print (f'{e}: Failed getting server ip. Retry {i+1}...')
                    time.sleep(3)
                    continue
            return False, None

    def update_server_addr(self, server_ip = '', server_name = ''):
        '''Serialize server ip and server name to file'''
        server_address = [server_ip, server_name]
        try:
            with open(self.serverAddressFile, 'wb') as file:
                pickle.dump(server_address, file)
        except Exception as e:
            print (f'Saving server address failed: {e}')

    def on_parent(self, *args):
        if self.parent:
            self.reset()

    def reset(self):
        print ('reset')
        '''Reset the widgets state'''
        # Setting isReset to True to prevent saving to database when the btnSaveEdit toggle event is fired.
        self.isReset = True
        # Reset the btnSaveEdit toggle button state to normal. This will trigger toggle event when state is changed.
        self.btnSaveEdit.state = 'normal'
        # Setting isReset back to False to enable the saving to database when the btnSaveEdit toggle event is fired.
        self.isReset = False
        # Reset the text inputs bg color 
        self.deviceNameText.background_color = (1, 1, 1)
        self.wifiNameText.background_color = (1, 1, 1)
        self.wifiPassText.background_color = (1, 1, 1)

    def populate(self, device_obj):
        '''Populate the view'''
        if self.get_device_obj(device_obj):
            self.fill (self.deviceObjName, self.deviceObjHostName, self.deviceObjWifiName, self.deviceObjWifiPass, self.deviceObjVisionAI)

    def get_device_obj(self, device_obj):
        '''Getting attribute of selected device object'''
        isDeviceObj = False
        if device_obj:
            self.deviceObjID = device_obj.deviceID
            self.deviceObjName = device_obj.deviceName
            self.deviceObjHostName = device_obj.hostName
            self.deviceObjWifiName = device_obj.wifiName
            self.deviceObjWifiPass = device_obj.wifiPass
            self.deviceObjVisionAI = device_obj.deviceVisionAI
            isDeviceObj = True
        return isDeviceObj
        

    def fill(self, device_obj_name, device_obj_host_name, device_obj_wifi_name, device_obj_wifi_pass, device_obj_visionai):
        
        def generate_qr(qr_data):
            # Remove previous qr image file (if exist)
            qrImage = os.listdir(self.qrSaveDir)
            for image in qrImage:
                os.remove(os.path.join(self.qrSaveDir, image))
            # Init QR generator
            qr = qrcode.QRCode(
                version=5,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=5,
                border=4)
            data = json.dumps(qr_data)
            qr.add_data(str(data))
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            # Saving QR image and display it
            qrFileName = f'{self.qrSaveDir}{str(uuid.uuid4())[0:8]}.png'
            img.save(qrFileName)
            self.qrImage.source = qrFileName

        # Getting server address
        serverName, serverIP = self.get_server_address()
        self.deviceNameText.text = device_obj_name
        self.wifiNameText.text = device_obj_wifi_name
        self.wifiPassText.text = device_obj_wifi_pass
        self.visionAISwitch.active = device_obj_visionai
        #qrData = {'server': serverAddress, 'host': host, 'name':deviceName, 'ssid':ssid, 'psk':psk}
        qrData = {'server': serverName, 'host': device_obj_host_name, 'name':device_obj_name, 'ssid':device_obj_wifi_name, 'psk':device_obj_wifi_pass}
        generate_qr(qrData)

    def remove_from_db(self):
        print ('remove from db')
        if self.deviceObjID:
            try:
                serverIP, serverName = self.get_server_address()
                isSuccess, r = self.send_request('delete', serverIP, serverName, 8000, f'api/device/{self.deviceObjID}/', None, 5)
                if isSuccess:
                    print (f'Status code: {r.status_code}')
                    # Refresh the device list.
                    self.parent.reinit_views()
                    self.parent.no_selection_config()
            except Exception as e:
                print (e)

    def toggle_press_callback(self, button):
        '''callback function for edit/save button'''
        if button == self.btnSaveEdit:
            if button.state == 'down':
                self.editMode = True
            else:
                print (self.isReset)
                self.editMode = False
                if not self.isReset:
                    # Only save to db when toggle is not triggered by reset method
                    print ('save to db')
                    self.save_device_to_db(self.deviceNameText, self.wifiNameText, self.wifiPassText)

    def button_press_callback(self, button):
        if button == self.btnRemove:
            button.source = 'images/settingview/btn_remove_down.png'

    def button_release_callback(self, button):
        if button == self.btnRemove:
            button.source = 'images/settingview/btn_remove.png'
            self.remove_from_db()


