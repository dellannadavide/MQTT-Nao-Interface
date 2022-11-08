import audioop
import random
import time
import traceback

import numpy as np
import pyaudio
import speech_recognition as sr

from sensors.audio.mic import MicEnergyDetector
from sensors.sensor import Sensor
import utils.constants as Constants
from utils.util import joinStrings

import logging
logger = logging.getLogger("mqtt-nao-interface.sensors.audio.speechrecognizer")

class SpeechRecognizer(Sensor):
    def __init__(self, nao_interface, id, mqtt_topic, freq, qi_app=None, micenergy=None, virtual=False):
        super(SpeechRecognizer, self).__init__(nao_interface, id, mqtt_topic, [], freq, qi_app, virtual)

        self.timeout = 10
        self.phrase_time_limit = 5

        p = pyaudio.PyAudio()
        # for i in range(p.get_device_count()):
        #     print(i)
        #     print p.get_device_info_by_index(i)

        self.r = sr.Recognizer()
        self.mic = sr.Microphone()
        if(p.get_device_count()>5):
            self.mic = sr.Microphone(2)
        with self.mic as source:
            self.r.adjust_for_ambient_noise(source)

        self.idx = 0

        self.micenergy = micenergy

    def sense(self):
        if self.nao_interface.is_speaking:
            logger.info("Nao is speaking, sleeping for 1 sec")
            time.sleep(1)
            return None
        try:
            with self.mic as source:
                if not self.micenergy is None:
                    self.micenergy.collectEnergyLevels()
                if self.idx>0:
                    logger.info("listening " + str(self.idx))
                self.idx = self.idx + 1
                if not self.virtual:
                    if self.idx > 0: #i skip the first green light so to avoid possible issues
                        self.nao_interface.services["LedsActuator"].setColor("green")
                audio = self.r.listen(source, timeout=self.timeout, phrase_time_limit=self.phrase_time_limit)
                if not self.virtual:
                    self.nao_interface.services["LedsActuator"].setColor("white")

        except Exception:
            logger.warning(traceback.format_exc())
            return None

        # if not self.micenergy is None:
        #     source_direction = self.micenergy.getSource()
        # else:
        #     source_direction = "Front"
            # audio = self.r.listen(source)
        # print(source_direction)
        # if source_direction=="Front":
        det = ""
        try:
            det = str(self.r.recognize_google(audio))
        except Exception:
            # print(traceback.format_exc())
            pass
        rms = audioop.rms(audio.get_raw_data(), 2)
        db = 20 * np.log10(rms)
        # print(rms)
        # print(db)
        if not det == "":
            to_ret = joinStrings([det,str(db)], Constants.STRING_SEPARATOR_INNER)
            # print(to_ret)
            logger.info("Detected speech info: {}".format(to_ret))
            # print(audio.get_raw_data())
            return to_ret
        else:
            # print("-nothing detected-")
            return None
        # else:
        #     return None

        # tor = "stand"
        # # tor = "test "+str(self.idx)
        # # self.idx = self.idx+1
        # print(tor)
        # return tor

