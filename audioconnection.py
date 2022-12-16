import sounddevice as sd
import socket
import requests
import numpy as np
from urllib.parse import urlparse

class AudioReceiver():

    stream = None
    deviceUrl = ''
    inSocket = None
    inFile = None
    # Audio sampling freq
    fs = 44100

    def __init__(self, deviceUrl, devicePort = 65001) -> None:
        self.stream = sd.OutputStream(callback = self.stream_callback, samplerate = self.fs, channels = 1, blocksize=1024)
        self.deviceUrl = deviceUrl
        # Parsing ip address
        deviceIP = urlparse(self.deviceUrl)[1][:-5]
        self.remoteAddress = (deviceIP, devicePort)

    def connect(self):
        # Initiate connection
        try:
            r = requests.get(self.deviceUrl+"?audioin=1")
            self.inSocket = socket.socket()
            self.inSocket.settimeout(10)
            self.inSocket.connect(self.remoteAddress)
            print ('inSocket connected')
            self.inFile = self.inSocket.makefile('rb')
            return True
        except Exception as e:
            print (f'inSocket connection error: {e}')
            return False

    def stream_callback(self, outdata, nsample, time, status):
        if self.inFile:
            try:
                sockData = self.inFile.read(4096)
                temp = np.frombuffer(sockData, dtype=np.float32)
                temp = np.reshape(temp, (1024,1))
                outdata[:1024] = temp
            except Exception as e:
                print(e)
                self.stop_stream()
        else:
            print ('no sockfile')

    def start_stream(self):
        if self.connect():
            self.stream.start()
        else:
            print ('Unable to connect. Stream not started')

    def stop_stream(self):
        self.stream.stop()
        self.stream.close()
        self.inSocket.close()
        self.inFile.close()


class AudioTransmitter():

    stream = None
    deviceUrl = ''
    outSocket = None
    outFile = None
    # Audio sampling freq
    fs = 44100

    def __init__(self, deviceUrl, devicePort = 65002) -> None:
        self.stream = sd.InputStream(callback = self.stream_callback, samplerate = self.fs, channels = 1, blocksize=1024)
        self.deviceUrl = deviceUrl
        # Parsing ip address
        deviceIP = urlparse(self.deviceUrl)[1][:-5]
        self.remoteAddress = (deviceIP, devicePort)

    def connect(self):
        # Initiate connection
        try:
            r = requests.get(self.deviceUrl+"?audioout=1")
            self.outSocket = socket.socket()
            self.outSocket.settimeout(10)
            self.outSocket.connect(self.remoteAddress)
            print ('outSocket connected')
            self.outFile = self.outSocket.makefile('wb')
            return True
        except Exception as e:
            print (f'outSocket connection error: {e}')
            return False

    def stream_callback(self, indata, nsample, time, status):
        if self.outFile:
            try:
                self.outFile.write(indata.tobytes())
            except Exception as e:
                print(e)
                self.stop_stream()
        else:
            print ('no sockfile')

    def start_stream(self):
        if self.connect():
            self.stream.start()
        else:
            print ('Unable to connect. Stream not started')

    def stop_stream(self):
        self.stream.stop()
        self.stream.close()
        self.outSocket.close()
        self.outFile.close()