import io
import os
import gc
import time
from datetime import datetime
from functools import partial
from threading import Thread, Condition

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.behaviors.hover_behavior import HoverBehavior
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.graphics.texture import Texture
from kivy.core.image import Image as CoreImage

from tkinter import Tk, filedialog

from audioconnection import AudioReceiver, AudioTransmitter
from mylayoutwidgets import ColorFloatLayout

from livestream import LiveStream
from rectransferbox import RecTransferBox

import numpy as np
import websocket
import json
import base64


Builder.load_file('livebox.kv')


class LiveBox(MDFloatLayout, HoverBehavior):

    manager = ObjectProperty(None)
    closeMe = ObjectProperty(None)
    liveStream = ObjectProperty(None)
    liveActionBar = ObjectProperty(None)
    moveLeft = ObjectProperty(None)
    moveRight = ObjectProperty(None)
    moveUp = ObjectProperty(None)
    moveDown = ObjectProperty(None)
    status = StringProperty("stop")
    moveEvent = None
    # Websockets
    wst = None
    wst_control = None
    # Stream monitor
    streamMon = None
    # Movement
    controlsEnabled = True
    moveRepetitionSec = 0.3
    moveDistance = 10
    # servo parameter
    servo_center_pos = 7
    servo_max_move = 1.7
    # Audio object
    audioReceiver = None
    audioTransmitter = None
    # Stop flag
    stop_flag = False
    # Device IP
    deviceIP = ''
    # Recording files from camera
    rec_files = {}
    rec_val_dates = {}
    dir_to_save_rec = ''
    rec_to_download = []
    download_ctr = 0


    def __init__(self, device_name = '', **kwargs):
        super().__init__(**kwargs)
        self.deviceName = device_name
        self.condition = Condition()
        
    def on_enter(self, *args):
        self.show_controls()

    def on_leave(self, *args):
        self.hide_controls()

    def update_frame(self, coreImg, *largs):
        ## Update the livestream texture with new frame
        self.liveStream.texture = coreImg.texture
        self.liveStream.canvas.ask_update()
        # Notify the stream monitor
        with self.condition:
            self.condition.notify_all()

    def on_frame_(self, wsapp, message):
        ### When frame data is received form server
        #### Create the CoreImage object
        coreImg = CoreImage(io.BytesIO(message), ext = 'jpg')
        #### Update the livestream texture with new frame
        Clock.schedule_once(partial(self.update_frame, coreImg), 0)
    

    def start_live_stream (self, deviceIP):
        # Start the live stream (Image object)

        self.deviceIP = deviceIP
        
        def monitor_stream():
            # Create the monitor function
            while (not self.stop_flag):
                with self.condition:
                    if not (self.condition.wait(timeout = 5)):
                        print ('stream monitor timeout')

        try:
            # Create the websocket connection to camera
            self.wsapp = websocket.WebSocketApp(f"ws://{deviceIP}:8000/frame/", on_message=self.on_frame_)
            self.wsapp_control = websocket.WebSocketApp(f"ws://{deviceIP}:8000/control/", on_message=self.on_control_response)

            def run():
                # Start the websocket connection
                time.sleep(0.3) # Without this delay the websocket callback will not run
                self.wsapp.run_forever()

            def run_control():
                # Start the websocket connection
                time.sleep(0.3) # Without this delay the websocket callback will not run
                self.wsapp_control.run_forever()

            # Re-init the texture of the liveStream object
            self.liveStream.texture = Texture.create()

            # Start the websocket connection in new thread
            self.wst = Thread(target = run)
            self.wst_control = Thread(target = run_control)
            self.wst.daemon = True
            self.wst.start()
            self.wst_control.daemon = True
            self.wst_control.start()
            # Start the monitor function in new thread
            #self.streamMon = Thread(target = monitor_stream)
            #self.streamMon.daemon = True
            #self.streamMon.start()
            # Change the status
            self.status = "play"
        except Exception as e:
            print (f'{e}: Failed starting websocket connection')
            self.wst = None
            self.wst_control = None
            # Close the websocket connection
            self.stop_websockets()


    def stop_websockets(self):
        try:
            self.wsapp.close()
            self.wsapp_control.close()
            self.wsapp_download.close()
        except:
            pass


    def stop_live_stream (self):
        try:  
            # Stopping the audio stream anyway
            self.stop_audio_in()
            self.stop_audio_out()
            # Reset the live action bar button state
            self.liveActionBar.reset()
            # Close the websocket connection
            self.stop_websockets()
            # If websocket thread exist
            if self.wst:
                self.wst.join()  
            if self.wst_control:
                self.wst_control.join()  
            if self.streamMon:
                with self.condition:
                    self.condition.notify_all()
                    self.streamMon.join()
            # Change status
            self.status = "stop"
        except Exception as e:
            print ("Error to stop live stream...")
            print (e)
            self.status = "stop"


    def adjust_self_size(self, size):
        self.size = size
        self.adjust_livestream_size(size)


    def adjust_livestream_size(self, size):
        factor1 = size[0] / self.liveStream.width
        factor2 = size[1] / self.liveStream.height
        factor = min(factor1, factor2)
        target_size = ((self.liveStream.width * factor), (self.liveStream.height * factor))
        self.liveStream.size = target_size     


    def capture_image(self, file_name = ''):
        if file_name =='':
            self.liveStream.texture.save("test.png", flipped = False)


    def show_controls(self):
        self.liveActionBar.opacity  = 0.7
        self.moveLeft.opacity  = 0.7
        self.moveRight.opacity  = 0.7
        self.moveUp.opacity  = 0.7
        self.moveDown.opacity  = 0.7
        self.closeMe.opacity = 0.7

    def hide_controls(self):
        self.liveActionBar.opacity  = 0
        self.moveLeft.opacity  = 0
        self.moveRight.opacity  = 0
        self.moveUp.opacity  = 0
        self.moveDown.opacity  = 0
        self.closeMe.opacity = 0

    def reduce_action_control(self):
        # Disable some controls (audio and download) on live action bar
        self.liveActionBar.reduce_action_control()
    
    def restore_action_control(self):
        # Re-enable some controls (audio and download) on live action bar
        self.liveActionBar.restore_action_control()


    def button_touch_down(self, *args):

        # Movements
        if self.controlsEnabled:

            if args[0].collide_point(*args[1].pos):

                if args[0] == self.closeMe:
                    # Close button pressed. Change button appearance
                    args[0].source = 'images/multiview/close_down.png'

                elif args[0] == self.moveLeft:
                    # Move left
                    print ('touch down left')
                    if not self.moveEvent:
                        # Change button appearance
                        args[0].source = 'images/multiview/moveleft_down.png'
                        # Move once
                        self.start_move(dir = 'L', distance = self.moveDistance)
                        # Continue movement with interval if the button is still pressed
                        self.moveEvent = Clock.schedule_interval(partial(
                            self.start_move,
                            dir = 'L',
                            distance = self.moveDistance
                            ), self.moveRepetitionSec
                        )
                elif args[0] == self.moveRight:
                    # Move right
                    print ('touch down right')
                    if not self.moveEvent:
                        # Change button appearance
                        args[0].source = 'images/multiview/moveright_down.png'
                        # Move once
                        self.start_move(dir = 'R', distance = self.moveDistance)
                        # Continue movement with interval if the button is still pressed
                        self.moveEvent = Clock.schedule_interval(partial( 
                            self.start_move,
                            dir = 'R',
                            distance = self.moveDistance
                            ), self.moveRepetitionSec
                        )
                elif args[0] == self.moveUp:
                    # Move up
                    print ('touch down up')
                    if not self.moveEvent:
                        # Change button appearance
                        args[0].source = 'images/multiview/moveup_down.png'
                        # Move once
                        self.start_move(dir = 'U', distance = self.moveDistance)
                        # Continue movement with interval if the button is still pressed
                        self.moveEvent = Clock.schedule_interval(partial( 
                            self.start_move,
                            dir = 'U',
                            distance = self.moveDistance
                            ), self.moveRepetitionSec
                        )
                elif args[0] == self.moveDown:
                    # Move down
                    print ('touch down down')
                    if not self.moveEvent:
                        # Change button appearance
                        args[0].source = 'images/multiview/movedown_down.png'
                        # Move once
                        self.start_move(dir = 'D', distance = self.moveDistance)
                        # Continue movement with interval if the button is still pressed
                        self.moveEvent = Clock.schedule_interval(partial( 
                            self.start_move,
                            dir = 'D',
                            distance = self.moveDistance
                            ), self.moveRepetitionSec
                        )


    def button_touch_up(self, *args):

        # Movements
        if self.controlsEnabled:

            if args[0].collide_point(*args[1].pos):

                if args[0] == self.closeMe:
                    # Close button pressed. Change button appearance
                    args[0].source = 'images/multiview/close_normal.png'
                    self.manager.mainTabs.multiView.remove_live_box(liveBox = self)
                    return

                # Stop the movement / cancel the repetitive movement
                if self.moveEvent:
                    self.moveEvent.cancel()
                    self.moveEvent = None
                    # Return the movement control buttons appearance
                    self.moveLeft.source = 'images/multiview/moveleft_normal.png'
                    self.moveRight.source = 'images/multiview/moveright_normal.png'
                    self.moveUp.source = 'images/multiview/moveup_normal.png'
                    self.moveDown.source = 'images/multiview/movedown_normal.png'


    def start_move(self, clock = None, dir = 'C', distance = 0):
        if dir != 'L' and dir != 'R' and dir != 'U' and dir != 'D' and dir != 'C':
            print ('Direction not valid')
            return False
        def move(dir, distance):
            data = {'op': 'mv', 'dir':dir, 'dist':distance}
            try:
                self.wsapp_control.send(json.dumps(data))
                return True
            except Exception as e:
                print (f'{e}: Error sending move command to server')
                return False
        # Start the move thread
        Thread(target = partial(move, dir ,distance)).start()
 

    def on_touch_down(self, touch):
        super().on_touch_down(touch)

        # Movements
        if self.controlsEnabled:
            if self.liveStream.collide_point(*touch.pos) and not (
                self.moveLeft.collide_point(*touch.pos) or
                self.moveRight.collide_point(*touch.pos) or
                self.moveUp.collide_point(*touch.pos) or
                self.moveDown.collide_point(*touch.pos) or
                self.liveActionBar.collide_point(*touch.pos) or
                self.closeMe.collide_point(*touch.pos)):

                touchPos = (touch.pos[0]-self.liveStream.x, touch.pos[1]-self.liveStream.y)
                # Calculate move distance
                distance_x, distance_y = self.calculate_move_distance(touch_x = touchPos[0], touch_y = touchPos[1])

                if distance_x > 0.1:
                    # Touch is at left area
                    self.start_move(dir = 'L', distance = abs(distance_x))
                elif distance_x < -0.1:
                    # Touch is at right area
                    self.start_move(dir = 'R', distance = abs(distance_x))
                if distance_y > 0.1:
                    # Touch is at lower area
                    self.start_move(dir = 'D', distance = abs(distance_y))
                elif distance_y < -0.1:
                    # Touch is at upper area
                    self.start_move(dir = 'U', distance = abs(distance_y))

                print (f'touch pos: {touchPos}')


    def calculate_move_distance(self, touch_x=0, touch_y=0):
        distance_x = (((self.liveStream.center_x-self.liveStream.x) - touch_x)/(self.liveStream.center_x-self.liveStream.x)) * self.servo_max_move
        distance_y = (((self.liveStream.center_y-self.liveStream.y) - touch_y)/(self.liveStream.center_y-self.liveStream.y)) * self.servo_max_move
        #print (f'move distance: {distance}, center_x: {self.liveStream.center_x}, touch_x: {touch_x}')
        return distance_x, distance_y


    def start_audio_in(self):
        # Start audio_in
        audioinThread = Thread(target = self.audio_in)
        audioinThread.start()


    def audio_in(self):
        print ('audio_in')
        self.audioReceiver = AudioReceiver(self.deviceUrl, devicePort = 65001)
        self.audioReceiver.start_stream()


    def stop_audio_in(self):
        if self.audioReceiver:
            self.audioReceiver.stop_stream()
            self.audioReceiver = None


    def start_audio_out(self):
        # Start audio_out
        audiooutThread = Thread(target = self.audio_out)
        audiooutThread.start()


    def audio_out(self):
        print ('audio_out')
        self.audioTransmitter = AudioTransmitter(self.deviceUrl, devicePort = 65002)
        self.audioTransmitter.start_stream()


    def stop_audio_out(self):
        if self.audioTransmitter:
            self.audioTransmitter.stop_stream()
            self.audioTransmitter = None


    def light(self, on = False):
        # Control the camera illumination

        def light_on():
            data = {'op': 'lt', 'on' : on}
            try:
                self.wsapp_control.send(json.dumps(data))
                return True
            except Exception as e:
                print (f'{e}: Error sending light command to camera')
                return False
        
        # Start the light thread
        Thread(target = light_on).start()
    

    def start_stop_cam(self, start=False):
        # Send start or stop command to camera

        def __start_stop_cam():

            data = {'op': 'st', 'start': start}
            try:
                self.wsapp_control.send(json.dumps(data))
                return True
            except Exception as e:
                print (f'{e}: Error start / stop command to camera')
                return False
        
        if not start:
            # Stop the camera            

            # Send stop command to camera
            __start_stop_cam()
            # Close existing frame websocket
            self.wsapp.close()
            # Show recording transfer dialog
            self.recTransferBox = RecTransferBox()
            self.add_widget(self.recTransferBox)
            self.disable_controls()

            try:
                # Create new websocket connection to camera for file download
                self.wsapp_download = websocket.WebSocketApp(f"ws://{self.deviceIP}:8000/download/", on_message=self.on_download)

                def run_ws_download():
                    # Start the websocket connection
                    time.sleep(0.3) # Without this delay the websocket callback will not run
                    self.wsapp_download.run_forever()

                self.wst_download = Thread(target = run_ws_download)
                self.wst_download.daemon = True
                self.wst_download.start()

            except Exception as e:
                print (f'{e}: Failed starting download websocket connection')
                self.wst_download = None
                del self.wst_download
                gc.collect()
        
        else:
            # Re-start the camera
            
            try:
                # Create the new frame websocket connection to camera
                self.wsapp = websocket.WebSocketApp(f"ws://{self.deviceIP}:8000/frame/", on_message=self.on_frame_)

                def run():
                    # Start the websocket connection
                    time.sleep(0.3) # Without this delay the websocket callback will not run
                    self.wsapp.run_forever()

                # Start the websocket connection in new thread
                self.wst = Thread(target = run)
                self.wst.daemon = True
                self.wst.start()
                # Change the status
                self.status = "play"

            except Exception as e:
                print (f'{e}: Failed starting websocket connection')
                self.wst = None
                del self.wst_download
                gc.collect()
                # Close the websocket connection
                self.stop_websockets()
            

    def get_rec_info(self):

        # Get rec file info from camera based on date and time
        data = {'op': 'rec_info'}

        try:
            self.wsapp_control.send(json.dumps(data))
            return True
        except Exception as e:
            print (f'{e}: Error getting rec file info from camera')
            return False


    def download_rec(self, date_, time_):
        # Download recording files from camera

        def __show_save_dialog():
            
            dirname = ''
            root = Tk()
            root.withdraw()
            dirname = filedialog.askdirectory()
            root.destroy()
            return dirname

        # Open directory selection dalog
        self.dir_to_save_rec = __show_save_dialog()

        if self.dir_to_save_rec != '':

            # Get path of files to download
            self.rec_to_download = self.get_rec_to_download(date_, time_)
            print (f'rec files to down: {self.rec_to_download}')

            try:
                # Create new websocket connection to camera for file download
                # self.wsapp_download = websocket.WebSocket()
                # self.wsapp_download.connect(f'ws://{self.deviceIP}:8000/download/{len(rec_to_download)}')
                
                # Sending download command via download websocket
                data = {'op': 'download', 'files': self.rec_to_download}
                self.wsapp_download.send(json.dumps(data))

                # Initialize download counter
                self.download_ctr = 1
                # Print download status info on rec transfer box
                self.recTransferBox.strStatus = f'Downloading 1 of {len(self.rec_to_download)}...'
                # for i in range(len(rec_to_download)):
                #     print ('receive something')
                #     message = self.wsapp_download.recv()
                #     message_json = json.loads(message)
                #     print (message_json['filename'])
                #     file_name = message_json['filename']
                #     file_bytes = base64.b64decode(message_json['filebytes'])
                #     with open (f'{file_name}', 'wb') as file:
                #         file.write(file_bytes)
                # self.wsapp_download.close()            
                return True
            
            except Exception as e:
                print (f'{e}: Error when downloading rec file from camera')
                return False


    def close_rec_dialog(self):
        # Closing the rec file download dialog

        try:
            # Close and remove websocket
            self.wsapp_download.close()
            self.wst_download = None
            del self.wst_download

        finally:
            # Remove rec dialog widget
            self.remove_widget(self.recTransferBox)
            self.recTransferBox = None
            del self.recTransferBox
            self.enable_controls()
            # Clearing list of recording files
            self.rec_files.clear()

            gc.collect()

            # Re-start the camera
            self.start_stop_cam(start=True)
        

    def get_rec_to_download(self, date_, time_):
        # Get rec files to download based on selected date and time
        
        try:

            year = date_.year
            month = date_.month
            day = date_.day
            hour = time_.hour

            # Compare selected date and time to elements in rec files dict

            # rec_to_download = []
            self.rec_to_download.clear()

            for file in self.rec_files.keys():
                # print (rec_files[file]['year'], rec_files[file]['month'], rec_files[file]['date'], rec_files[file]['hour'])
                if ((self.rec_files[file]['year']==year) and
                        (self.rec_files[file]['month']==month) and 
                        (self.rec_files[file]['date']==day) and 
                        (self.rec_files[file]['hour']==hour)):
                    
                    # Add the rec file path to list for download
                    self.rec_to_download.append(self.rec_files[file]['path'])
                
            return self.rec_to_download
        
        except:
            print ('not exist')
            return []


    def is_rec_exist(self, year, month, day, hour):
        # Get rec files to download based on selected date and time

        try:
            # Compare selected date and time to elements in rec files dict
            for file in self.rec_files.keys():
                if ((self.rec_files[file]['year']==year) and
                        (self.rec_files[file]['month']==month) and 
                        (self.rec_files[file]['date']==day) and 
                        (self.rec_files[file]['hour']==hour)):
                    print ('exist')
                    return True
                
            print ('not exist')
            return False
        
        except:
            print ('not exist')
            return False
        
    
    def on_control_response(self, wsapp, message):

        message_json = json.loads(message)
        
        if message_json['resp_type'] == 'rec_files':
            # If the response is JSON of recoding files

            # Extracting the year, month, date, hour and mins of rec files
            files = message_json['files']

            years=[];months=[];dates=[]
            
            for file in files:
                file_name = os.path.splitext(os.path.split(file)[-1])[0]
                year, month, date_, hour, min_, sec = file_name.split('_')
                year = int(year) ; month = int(month) ; date_ = int(date_) ; hour = int(hour) 
                years.append(int(year))
                months.append(int(month))
                dates.append(int(date_))

                self.rec_files[file_name]={'path':file, 'year':year, 'month': month, 'date': date_, 'hour': hour, 'min': min_}

            years = np.array(years)
            months = np.array(months)
            dates = np.array(dates)

            # Getting min and max value for year, month and date 
            self.rec_val_dates['year_min'] = years.min() ; self.rec_val_dates['year_max'] = years.max()
            self.rec_val_dates['month_min'] = months.min() ; self.rec_val_dates['month_max'] = months.max()
            self.rec_val_dates['date_min'] = dates.min() ; self.rec_val_dates['date_max'] = dates.max()

            # Check if the recording is exist for current time
            datetime_ = datetime.now()
            date_ = datetime_.date()
            time_ = datetime_.time()
            if (self.is_rec_exist(date_.year, date_.month, date_.day, time_.hour)):
                # Enable the download button on rec transfer dialog
                self.recTransferBox.btnDownload.disabled=False


    def on_download(self, wsapp, message):
        
        message_json = json.loads(message)
        print (f"Receiving {message_json['filename']}")
        file_name = message_json['filename']
        file_bytes = base64.b64decode(message_json['filebytes'])
        with open (f'{os.path.join(self.dir_to_save_rec, file_name)}', 'wb') as file:
            file.write(file_bytes)

        # Check if download is completed
        if self.download_ctr == len(self.rec_to_download) :
            # Download is complete if downnload counter is equal to number of file to download.
            self.recTransferBox.strStatus = 'Download Complete'
        else:
            # Continue downloading other file
            self.download_ctr += 1
            self.recTransferBox.strStatus = f'Downloading {self.download_ctr} of {len(self.rec_to_download)}...'


    def disable_controls(self):
        self.controlsEnabled = False
        self.liveActionBar.disabled = True
        
    def enable_controls(self):
        self.controlsEnabled = True
        self.liveActionBar.disabled = False