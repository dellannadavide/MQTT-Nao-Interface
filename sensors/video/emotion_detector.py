import cv2
import numpy as np
import os
import bleedfacedetector as fd
import time

from sensors.sensor import Sensor
import utils.constants as Constants

import logging
logger = logging.getLogger("mqtt-nao-interface.sensors.video.emotion_detector")

class EmotionDetector(Sensor):
    """
        A simple class to compute data about face emotion
        """
    def __init__(self, nao_interface, id, mqtt_topic, freq, qi_app=None, virtual=False):
        super(EmotionDetector, self).__init__(nao_interface, id, mqtt_topic, [], freq, qi_app, virtual)
        # Set model path
        self.data_folder = "sensors/video/data/"
        self.model = self.data_folder+'emotion-ferplus-8.onnx'
        # Now read the model
        self.net = cv2.dnn.readNetFromONNX(self.model)

        self.emotions = ['Neutral', 'Happy', 'Surprised', 'Sad', 'Angry', 'Disgusted', 'Fearful', 'Contempt']

        self.lastImage = None

    def sense(self):
        self.lastImage, gray = self.nao_interface.services["NaoImageCollector"].getLastFrame()
        if not self.lastImage is None:
            # Use SSD detector with 20% confidence threshold.
            faces = fd.ssd_detect(self.lastImage, conf=0.2)
            if len(faces)>0:
                # Lets take the coordinates of the first face in the image.
                x, y, w, h = faces[0]
                # Define padding for face roi
                padding = 3
                # Extract the Face from image with padding.
                padded_face = self.lastImage[y - padding:y + h + padding, x - padding:x + w + padding]
                # # Non Padded face
                # face = img_copy[y:y + h, x:x + w]
                # Convert Image into Grayscale
                # gray = cv2.cvtColor(self.lastImage, cv2.COLOR_BGR2GRAY)
                # Resize into 64x64
                resized_face = cv2.resize(gray, (64, 64))
                # Reshape the image into required format for the model
                processed_face = resized_face.reshape(1, 1, 64, 64)
                self.net.setInput(processed_face)
                Output = self.net.forward()
                # Compute softmax values for each sets of scores
                expanded = np.exp(Output - np.max(Output))
                probablities = expanded / expanded.sum()
                # Get the final probablities
                prob = np.squeeze(probablities)
                # print(prob)
                # emotions list you created above.
                predicted_emotion = self.emotions[prob.argmax()].lower()
                # Print the target Emotion
                logger.info('Prob.: {}'.format(prob))
                logger.info('Predicted: {}'.format(predicted_emotion))
                if not predicted_emotion == "neutral":
                    return predicted_emotion
                else:
                    # logger.info('Emotion is: {}'.format(predicted_emotion))
                    return None
            else:
                return None
        else:
            return None


