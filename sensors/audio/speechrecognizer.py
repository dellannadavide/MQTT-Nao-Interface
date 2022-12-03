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

        self.timeout = 7
        self.phrase_time_limit = 5
        self.micenergy = micenergy

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
        self.r.pause_threshold = 0.1
        self.r.non_speaking_duration = 0.05
        self.stop_listening = None

        mic = sr.Microphone(self.mic_device)
        with mic as source:
            self.r.adjust_for_ambient_noise(source)

        self.idx = 0



        self.last_detected_speech = None
        self.last_detected_speech_db = None

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

    def listening_callback(self, recognizer, audio):  # this is called from the background thread
        # self.nao_interface.is_listening = False
        # logger.debug("in callback")
        if not self.virtual:
            self.nao_interface.services["LedsActuator"].setColor(Constants.COLORS_YELLOW)
        try:
            self.last_detected_speech = str(recognizer.recognize_google(audio))
            rms = audioop.rms(audio.get_raw_data(), 2)
            self.last_detected_speech_db = str(20 * np.log10(rms))
            # print("You said " + self.last_detected_speech)  # received audio data, now need to recognize it
            # logger.debug("recognized {} ({})".format(self.last_detected_speech, self.last_detected_speech_db))
            if self.last_detected_speech == "":
                self.last_detected_speech = None
                self.last_detected_speech_db = None
        except:
            # logger.warning(traceback.format_exc())
            # print("Oops! Didn't catch that")
            # logger.debug("nothing recognized")
            self.last_detected_speech = None
            self.last_detected_speech_db = None

        self.stopListening(erase_detected=False)  # stop listening when audio being processed (it will restart later)

    def stopListening(self, erase_detected):
        logger.debug("stopping listening")
        try:
            self.stop_listening(wait_for_stop=False)
        except:
            logger.debug("error in stopping listening")
            pass
        self.nao_interface.is_listening = False
        if erase_detected:
            self.last_detected_speech = None
            self.last_detected_speech_db = None

    def sense(self):
        # logger.debug("....beginning sensing")
        if self.nao_interface.is_speaking or self.nao_interface.is_thinking:
            # logger.info("Nao is speaking, I'm not gonna listen")
            # time.sleep(0.5)
            return None

            # with self.mic as source:
            #     # if not self.micenergy is None:
            #     #     self.micenergy.collectEnergyLevels()
            #     if self.idx>0:
            #         logger.info("listening " + str(self.idx))
            #     self.idx = self.idx + 1
            #     if not self.virtual:
            #         if self.idx > 1: #i skip the first green light so to avoid possible issues
            #             self.nao_interface.services["LedsActuator"].setColor("green")
            #
            #     self.nao_interface.is_listening = True
            #     # logger.debug("....listening started")
            #     audio = self.r.listen(source, timeout=self.timeout, phrase_time_limit=self.phrase_time_limit)
            #     # logger.debug("....listening ended")
            #     self.nao_interface.is_listening = False
            #     if not self.virtual:
            #         self.nao_interface.services["LedsActuator"].setColor("white")

        if self.idx > 0:
            logger.info("listening " + str(self.idx))
        self.idx = self.idx + 1
        if not self.virtual:
            if self.idx > 1:  # i skip the first green light so to avoid possible issues
                self.nao_interface.services["LedsActuator"].setColor("green")
        self.nao_interface.is_listening = True
        timeout = time.time() + self.timeout
        # logger.debug("beginning listening in bg")
        try:
            self.stop_listening = self.r.listen_in_background(sr.Microphone(self.mic_device), self.listening_callback, phrase_time_limit=self.phrase_time_limit)
            while self.nao_interface.is_listening:
                # print(self.r.energy_threshold)
                # logger.debug("checking if timeout reached")
                if time.time() <= timeout:
                    # logger.debug("no, I wait and then retry")
                    time.sleep(0.05)
                else:  # if I reached the timeout
                    # logger.debug("yes, stopping listening with no detected speech")
                    self.stopListening(erase_detected=True)
                    if not self.virtual:
                        self.nao_interface.services["LedsActuator"].setColor("white")
        except:
            # logger.warning(traceback.format_exc())
            self.stopListening(erase_detected=True)
            return None

        # if not self.micenergy is None:
        #     source_direction = self.micenergy.getSource()
        # else:
        #     source_direction = "Front"
            # audio = self.r.listen(source)
        # print(source_direction)
        # if source_direction=="Front":
        if not self.last_detected_speech is None:
            if not self.virtual:
                self.nao_interface.services["LedsActuator"].setColor(Constants.COLORS_YELLOW)
            # det = ""
            # try:
            #     det = str(self.r.recognize_google(audio))
            # except Exception:
            #     # print(traceback.format_exc())
            #     pass
            # rms = audioop.rms(audio.get_raw_data(), 2)
            # db = 20 * np.log10(rms)
            # print(rms)
            # print(db)
            # if not self.last_detected_speech == "":
            to_ret = joinStrings([self.last_detected_speech,self.last_detected_speech_db], Constants.STRING_SEPARATOR_INNER)
            # print(to_ret)
            logger.info("Detected speech info: {}".format(to_ret))
            # print(audio.get_raw_data())
            if self.nao_interface.is_sleeping:
                if self.last_detected_speech == "wake up":
                    self.nao_interface.setSleeping(False)
                    return to_ret
                else:
                    return None
            return to_ret
            # else:
            #     # print("-nothing detected-")
            #     return None
        else:
            return None


