import base64
import io
import pickle
import requests
import socket
import time
from functools import partial
from threading import Thread

from cv2 import imencode

from kivy.core.image import Image as CoreImage
from kivy.lang import Builder
from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

from databasecontentbox import DatabaseContentBox
from databaseitem import FaceObjectWidget

Builder.load_file('databaseview.kv')

class DatabaseView(BoxLayout):

    faces = ListProperty([])
    manager = ObjectProperty(None)
    databaseListBox = ObjectProperty(None)
    databaseContentBox = ObjectProperty(None)
    serverAddress = ''
    stopFlag = False
    isServerTimeout = False

    def __init__(self, server_address_file='data/serveraddress.p', **kwargs):
        super().__init__(**kwargs)
        # Getting the server adrress, deserialize the serveraddress.p
        self.serverAddressFile = server_address_file

    def init_view(self, *args):
        '''Initialize the view of this class'''
        # Refresh from previous state
        self.refresh_views()
        # Get faces from database
        self.init_faces()

    def refresh_views(self):
        self.faces.clear()
        self.databaseListBox.databaseListLayout.clear_widgets()
        self.databaseContentBox.clear_widgets()

    def init_faces(self):
        '''Get devices from server and show it on the layout'''
        # Get the server IP from the file
        serverIP, serverName = self.get_server_address()
        # Show popup message
        self.manager.open_popup(self)
        # Get devices from the server - perform in new thread
        self.get_faces(server_ip=serverIP, server_name = serverName)

    def get_faces(self, server_ip, server_name):
        '''Retrieve faces from server REST API'''

        def _send_request():
            '''Thread function'''
            # Resetting the stop flag
            self.stopFlag = False
            # Send request to the server
            isSuccess, r = self.send_request_get(server_ip, server_name, 8000, f'api/face/', 5)
            # Sending request complete. Run callback function
            Clock.schedule_once(partial(callback, isSuccess, r), 0)

        def callback(isSuccess, r, *args):
            if isSuccess:
                # Success getting face from fatabase
                face_response = r.json()  # Produce list of dict
                if len (face_response) > 0:
                    # Faces exist in database
                    for face in face_response:
                        id = face['id']
                        faceID = face['faceID']
                        firstName = face['firstName']
                        lastName = face['lastName']
                        faceDataStr = face['faceData']
                        faceDataNp = pickle.loads(base64.b64decode(faceDataStr))
                        # Take image in index 0 only
                        _, faceDataBytes = imencode(".jpg", faceDataNp[0])
                        coreImg = CoreImage(io.BytesIO(faceDataBytes), ext = 'jpg')
                        self.faces.append(
                            FaceObjectWidget(
                                id = id,
                                str_datalist= [faceID, firstName, lastName],
                                img_datalist = faceDataNp,
                                face_texture = coreImg.texture)
                        )
                        self.databaseContentBox.no_selection_config(text = 'Select Face for Info...')
                    # Show faces in databaseListLayout
                    self.show_faces(self.databaseListBox.databaseListLayout, self.faces)
                else:
                    # Face does not exist
                    self.databaseContentBox.no_selection_config(text = 'No Face Found, Add Face to Database...')
                    
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
                    print ('Get faces timeout')
            # Displaying message in database content box
            self.databaseContentBox.no_selection_config(text = 'Unable to Connect to Server Database...')

        # Starting the new thread
        t = Thread(target = _send_request)
        t.daemon = True
        t.start()

    def show_faces(self, layout, face_widget_list):
        '''Populate items to a list widget'''
        for faceWidget in face_widget_list:
            layout.add_widget(faceWidget)

    def update_database_item(self, new_data):
        '''Update displayed face based on new_data'''
        for face in self.faces:
            if face.id == new_data['id']:
                # Update the device property except its hostname (not changeable)
                face.dataID = new_data['faceID']
                face.dataFirstName = new_data['firstName']
                face.dataLastName = new_data['lastName']
                self.databaseContentBox.change_config(face)

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