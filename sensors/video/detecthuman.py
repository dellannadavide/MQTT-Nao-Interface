#! /usr/bin/env python
# -*- encoding: UTF-8 -*-

"""Example: A Simple class to get & read FaceDetected Events"""
from datetime import datetime

import qi
import time
import sys
import argparse


import paho.mqtt.client as mqtt
from random import randrange, uniform
import time

import utils.constants as Constants
import utils.util
from sensors.sensor import Sensor
from utils.mqttclient import MQTTClient

import logging
logger = logging.getLogger("mqtt-nao-interface.sensors.video.detecthuman")

class HumanDetector(Sensor):
    """
    A simple class to react to face detection events.
    """

    def __init__(self, nao_interface, id, mqtt_topic, freq, qi_app=None):
        super(HumanDetector, self).__init__(nao_interface, id, mqtt_topic, [Constants.NAO_SERVICE_MEMORY,
                                                             Constants.NAO_SERVICE_FACEDETECTION], freq, qi_app)
        self.subscribeToServices()

        self.got_faces = False
        self.faces = []
        self.last_seen = ""



    def subscribeToServices(self):
        self.subscriber = self.services[Constants.NAO_SERVICE_MEMORY].subscriber(Constants.NAO_EVENT_FACEDETECTED)
        self.subscriber.signal.connect(self.on_human_tracked)
        self.subscribe(Constants.NAO_SERVICE_FACEDETECTION, self.id)


    def sense(self):
        logger.info("faces: {}".format(self.faces))
        if len(self.faces)>0:
            to_ret = utils.util.joinStrings(self.faces)
            logger.info(to_ret)
            if not self.last_seen == to_ret:
                self.last_seen = to_ret
                # to_ret = str(self.faces)
                self.faces = []
                self.got_faces = False
                return to_ret
            else:
                return None
        else:
            return None

    def on_human_tracked(self, value):
        # print("human tracked")
        """
        Callback for event FaceDetected.
        """
        if value == []:  # empty value when the face disappears
            self.got_faces = False
            self.faces = []
        elif not self.got_faces:
            timeStamp = value[0]
            # print "TimeStamp is: " + str(timeStamp)
            # Second Field = array of face_Info's.
            faceInfoArray = value[1]
            for j in range( len(faceInfoArray)-1 ):
                faceInfo = faceInfoArray[j]
                # First Field = Shape info.
                faceShapeInfo = faceInfo[0]
                # Second Field = Extra info (empty for now).
                faceExtraInfo = faceInfo[1]
                # print "Face Infos :  alpha %.3f - beta %.3f" % (faceShapeInfo[1], faceShapeInfo[2])
                # print "Face Infos :  width %.3f - height %.3f" % (faceShapeInfo[3], faceShapeInfo[4])
                # print "Face Extra Infos :" + str(faceExtraInfo)
                self.timeFilteredResult = value[1][len(value[1]) - 1]
                if (len(self.timeFilteredResult) == 1):
                    # If a face has been detected for more than 8s but not recognized
                    if (self.timeFilteredResult[0] == 4):
                        # self.onDetectWithoutReco()
                        # print("unknown")
                        self.got_faces = True
                        self.faces.append("unknown")
                        logger.info("detected unknown")
                elif (len(self.timeFilteredResult) == 2):
                    # If one or several faces have been recognized
                    if (self.timeFilteredResult[0] in [2, 3]):
                        for s in self.timeFilteredResult[1]:
                            # self.onRecognizedFace(s)
                            # print(s)
                            self.got_faces = True
                            self.faces.append(s)
                            logger.info("detected "+str(s))