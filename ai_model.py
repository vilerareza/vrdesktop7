import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from tensorflow.keras import models
import numpy as np

from cv2 import imread, resize
import numpy as np

class AIModel():

    detector1 = None
    detector2 = None
    classifier = None
    classes = None
    modelLocation = '' #"E:/testimages/facetest/vggface/ir/saved_model.xml"
    ieModelProperties = []

    def __init__(self, recognition = False, model_location = '', classes_location = ''):
        
        # Face detector 1 (haarcascade)
        from cv2 import CascadeClassifier
        self.detector1 = CascadeClassifier("haarcascade_frontalface_default.xml")
        # Face detector 2 (mtcnn)
        from mtcnn.mtcnn import MTCNN
        self.detector2 = MTCNN()

        # Classifier
        if recognition:
            self.modelLocation = model_location
            if model_location != '':
                # Use regular tf / keras model
                self.classifier = models.load_model(self.modelLocation)
            else:
                print ('Model location is not set')
        
        if classes_location != '':
            try:
                self.classes = np.load(classes_location)
            except Exception as e:
                print (f'{e}: Failed loading classes')
                self.classes = None
    
    def detect_faces(self, detector_type, img):
        # Check type of detector
        if detector_type == 1:
            detector = self.detector1
        elif detector_type == 2:
            detector = self.detector2

        if detector == self.detector1:
            # Haarcascade detector perform here
            bboxes = detector.detectMultiScale(img)
            if (len(bboxes)>0):
                # Face detected
                print ('Detector 1: Face detected')
                return bboxes, img
            else:
                return [], img

        elif detector == self.detector2:
            # MTCNN detector perform here
            detection = detector.detect_faces(img)
            if (len(detection)>0):
                print ('Detector 2: Face detected')
                bboxes = []
                for dict in detection:
                    bboxes.append(dict['box'])
                return bboxes, img
            else:
                return [], img

    def extract_faces(self, detector_type, img, target_size = (224,224)):
        # Detect faces and get bounding boxes
        bboxes, img = self.detect_faces(detector_type, img)
        if np.any(bboxes):
            faces = []
            for box in bboxes:
                x1, y1, width, height = box
                x2, y2 = x1 + width, y1 + height
                # face data array
                face = img[y1:y2, x1:x2]
                # Resizing
                factor_y = target_size[0] / face.shape[0]
                factor_x = target_size[1] / face.shape[1]
                factor = min (factor_x, factor_y)
                face_resized = resize(face, (int(face.shape[0]* factor), int(face.shape[1]*factor)))
                diff_y = target_size[0] - face_resized.shape[0]
                diff_x = target_size[1] - face_resized.shape[1]
                # Padding
                face_resized = np.pad(face_resized,((diff_y//2, diff_y - diff_y//2), (diff_x//2, diff_x-diff_x//2), (0,0)), 'constant')
                faces.append(face_resized)
            return bboxes, faces
        return [], []

    def extract_primary_face(self, detector_type, image_path, target_size = (224,224)):
        # Detection
        img, box = self.detect_primary_face_from_file(detector_type, image_path)
        if np.any(box):
            x1, y1, width, height = box
            x2, y2 = x1 + width, y1 + height
            # face data array
            face = img[y1:y2, x1:x2]
            # Resizing
            factor_y = target_size[0] / face.shape[0]
            factor_x = target_size[1] / face.shape[1]
            factor = min (factor_x, factor_y)
            face_resized = resize(face, (int(face.shape[0]* factor), int(face.shape[1]*factor)))
            diff_y = target_size[0] - face_resized.shape[0]
            diff_x = target_size[1] - face_resized.shape[1]
            # Padding
            face_resized = np.pad(face_resized,((diff_y//2, diff_y - diff_y//2), (diff_x//2, diff_x-diff_x//2), (0,0)), 'constant')
            # Progress
            return face_resized
        return None

    def detect_primary_face_from_file(self, detector_type, image_path):
        # Check type of detector
        if detector_type == 1:
            detector = self.detector1
        elif detector_type == 2:
            detector = self.detector2

        img = imread(image_path)

        if detector == self.detector1:
            # Haarcascade detector perform here
            img = imread(image_path)
            bboxes = detector.detectMultiScale(img)
            if (len(bboxes)>0):
                # Face detected
                print ('Detector 1: Face detected')
                box = bboxes[0]
                return img, box
            else:
                return img, []

        elif detector == self.detector2:
            # Haarcascade detector perform here
            detection = detector.detect_faces(img)
            if (len(detection)>0):
                print ('Detector 2: Face detected')
                box = detection[0]['box']
                return img, box
            else:
                return img, []

    def create_face_vectors(self, face_list):
        # Create face vectors numpy array from list of face data
        if self.classifier:
            face_vectors = []
            for face in face_list.copy():
                face = np.expand_dims(face, axis=0)
                face = face/255
                # Predict vector
                vector = self.classifier.predict(face)[0]
                face_vectors.append(vector)
            face_vectors = np.array(face_vectors)
            return face_vectors
        else:
            print ('No classifier, face vector not created')
            return []

    def create_mean_face_vector(self, face_list):
        # Create mean face vector numpy array from list of face data
        if self.classifier:
            face_vector = []
            for face in face_list.copy():
                face = np.expand_dims(face, axis=0)
                face = face/255
                #face = np.moveaxis(face, -1, 1)
                print (f'face shape: {face.shape}')
                # Predict vector
                vector = self.classifier.predict(face)[0]
                face_vector.append(vector)
            face_vector = np.array(face_vector)
            face_vector = np.mean(face_vector, axis = 0)
            print (f'face_vector shape: {face_vector.shape}')
            return face_vector
        else:
            print ('No classifier, mean face vector not created')
            return []