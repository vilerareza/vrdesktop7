import io
import requests
import pickle
import socket
import time

from cv2 import imencode
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivy.properties import ObjectProperty, BooleanProperty
from mylayoutwidgets import ImageButton, ImageToggle

Builder.load_file('databasecontentface.kv')

class DatabaseContentFace(FloatLayout):

    faceIDText = ObjectProperty(None)
    faceFirstNameText = ObjectProperty(None)
    faceLastNameText = ObjectProperty(None)
    faceImageLayout = ObjectProperty(None)
    btnSaveEdit = ObjectProperty(None)
    btnRemove = ObjectProperty(None)
    editMode = BooleanProperty(False)
    faceContent = []
    serverAddress = ''

    def __init__(self, server_address_file='data/serveraddress.p', **kwargs):
        super().__init__(**kwargs)
        '''Getting the server adrress'''
        self.serverAddressFile = server_address_file

    def fill(self, face_obj):
        '''Filling data to widgets'''
        # Setting class properties
        self.id = face_obj.id
        # self.faceID = str(face_obj.dataID)
        # self.faceFirstName = face_obj.dataFirstName
        # self.faceLastName = face_obj.dataLastName
        # self.imgDataList = face_obj.imgDataList
        # Filling widgets
        # self.faceIDText.text = self.faceID
        # self.faceFirstNameText.text = self.faceFirstName
        # self.faceLastNameText.text = self.faceLastName
        self.faceIDText.text = str(face_obj.dataID)
        self.faceFirstNameText.text = face_obj.dataFirstName
        self.faceLastNameText.text = face_obj.dataLastName
        # Displaying images
        self.display_images(face_obj.imgDataList)
    
    def display_images(self, img_data_list):
        '''Displaying images in faceImageLayout'''
        # Clearing previous images
        self.faceImageLayout.clear_widgets()
        for imgData in img_data_list:
            _, faceDataBytes = imencode(".jpg", imgData)
            coreImg = CoreImage(io.BytesIO(faceDataBytes), ext = 'jpg')
            # Creating and adding image object to face image layout
            self.faceImageLayout.add_widget(
                Image(texture = coreImg.texture,size_hint = (None, 1))
                )

    def save_change_to_db(self):
        '''Save face change to db'''
        def _get_face_detail(server_ip, server_name, id):
            isSuccess, r = self.send_request('get', server_ip, server_name, 8000, f'api/face/{id}/', None, 5)
            if isSuccess:
                face = r.json()
                return face
            else:
                return {}

        try:
            # User pressed "Save. Prepare new data"
            id = self.id
            newFaceID = self.faceIDText.text
            newFaceFirstName = self.faceFirstNameText.text
            newFaceLastName = self.faceLastNameText.text
            newData = {'faceID': newFaceID, 'firstName': newFaceFirstName, 'lastName': newFaceLastName}
            serverIP, serverName = self.get_server_address()
            #r = requests.put(f"http://{serverAddress}/api/face/{id}/", data = newData)
            isSuccess, r = self.send_request('put', serverIP, serverName, 8000, f'api/face/{id}/', newData,  5)
            print (f'{isSuccess} {r.status_code}')
            if isSuccess:
                if r.status_code == 200:
                    # Get the new device attribute (json) form the sever
                    newFace = _get_face_detail(serverIP, serverName, id)
                    # Update the current deviceitem
                    self.parent.update_database_item(newFace)
        except Exception as e:
            print (f'save_change_db: {e}')

    def remove_from_db(self, id):
        '''Remove face based on given id'''
        serverIP, serverName = self.get_server_address()
        isSuccess, r = self.send_request('delete', serverIP, serverName, 8000, f'api/face/{id}/', None, 5)
        #r = requests.delete(f"http://{serverAddress}/api/face/{id}/")
        if isSuccess:
            response = r.status_code
            print (f'Status code: {response}')
            self.parent.request_parent_refresh()

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

    def send_request(self, method, server_ip, server_name, port, url, data = None, timeout = 3):
        '''Send request using server_ip, if it fails try again using server_name'''
        try:
            # Try connecting using IP
            if method ==  'get':
                r = requests.get(f'http://{server_ip}:{port}/{url}', timeout = timeout)
            elif method == 'put':
                r = requests.put(f'http://{server_ip}:{port}/{url}', data = data, timeout = timeout)
            elif method == 'delete':
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
                        r = requests.get(f'http://{newIP}:{port}/{url}', timeout = timeout)
                    elif method == 'put':
                        r = requests.put(f'http://{server_ip}:{port}/{url}', data = data, timeout = timeout)
                    elif method == 'delete':
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

    def toggle_press_callback(self, button):
        '''callback function for edit/save button'''
        if button == self.btnSaveEdit:
            if button.state == 'down':
                self.editMode = True
                button.source = 'images/databaseview/btn_save_change.png'
            else:
                self.editMode = False
                button.source = 'images/databaseview/btn_edit.png'
                # Trigger saving to database
                self.save_change_to_db()

    def button_press_callback(self, widget):
        if widget == self.btnRemove:
            widget.source = 'images/databaseview/btn_remove_down.png'

    def button_release_callback(self, widget):
        if widget == self.btnRemove:
            widget.source = 'images/databaseview/btn_remove.png'
            self.remove_from_db(self.id)