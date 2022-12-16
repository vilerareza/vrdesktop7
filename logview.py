import io
import base64
import pickle
import requests
import socket
import time
from functools import partial
from threading import Thread

from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.core.image import Image as CoreImage
from kivy.clock import Clock

import numpy as np
from cv2 import imencode

Builder.load_file('logview.kv')


class LogView(BoxLayout):

    manager = ObjectProperty(None)
    logFaceObjectBox = ObjectProperty(None)
    logContentBox = ObjectProperty(None)
    serverAddress = ''
    isServerTimeout = False
    stopFlag = False

    def __init__(self, server_address_file='data/serveraddress.p', **kwargs):
        super().__init__(**kwargs)
        # Getting the server adrress, deserialize the serveraddress.p
        self.serverAddressFile = server_address_file

    def init_view(self, *args):
        '''Initialize the view of this class'''
        # Refresh from previous state
        self.refresh_views()
        # Get logs from server database
        self.init_logs()

    def refresh_views(self):
        # Clearing log grid layout
        self.logFaceObjectBox.stackLayout.clear_widgets()
        self.logContentBox.clear_images()

    def init_logs(self):
        # Get the server IP from the file
        serverIP, serverName = self.get_server_address()
        # Show popup message
        self.manager.open_popup(self)
        #face_ids = self.get_face_ids(serverIP, serverName)
        self.display_log(serverIP, serverName)

    def display_log(self, server_ip, server_name):
        '''Retrieve log from server REST API'''

        def _send_request():
            '''Thread function tp get face IDs'''
            isSuccess = True
            # Resetting the stop flag
            self.stopFlag = False
            '''Send request to the server to get log face IDs'''
            isSuccess, r = self.send_request_get(server_ip, server_name, 8000, f'api/log/faceid/', 5)
            # Empty placeholder list for face responses
            faceResponses = []
            if isSuccess:
                # Success getting log face IDs
                faceIds = r.json()
                faceIds = self.get_logs_unique_faceids(faceIds)
                print (f'FACEIDS: {len(faceIds)}')                
                # Displaying logs
                for id in faceIds:
                    '''Send request to the server to get face object data for given ID'''
                    isSuccess, r = self.send_request_get(server_ip, server_name, 8000, f'api/face/{id}', 5)
                    if isSuccess:
                        faceResponses.append(r.json())
                    else:
                        break
            # Sending request complete. Run callback function
            Clock.schedule_once(partial(callback, isSuccess, faceResponses), 0)

        def callback(isSuccess, face_responses, *args):
            if isSuccess:
                if len (face_responses) > 0:
                    for faceResponse in face_responses:
                        self.show_faceobject(self.logFaceObjectBox, faceobject_data=faceResponse)
                else:
                    print ('Log is empty...')
                # Dismissing popup message
                self.manager.popup.dismiss()
            else:
                # Unable to get faces from database
                if self.stopFlag:
                    # Triggered by cancellation
                    # Dismissing popup message
                    self.manager.popup.dismiss()
                    # Clearing stop flag
                    self.stopFlag = False
                else:
                    # Timeout. Prompting user to acknowledge
                    self.isServerTimeout = True
                    # Displaying message in database content box
                    self.manager.popup.title = 'Server connection timeout'
                    self.manager.popup.button.text = 'OK'
                    print ('Get logs timeout')

        # Starting the new thread
        t = Thread(target = _send_request)
        t.daemon = True
        t.start()
    

    def show_faceobject(self, widget, faceobject_data):
        '''Display face object in the widget'''
        id = faceobject_data['id']
        str_datalist = [
            faceobject_data['faceID'], 
            faceobject_data['firstName'],
            faceobject_data['lastName']
            ]
        faceDataStr = faceobject_data['faceData']
        faceDataNp = pickle.loads(base64.b64decode(faceDataStr))[0]    # choose first image only.
        _, faceDataBytes = imencode(".jpg", faceDataNp)
        coreImg = CoreImage(io.BytesIO(faceDataBytes), ext = 'jpg')
        widget.add_item(id = id, str_datalist = str_datalist, face_texture = coreImg.texture)

    def get_logs_unique_faceids(self, logs):
        '''Get unique face IDs from detection log'''
        ids = []
        for log in logs:
            id = log['objectID']
            ids.append(id)
        faceids = np.unique(ids)
        return faceids

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
            # Setting the class property
            self.serverName = [serverIP, serverName]
            return serverIP, serverName
    
    def send_request_get(self, server_ip, server_name, port, url, timeout = 3):
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

    def popup_button_callback(self, popup):
        # Callback function for manager popup button
        if not self.isServerTimeout:
            # Cancelation
            popup.title = 'Cancelling...'
            # Resetting stop flag
            self.stopFlag = True
        else:
            # Timeout
            popup.dismiss()
            # Resetting isServerTimeout
            self.isServerTimeout = False


    
