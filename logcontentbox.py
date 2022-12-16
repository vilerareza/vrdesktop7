import io
from threading import Thread
import pickle
import base64
import socket
import time
from dateutil.parser import isoparse
from functools import partial

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.stacklayout import StackLayout
from kivy.uix.behaviors.compoundselection import CompoundSelectionBehavior
from kivy.uix.behaviors import FocusBehavior
from kivy.core.image import Image as CoreImage
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock

from logfaceitem import LogFaceItem

import requests
import numpy as np
from cv2 import imencode, imdecode, rectangle

import datetime

Builder.load_file('logcontentbox.kv')

class LogContentBox(BoxLayout):

    manager = ObjectProperty(None)
    detectionLog = None
    logFaceLayout = ObjectProperty(None)
    logFrameLayout = ObjectProperty(None)
    isServerTimeout = False
    stopFlag = False

    def __init__(self, server_address_file='data/serveraddress.p', **kwargs):
        super().__init__(**kwargs)
        # Getting the server adrress, deserialize the serveraddress.p
        self.serverAddressFile = server_address_file

    def display_detection_log(self, face_id):
        # Clearing layout
        self.clear_images()
        # Getting server address
        serverIP, serverName = self.get_server_address()
        # Show popup message
        self.manager.open_popup(self)
        self.manager.popup.title = 'Getting Log from Server...'
        # Get detection log form the server
        self.get_detection_log(face_id, serverIP, serverName)

    def clear_images(self):
        '''Clearing images in layouts'''
        layouts = [self.logFaceLayout, self.logFrameLayout]
        for layout in layouts:
            layout.clear_widgets()

    def get_detection_log(self, face_id, server_ip, server_name):
        '''Get detection log for respective face_id'''

        def _send_request():
            '''Thread function tp get face IDs'''
            isSuccess = True
            # Resetting the stop flag
            self.stopFlag = False
            '''Send request to the server to get log for given face IDs'''
            isSuccess, r = self.send_request_get(server_ip, server_name, 8000, f'api/log/faceid/{face_id}/', 5)
            # Sending request complete. Run callback function
            Clock.schedule_once(partial(callback, isSuccess, r), 0)

        def callback(isSuccess, r, *args):
            # Getting and parsing response
            if isSuccess:
                log_response = r.json()  # Produce list of dict
                self.show_detection_face(self.logFaceLayout, log_response)
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
                    print ('Get logs cancelled')
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


    def show_detection_face(self, widget, detection_log):
        '''Display detection face in the widget'''
        for log in detection_log:
            logID = log['id']
            timeStamp = isoparse(log['timeStamp'])
            faceDataStr = log['faceData']
            faceDataNp = pickle.loads(base64.b64decode(faceDataStr))
            _, faceDataBytes = imencode(".jpg", faceDataNp)
            frameID = log['frameID']
            # Bounding box property (numpy)
            bbox = pickle.loads(base64.b64decode(log['bbox']))
            coreImg = CoreImage(io.BytesIO(faceDataBytes), ext = 'jpg')
            widget.add_widget(LogFaceItem(
                log_id = logID, 
                time_stamp = timeStamp, 
                face_texture = coreImg.texture, 
                frame_id = frameID, 
                bbox = bbox
                )
            )

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

class LogFaceGrid (FocusBehavior, CompoundSelectionBehavior, GridLayout):
    '''Grid layout for displaying face log content'''
    myRoot = ObjectProperty(None)
    frameLayout = ObjectProperty(None)
    selectedData = ObjectProperty(None)

    def __init__(self, server_address_file='data/serveraddress.p', **kwargs):
        super().__init__(**kwargs)
        # Getting the server adrress, deserialize the serveraddress.p
        self.serverAddressFile = server_address_file
        self.bind(selectedData = self.show_frame)

    def show_frame(self, *args):
        '''display corresponding frame in frameLayout'''
        if self.frameLayout:
            frameData = self.get_frame_data(self.selectedData.frameID)
            bbox = self.selectedData.bbox
            try:
                frameTexture = self.create_frame_texture(frameData, bbox)
                # Prepare image widget
                frameWidget = Image(
                    size_hint = (0.9, 0.9), 
                    pos_hint = {'center_x' : 0.5, 'center_y' : 0.5},
                    texture = frameTexture
                )
                # Show the image widget in frameLayout
                self.frameLayout.add_widget(frameWidget)
            except Exception as e:
                print (f'Cannot display frame image: {e}')

    def get_frame_data (self, frame_id):
        '''Sending request for frame'''
        serverIP, serverName = self.myRoot.get_server_address()
        isSuccess, r = self.myRoot.send_request_get(serverIP, serverName, 8000, f'api/log/frame/{frame_id}/', 5)
        #r = requests.get(f"http://{serverAddress}/api/log/frame/{frame_id}/")
        if isSuccess:
            frameData = r.json()['frameData']
            return frameData
        else:
            return None

    def create_frame_texture(self, frame_data, bbox):
        '''Creating kivy image texture from from frame string data'''
        faceDataBytes = base64.b64decode(frame_data)
        # Conversion to np array
        buff = np.asarray(bytearray(faceDataBytes))
        img = imdecode(buff, 1)
        # Draw bounding box
        xb, yb, widthb, heightb = bbox
        rectangle(img, (xb, yb), (xb+widthb, yb+heightb), color = (232,164,0), thickness = 3)
        # Returning bytes data
        _, img_bytes = imencode(".jpg", img)
        # Creating core image and return its texture
        coreImg = CoreImage(io.BytesIO(img_bytes.tobytes()), ext = 'jpg')
        return coreImg.texture

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if super().keyboard_on_key_down(window, keycode, text, modifiers):
            return True
        if self.select_with_key_down(window, keycode, text, modifiers):
            return True
        return False

    def keyboard_on_key_up(self, window, keycode):
        if super().keyboard_on_key_up(window, keycode):
            return True
        if self.select_with_key_up(window, keycode):
            return True
        return False

    def add_widget(self, widget):
        super().add_widget(widget)
        widget.bind(on_touch_down = self.widget_touch_down, on_touch_up = self.widget_touch_up)
    
    def widget_touch_down(self, widget, touch):
        if widget.collide_point(*touch.pos):
            self.select_with_touch(widget, touch)
    
    def widget_touch_up(self, widget, touch):
        if self.collide_point(*touch.pos) and (not (widget.collide_point(*touch.pos) or self.touch_multiselect)):
            self.deselect_node(widget)
    
    def select_node(self, node):
        node.backgroundImage.source = 'images/logview/faceitem_down.png'
        self.selectedData = node
        return super().select_node(node)
        
    def deselect_node(self, node):
        super().deselect_node(node)
        node.backgroundImage.source = 'images/logview/faceitem_normal.png'
    
    def clear_selection(self, widget=None):
        return super().clear_selection()

    def on_selected_nodes(self,grid,nodes):
        pass

