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
logger = logging.getLogger("mqtt-nao-interface.sensors.video.detectobject")

class VisionRecognition(Sensor):
    """
    A simple class to react to object detection events.
    """

    def __init__(self, nao_interface, id, mqtt_topic, freq, qi_app=None):
        super(VisionRecognition, self).__init__(nao_interface, id, mqtt_topic, [Constants.NAO_SERVICE_MEMORY,
                                                             Constants.NAO_SERVICE_VISION_RECOGNITION], freq, qi_app)
        self.subscribeToServices()

        self.got_objects = False
        self.objects = []
        self.last_object = ""



    def subscribeToServices(self):
        self.subscriber = self.services[Constants.NAO_SERVICE_MEMORY].subscriber(Constants.NAO_EVENT_PICTURE_DETECTED)
        self.subscriber.signal.connect(self.on_picture_detected)
        self.subscribe(Constants.NAO_SERVICE_VISION_RECOGNITION, self.id)


    def sense(self):
        logger.info("objects: {}".format(self.objects))
        if len(self.objects)>0:
            to_ret = utils.util.joinStrings(self.objects)
            logger.info(to_ret)
            if not self.last_object == to_ret:
                self.last_object = to_ret
                # to_ret = str(self.faces)
                self.objects = []
                self.got_objects = False
                return to_ret
            else:
                return None
        else:
            return None

    def on_picture_detected(self, value):
        # print("human tracked")
        """
        Callback for event PictureDetected.
        """
        print(value)
        # if value == []:  # empty value when the object disappears
        #     # self.got_objects = False
        #     # self.objects = []
        # elif not self.got_objects:
        if not value==[]:
            # First Field is the timestamp
            timestamp = value[0]
            # Second Field is a list of recognized objects with their details.
            objects_info_array = value[1]
            """ For each object we have 
            [
              Label[N], # names given to the picture
              MatchedKeypoints, # number of keypoints retrieved in the current frame for the object
              Ratio, # number of keypoints retrieved in the current frame for the object divided by the number of keypoints found during the learning stage of the object.
              BoundaryPoint[N] # list of points coordinates in angle values (radian) representing the reprojection in the current image of the boundaries selected during the learning stage.
            ]
            """
            # print(objects_info_array)
            # print(len(objects_info_array))
            for j in range(len(objects_info_array)):
                object_info = objects_info_array[j]
                # First Field = Object labels.
                object_labels = object_info[0]
                main_label = object_labels[0]
                if main_label=="captain_hat_symbol":
                    main_label = "captain_hat"
                self.got_objects = True
                self.objects.append(main_label)
                logger.info("detected "+str(main_label))