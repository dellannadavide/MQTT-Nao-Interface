# from random import random
import math

import utils.util
import utils.constants as Constants
from sensors.sensor import Sensor
import random
import numpy as np
import csv

class DistanceDetectorSim(Sensor):
    def __init__(self, nao_interface, id, mqtt_topic, freq, qi_app=None, ds=None):
        super(DistanceDetectorSim, self).__init__(nao_interface, id, mqtt_topic, [], freq, qi_app)
        self.curr_step = 0
        self.ds = []
        ds_reader = csv.reader(open(ds, "rb"))
        next(ds_reader)
        for row in ds_reader:
            self.ds.append(row)


    def sense(self):
        if self.curr_step < len(self.ds):
            curr_row = self.ds[self.curr_step]
            #curr_row[0] is society
            message = utils.util.joinStrings([curr_row[2], #x
                                           curr_row[3], #y
                                           curr_row[4] #d
                                           ]
                                             )
            self.curr_step=self.curr_step+1

            print("distance detect: "+str(message))


            return message
        else:
            return None
