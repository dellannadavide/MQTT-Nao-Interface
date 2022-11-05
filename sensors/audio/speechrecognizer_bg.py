import random

import pyaudio
import speech_recognition as sr

from sensors.audio.mic import MicEnergyDetector
from sensors.sensor import Sensor
import utils.constants as Constants
import utils.util

class SpeechRecognizerBG(Sensor):
    def __init__(self, nao_interface, id, mqtt_topic, freq, qi_app=None, micenergy=None, virtual=False):
        super(SpeechRecognizerBG, self).__init__(nao_interface, id, mqtt_topic, [], freq, qi_app, virtual)

        self.timeout = 10
        self.phrase_time_limit = 5

        p = pyaudio.PyAudio()
        self.dev_count = p.get_device_count()
        # for i in range(p.get_device_count()):
        #     print(i)
        #     print p.get_device_info_by_index(i)

        self.micenergy = micenergy

        self.sentences = []
        self.last_sentences = ""

        self.get_audio()

    def get_audio(self):
        try:
            r = sr.Recognizer()
            mic = sr.Microphone()
            if (self.dev_count > 5):
                mic = sr.Microphone(2)
            print("listening...")
            with mic as source:
                r.adjust_for_ambient_noise(source)
                if not self.micenergy is None:
                    self.micenergy.collectEnergyLevels()

                    stop_listening = r.listen_in_background(source, phrase_time_limit=self.phrase_time_limit, callback=self.callback)
        except:
            print("try again")
            self.get_audio()


    def sense(self):
        if len(self.sentences) > 0:
            to_ret = utils.util.joinStrings(self.sentences)
            if not self.last_sentences == to_ret:
                self.last_sentences = to_ret
                # to_ret = str(self.faces)
                self.sentences = []
                return to_ret
            else:
                return None
        else:
            return None

    def callback(self, recognizer, audio):  # this is called from the background thread
        source_direction = "Front"
        det = ""

        if not self.micenergy is None:
            source_direction = self.micenergy.getSource()
            self.micenergy.collectEnergyLevels()

        print(source_direction)
        if source_direction == "Front":
            try:
                det = str(recognizer.recognize_google(audio))
                # print("You said " + recognizer.recognize(audio))  # received audio data, now need to recognize it
            except LookupError:
                print("Oops! Didn't catch that")

        if not det == "":
            print(det)
            self.sentences.append(det)

        print("listening...")
