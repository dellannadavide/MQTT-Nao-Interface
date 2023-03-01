import audioop
import random
import time
import traceback
from datetime import datetime

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
    """ Speech Recognizer Sensor. It handles data coming from micropohones
    (these could be Nao's, or also external ones,
    e.g., the laptop mic if virtual robot is used, or external microphones).
    Uncommenting the lines indicated below with */*/*/,
    it is also possible to simulate speech detection by interactively inserting text via console
    """
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
        if self.nao_interface.is_speaking or self.nao_interface.is_thinking:
            if self.nao_interface.is_thinking:
                if float(time.time()) - float(self.nao_interface.last_thinking_time) < 30:
                    return None
                else:
                    pass
            else:
                return None

        if self.idx > 0:
            logger.info("listening " + str(self.idx))
        self.idx = self.idx + 1
        if not self.virtual:
            if self.idx > 1:  # i skip the first green light so to avoid possible missed sentences
                self.nao_interface.services["LedsActuator"].setColor("green")
        self.nao_interface.is_listening = True
        timeout = time.time() + self.timeout
        try:
            self.stop_listening = self.r.listen_in_background(sr.Microphone(self.mic_device), self.listening_callback, phrase_time_limit=self.phrase_time_limit)
            while self.nao_interface.is_listening:
                if time.time() <= timeout:
                    time.sleep(0.05)
                else:
                    self.stopListening(erase_detected=True)
                    if not self.virtual:
                        self.nao_interface.services["LedsActuator"].setColor("white")
        except:
            self.stopListening(erase_detected=True)
            return None


        """ */*/*/ Uncomment the following if you want to insert interactively text from console, simulating speech detection """
        # to_say = raw_input("Enter what to say:")
        # return joinStrings([to_say, "50"],
        #                      Constants.STRING_SEPARATOR_INNER)


        if not self.last_detected_speech is None:
            if not self.virtual:
                self.nao_interface.services["LedsActuator"].setColor(Constants.COLORS_YELLOW)
            to_ret = joinStrings([self.last_detected_speech,self.last_detected_speech_db], Constants.STRING_SEPARATOR_INNER)
            logger.info("Detected speech info: {}".format(to_ret))
            if self.nao_interface.is_sleeping:
                if self.last_detected_speech == "wake up":
                    self.nao_interface.setSleeping(False)
                    return to_ret
                else:
                    return None
            return to_ret
        else:
            return None


