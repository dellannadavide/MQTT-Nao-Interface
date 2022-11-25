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
        self.mic_device = 0
        for i in range(p.get_device_count()):
            print(p.get_device_info_by_index(i))
            if "Wireless GO" in str(p.get_device_info_by_index(i)):
                self.mic_device = i
                break
            elif "Microphone Array (Realtek(R)" in str(p.get_device_info_by_index(i)):
                self.mic_device = i
                break

        logger.info("Selected mic: "+str(self.mic_device)+" - "+str(p.get_device_info_by_index(self.mic_device)))

        self.r = sr.Recognizer()
        self.r.pause_threshold = 0.2
        self.r.non_speaking_duration = 0.1
        self.mic = sr.Microphone(self.mic_device)

        with self.mic as source:
            self.r.adjust_for_ambient_noise(source)

        self.idx = 0

        self.micenergy = micenergy

    # def initRecognizer(self):
    #     self.r = sr.Recognizer()
    #     self.r.pause_threshold = 0.2
    #     self.r.non_speaking_duration = 0.1
    #     self.mic = sr.Microphone(self.mic_device)
    #
    #     with self.mic as source:
    #         self.r.adjust_for_ambient_noise(source)
    # def stopListening(self):
    #     self.initRecognizer()


    def sense(self):
        # logger.debug("....beginning sensing")
        if self.nao_interface.is_speaking:
            logger.info("Nao is speaking, I'm not gonna listen")
            # time.sleep(0.5)
            return None
        try:
            with self.mic as source:
                # if not self.micenergy is None:
                #     self.micenergy.collectEnergyLevels()
                if self.idx>0:
                    logger.info("listening " + str(self.idx))
                self.idx = self.idx + 1
                if not self.virtual:
                    if self.idx > 1: #i skip the first green light so to avoid possible issues
                        self.nao_interface.services["LedsActuator"].setColor("green")

                self.nao_interface.is_listening = True
                # logger.debug("....listening started")
                audio = self.r.listen(source, timeout=self.timeout, phrase_time_limit=self.phrase_time_limit)
                # logger.debug("....listening ended")
                self.nao_interface.is_listening = False
                if not self.virtual:
                    self.nao_interface.services["LedsActuator"].setColor("white")

        except Exception:
            # logger.warning(traceback.format_exc())
            self.nao_interface.is_listening = False
            return None

        # if not self.micenergy is None:
        #     source_direction = self.micenergy.getSource()
        # else:
        #     source_direction = "Front"
            # audio = self.r.listen(source)
        # print(source_direction)
        # if source_direction=="Front":
        if not self.nao_interface.discard_last_audio:
            self.nao_interface.services["LedsActuator"].setColor(Constants.COLORS_YELLOW)
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
                if self.nao_interface.is_sleeping:
                    if det == "wake up":
                        self.nao_interface.setSleeping(False)
                        return to_ret
                    else:
                        return None
                return to_ret
            else:
                # print("-nothing detected-")
                return None
        else:
            self.nao_interface.discard_last_audio = False
            return None


