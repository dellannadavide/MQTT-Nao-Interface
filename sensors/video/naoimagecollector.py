from sensors.sensor import Sensor
import utils.constants as Constants
import cv2
import vision_definitions
from PIL import Image
import numpy as np

import logging
logger = logging.getLogger("mqtt-nao-interface.sensors.video.naoimagecollector")

class NaoImageCollector(Sensor):
    """ Collects frames from Camera """

    def __init__(self, nao_interface, id, mqtt_topic, freq, qi_app=None, virtual=False):
        super(NaoImageCollector, self).__init__(nao_interface, id, mqtt_topic, [Constants.NAO_SERVICE_VIDEO], freq, qi_app, virtual)

        self._imgClient = None


        if self.virtual:
            """ In case of virtual robot, it is assumed it can be used the camera of the laptop """
            self._cameraID = 0
            self.capture = cv2.VideoCapture(self._cameraID)
        else:
            self.resolution = vision_definitions.kQVGA#.k960p#.kQVGA  # 320 * 240
            self.colorSpace = vision_definitions.kRGBColorSpace

            self.fps = 5

            self.subscribeToServices()


        self.lastImage = None
        self.lastFrame = None
        self.lastFrame_gray = None
        self.updated = True

    def subscribeToServices(self):
        if not self._imgClient is None:
            self.services[Constants.NAO_SERVICE_VIDEO].unsubscribe(self._imgClient)
        self._imgClient = self.subscribe(Constants.NAO_SERVICE_VIDEO, "NaoImageCollector", self.resolution,
                                         self.colorSpace, self.fps)

    def prepareToEnd(self):
        super(NaoImageCollector, self).prepareToEnd()
        if self.virtual:
            self.capture.release()

    def sense(self):
        if self.virtual:
            ret, frame = self.capture.read()
            self.lastImage = frame
            self.lastFrame = frame
            self.lastFrame_gray = cv2.cvtColor(self.lastFrame, cv2.COLOR_BGR2GRAY)
        else:
            self.lastImage = self.services[Constants.NAO_SERVICE_VIDEO].getImageRemote(self._imgClient)
            imageWidth = self.lastImage[0]
            imageHeight = self.lastImage[1]
            array = self.lastImage[6]
            image_string = str(bytearray(array))
            pil_image = Image.frombytes("RGB", (imageWidth, imageHeight), image_string)
            open_cv_image = np.array(pil_image)
            # Convert RGB to BGR
            self.lastFrame = open_cv_image[:, :, ::-1].copy()
            self.lastFrame_gray = cv2.cvtColor(self.lastFrame, cv2.COLOR_BGR2GRAY)
        self.updated = True


        # print("image collected: ", self.lastFrame)

        return None

    def getLastFrame(self):
        if not self.updated:
            return None, None
        self.updated = False
        return self.lastFrame, self.lastFrame_gray

