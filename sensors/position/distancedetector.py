# from random import random
import math

import utils.util
import utils.constants as Constants
from sensors.sensor import Sensor
import random
import numpy as np


import logging
logger = logging.getLogger("mqtt-nao-interface.sensors.position.distancedetector")

class DistanceDetector(Sensor):
    """ Distance Detector Sensor. It handles data coming from Nao's sonars sensors
        """
    def __init__(self, nao_interface, id, mqtt_topic, freq, qi_app=None, virtual=False):
        super(DistanceDetector, self).__init__(nao_interface, id, mqtt_topic, [Constants.NAO_SERVICE_MEMORY, Constants.NAO_SERVICE_SONAR], freq, qi_app, virtual)
        self.subscribeToServices()


    def subscribeToServices(self):
        self.subscribe(Constants.NAO_SERVICE_SONAR, "DistanceDetector")

    def sense(self):
        try:
            left = self.services[Constants.NAO_SERVICE_MEMORY].getData("Device/SubDeviceList/US/Left/Sensor/Value")
            right= self.services[Constants.NAO_SERVICE_MEMORY].getData("Device/SubDeviceList/US/Right/Sensor/Value")
            min_dist = min(left, right)
            logger.info("min sonar distance: "+str(min_dist))
            message = utils.util.joinStrings([str(min_dist)])
            return message
        except:
            return None

