import random
from statistics import mean

import pyaudio
import speech_recognition as sr

from sensors.sensor import Sensor
import utils.constants as Constants

import time

class MicEnergyDetector(Sensor):
    def __init__(self, nao_interface, id, mqtt_topic, freq, qi_app=None):
        super(MicEnergyDetector, self).__init__(nao_interface, id, mqtt_topic, [Constants.NAO_SERVICE_AUDIO], freq, qi_app)
        self.detected_front = []
        self.detected_left = []
        self.detected_right = []
        self.detected_rear = []
        self.collect = False

        t_end = time.time() + 5
        audio = self.services[Constants.NAO_SERVICE_AUDIO]
        self.collect = True
        while time.time() < t_end:
            self.detected_front.append(audio.getFrontMicEnergy())
            self.detected_left.append(audio.getLeftMicEnergy())
            self.detected_right.append(audio.getRightMicEnergy())
            self.detected_rear.append(audio.getRearMicEnergy())
        self.collect = False

        self.baseline_front = mean(self.detected_front)
        self.baseline_left = mean(self.detected_left)
        self.baseline_right = mean(self.detected_right)
        self.baseline_rear = mean(self.detected_rear)



    def sense(self):
        try:
            if self.collect:
                audio = self.services[Constants.NAO_SERVICE_AUDIO]
                self.detected_front.append(audio.getFrontMicEnergy()-self.baseline_front)
                self.detected_left.append(audio.getLeftMicEnergy()-self.baseline_left)
                self.detected_right.append(audio.getRightMicEnergy()-self.baseline_right)
                self.detected_rear.append(audio.getRearMicEnergy()-self.baseline_rear)
            return None
        except:
            return None

    def collectEnergyLevels(self):
        self.detected_front = []
        self.detected_left = []
        self.detected_right = []
        self.detected_rear = []
        self.collect = True


    def getSource(self):
        self.collect = False
        avg_vals = {
            "Front": 0.0 if len(self.detected_front)==0 else max(self.detected_front),
            "Left": 0.0 if len(self.detected_left)==0 else max(self.detected_left),
            "Right": 0.0 if len(self.detected_right)==0 else max(self.detected_right),
            "Rear": 0.0 if len(self.detected_rear)==0 else max(self.detected_rear)
        }
        return max(avg_vals, key=avg_vals.get)

