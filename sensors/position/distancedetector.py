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
    def __init__(self, nao_interface, id, mqtt_topic, freq, qi_app=None, virtual=False):
        super(DistanceDetector, self).__init__(nao_interface, id, mqtt_topic, [Constants.NAO_SERVICE_MEMORY, Constants.NAO_SERVICE_SONAR], freq, qi_app, virtual)
        self.subscribeToServices()

        # self.services[Constants.NAO_SERVICE_SONAR].subscribe("DistanceDetector")


    def subscribeToServices(self):
        self.subscribe(Constants.NAO_SERVICE_SONAR, "DistanceDetector")

    def sense(self):
        # r = random.random()
        # r = 0.5
        # print(r)
        # message = utils.util.joinStrings([str(r)])
        # return message
        try:
            # Now you can retrieve sonar data from ALMemory. (distance in meters to the first obstacle).
            left = self.services[Constants.NAO_SERVICE_MEMORY].getData("Device/SubDeviceList/US/Left/Sensor/Value")
            # Same thing for right.
            right= self.services[Constants.NAO_SERVICE_MEMORY].getData("Device/SubDeviceList/US/Right/Sensor/Value")
            # print(left)
            # print(right)
            # avg_dist = (left+right)/2.0
            min_dist = min(left, right)
            # print("avg sonar distance: "+str(avg_dist))
            logger.info("min sonar distance: "+str(min_dist))
            message = utils.util.joinStrings([str(min_dist)])
            return message
        except:
            return None

