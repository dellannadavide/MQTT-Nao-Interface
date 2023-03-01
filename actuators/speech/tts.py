import time
import traceback
# import pyttsx3


import utils.constants as Constants
from actuators.actuator import Actuator

import logging
logger = logging.getLogger("mqtt-nao-interface.actuators.speech.tts")

class TextToSpeech(Actuator):
    """ Text to speech actuator. Processes direcctives that indicate what to say and how. """
    def __init__(self, nao_interface, id, mqtt_topic, qi_app, virtual=False):
        super(TextToSpeech, self).__init__(nao_interface, id, mqtt_topic, [Constants.NAO_SERVICE_TTS], qi_app, virtual)
        self.services[Constants.NAO_SERVICE_TTS].setLanguage("English")
        self.default_volume = 0.9
        self.default_speed = 90
        self.is_first_tts = True

    def actuate(self, directive_list):
        for directive in directive_list:
            splitted_directive = directive.split(Constants.STRING_SEPARATOR)
            logger.info(str(splitted_directive))
            if splitted_directive[0] == "say":
                try:
                    logger.debug("Setting is_speaking to True")
                    self.nao_interface.is_speaking = True
                    if self.nao_interface.is_listening:  # if I start saying something while audio is being captured, then I set to discard such a thing later
                        self.nao_interface.services["SpeechRecognizer"].stopListening(erase_detected=True)

                    sentence = str(splitted_directive[1])

                    """ Cleaning the sentence by replacing some stuff that cannot be said out loud (the list of things could be expanded) """
                    sentence = sentence.replace(":D", "")

                    volume = None
                    if splitted_directive[2] == "volume":
                        volume = round(float(splitted_directive[3])/100.0,2)
                    speed = None
                    if splitted_directive[4] == "speed":
                        speed = float(splitted_directive[5])
                    shape = None
                    if splitted_directive[6] == "tone":
                        shape = float(splitted_directive[7])
                    emotion = None
                    if len(splitted_directive)>8 and splitted_directive[7] == "emotion":
                        emotion = splitted_directive[8]

                    logger.info("-> "+str(sentence))
                    self.say(str(sentence), emotion, speed, shape, volume)

                    self.nao_interface.is_speaking = False
                    logger.debug("Setting is_speaking to False")

                except Exception:
                    logger.warning(traceback.format_exc())
                    logger.warning("Could not perform directive ", splitted_directive)
                    self.nao_interface.is_speaking = False
                    pass

    def say(self, sentence, emotion, speed, shape, volume):
        if not volume is None:
            logger.info("-> setting volume to " + str(volume))
            self.services[Constants.NAO_SERVICE_TTS].setVolume(volume)
        else:
            self.services[Constants.NAO_SERVICE_TTS].setVolume(self.default_volume)

        sub_sentences = sentence.split(".")
        for ss in sub_sentences:
            if (not emotion is None) and (emotion == "joy"):
                ss = "\\style=playful\\ " + ss
            if (not speed is None):
                ss = "\\rspd="+str(int(speed))+"\\"+ss
            if (not shape is None):
                ss = "\\vct="+str(int(shape))+"\\"+ss

            logger.info("---> " + str(ss))

            id = self.services[Constants.NAO_SERVICE_TTS].pCall("say", str(ss))
            self.services[Constants.NAO_SERVICE_TTS].wait(id)

        logger.debug("Finished saying sentences")


