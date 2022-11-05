import random

import pyaudio
import speech_recognition as sr

from sensors.audio.mic import MicEnergyDetector
from sensors.sensor import Sensor
import utils.constants as Constants
import utils.util
import csv

class SpeechRecognizerSim(Sensor):
    def __init__(self, nao_interface, id, mqtt_topic, freq, qi_app=None, micenergy=None, ds=None):
        super(SpeechRecognizerSim, self).__init__(nao_interface, id, mqtt_topic, [], freq, qi_app)
        self.curr_step = 0
        self.ds = []
        ds_reader = csv.reader(open(ds, "rb"))
        next(ds_reader)
        for row in ds_reader:
            self.ds.append(row)

    def sense(self):
        if self.curr_step<len(self.ds):
            curr_row = self.ds[self.curr_step]
            # curr_row[0] is society
            message = utils.util.joinStrings([curr_row[6]]  # greets
                                             )
            self.curr_step = self.curr_step + 1

            print("speech recogn: "+str(message))

            return message
        else:
            return None
