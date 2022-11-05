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
import csv

class HumanDetectorSim(Sensor):
    """
    A simple class to react to face detection events.
    """

    def __init__(self, nao_interface, id, mqtt_topic, freq, qi_app=None, ds=None):
        super(HumanDetectorSim, self).__init__(nao_interface, id, mqtt_topic, [], freq, qi_app)
        self.curr_step = 0
        self.ds = []
        ds_reader = csv.reader(open(ds, "rb"))
        next(ds_reader)
        for row in ds_reader:
            self.ds.append(row)

    def sense(self):
        if self.curr_step < len(self.ds):
            curr_row = self.ds[self.curr_step]
            # curr_row[0] is society
            # curr_row[1] is person
            # person_id = curr_row[0] + "-" + curr_row[1]
            society_id = curr_row[0]
            person_id = curr_row[1]
            message = utils.util.joinStrings([society_id,
                                              person_id,
                                              curr_row[5]] #PERSON_NORM
                                             )

            self.curr_step = self.curr_step + 1

            print("human detect: "+str(message))

            return message
        else:
            return None