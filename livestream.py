import io
import threading
import time
from datetime import datetime
import uuid
from functools import partial

import numpy as np
from cv2 import imdecode, imwrite

from kivy.lang import Builder
from kivy.graphics import Color, Line
from kivy.graphics.texture import Texture
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivy.uix.label import Label
from kivy.properties import ObjectProperty, BooleanProperty

Builder.load_file('livestream.kv')

class LiveStream(Image):

    manager = ObjectProperty(None)

    # Vision AI
    aiModel = None
    faceDatabase = None
    deviceName = ''

    processThisFrame = True
    t_process_frame = None
    bboxFactor = 0
    frameCount = 0
    streamSize = (1280, 720)
    faceDatabase = None
    faceDatabaseIDs = []
    faceDatabaseVectors = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nocache = BooleanProperty(True)
        self.state = "stop"
        self.device_name = ""
        self.server_address = ""

    # Video Frame Event Function
    def _on_video_frame(self, *largs):
        pass

    def process_frame(self, data):
        pass

    def print_id_distance(self, ids, distances):
        print (f'LEN IDS: {len(ids)}, LEN DISTANCES: {len(distances)}')
        for i in range(len(ids)):
            print (f'ID[{i}]: {ids[i]}, DISTANCE[{i}]: {distances[i]}')