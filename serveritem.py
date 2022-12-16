from threading import Thread
import time
import requests
import socket
import pickle

from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock

Builder.load_file("serveritem.kv")

class ServerItem(FloatLayout):
    serverImage = ObjectProperty(None)
    statusImage = ObjectProperty(None)
    serverAddressFile = ''
    serverName = ''
    serverIP = ''
    port = 8000
    t_check = 5
    stop_flag = False
        
    def __init__(self, server_address_file='data/serveraddress.p', **kwargs):
        super().__init__(**kwargs)
        try:
            self.serverAddressFile = server_address_file
            # Deserialize the server address
            with open(self.serverAddressFile, 'rb') as file:
                self.serverIP, self.serverName = pickle.load(file)
        except Exception as e:
            print(f'{e}: Failed loading server address: {e}')

    def update_server_addr(self, server_ip = '', server_name = ''):
        # Serialize server address to file
        self.serverIP = server_ip
        self.serverName = server_name
        server_address = [self.serverIP, self.serverName]
        try:
            with open(self.serverAddressFile, 'wb') as file:
                pickle.dump(server_address, file)
        except Exception as e:
            print (f'Saving server address failed: {e}')

    def send_request(self, server_ip, server_name, server_port, url, timeout = 3):
        try:
            # Try connecting using IP
            r = requests.get(f'http://{server_ip}:{server_port}/{url}', timeout = timeout)
            return True, r
        except:
            # Server IP maybe already changed. Try to find the new IP using server_name           
            for i in range(3):
                try:
                    if self.stop_flag:
                        break
                    # Try to get new IP
                    newIP = socket.gethostbyname(server_name)
                    # Try again using new IP
                    r = requests.get(f'http://{newIP}:{server_port}/{url}', timeout = timeout)
                    # Save new IP to file
                    self.update_server_addr(newIP, server_name)
                    return True, r
                except Exception as e:
                    print (f'{e}: Failed getting server ip. Retry {i+1}...')
                    time.sleep(3)
                    continue
            return False, None  

    def start_server_checker(self):
        # Start the status checker thread
        self.stop_flag=False

        def callback_ok(*args):
            self.statusImage.source = 'images/settingview/statusicon_active.png'
        
        def callback_fail(*args):
            self.statusImage.source = 'images/settingview/statusicon_inactive.png'

        def check():
            while (not self.stop_flag):
                # Loop check, if the application exit then break the loop
                isSuccess, r = self.send_request(self.serverIP, self.serverName, 8000, 'servercheck/', 5)
                if isSuccess:
                    # Connection ok
                    if r.status_code == 200 and r.text == 'ServerOk!':
                        Clock.schedule_once(callback_ok, 0)
                    else:
                        Clock.schedule_once(callback_fail, 0)
                else:
                    # Connection failed
                    Clock.schedule_once(callback_fail, 0)
                time.sleep(self.t_check)

        # Starting the server checker thread
        t = Thread(target = check)
        t.daemon = True
        t.start()

    def stop_server_checker(self):
        self.stop_flag=True



