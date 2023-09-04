import threading
import socket
import time
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import ObjectProperty, StringProperty
from kivy.lang import Builder
from kivy.clock import Clock

Builder.load_file('deviceIcon.kv')


class DeviceIcon(ButtonBehavior, FloatLayout):

    statusImage = ObjectProperty(None)
    deviceName = StringProperty("")
    deviceLabel = ObjectProperty(None)
    t_status_checker = None
    stop_flag = False
    deviceIP = ''
    tCheck = 3
    isConnected = False

    def __init__(self, hostName, deviceName, **kwargs):
        super().__init__(**kwargs)
        #self.hostName = 'vr774c6498'
        self.hostName = hostName
        self.deviceName = deviceName
        self.condition = threading.Condition()
        self.disabled = True

    def get_device_ip(self):
        '''Get device ip address based on device hostname'''

        def callback_ok(*args):
            # Enable the item
            self.disabled = False
            self.isConnected = True
            self.statusImage.source = "images/multiview/standby.png"
            self.deviceLabel.text = "[color=cccccc]"+self.deviceName+"[/color]"
        
        def callback_fail(*args):
            # Disable the item
            self.disabled = False
            self.isConnected = False
            self.statusImage.source = "images/multiview/unavailable.png"
            self.deviceLabel.text = "[color=777777]"+self.deviceName+"[/color]"

        def _get_device_ip(): 
            
            for i in range(3):
                if not self.stop_flag:
                # Perform 3 times trial
                    try:
                        time.sleep(3)
                        self.deviceIP = socket.gethostbyname(self.hostName)
                        break
                    except Exception as e:
                        print (f'{e}: Failed getting server ip. Retry {i+1}...')
                        continue
            if self.deviceIP != '':
                Clock.schedule_once(callback_ok, 0)
            else:
                Clock.schedule_once(callback_fail, 0)

        self.disabled = True
        self.statusImage.source = "images/multiview/connecting.png"
        t_get_device_ip = threading.Thread(target = _get_device_ip)
        t_get_device_ip.daemon = True
        t_get_device_ip.start()

    def stop(self):
        self.stop_flag=True
