import time
import traceback
# import pyttsx3


import utils.constants as Constants
from actuators.actuator import Actuator

import logging
logger = logging.getLogger("mqtt-nao-interface.actuators.speech.tts")

class TextToSpeech(Actuator):
    def __init__(self, nao_interface, id, mqtt_topic, qi_app, virtual=False):
        super(TextToSpeech, self).__init__(nao_interface, id, mqtt_topic, [Constants.NAO_SERVICE_TTS], qi_app, virtual)
        self.services[Constants.NAO_SERVICE_TTS].setLanguage("English")
        self.default_volume = 0.7
        self.is_first_tts = True

        # if self.virtual:
        #     self.tts_engine = pyttsx3.init()


    def actuate(self, directive):
        splitted_directive = directive.split(Constants.STRING_SEPARATOR)
        logger.info(str(splitted_directive))
        if splitted_directive[0] == "say":
            try:
                logger.debug("Setting is_speaking to True")
                self.nao_interface.is_speaking = True
                if self.nao_interface.is_listening:  # if I start saying something while audio is being captured, then I set to discard such a thing later
                    self.nao_interface.discard_last_audio = True

                # sentence = "\RSPD=" + str(tts.getParameter("Speed (%)")) + "\ "
                # sentence += "\VCT=" + str(tts.getParameter("Voice shaping (%)")) + "\ "
                sentence = str(splitted_directive[1])
                if splitted_directive[2] == "volume":
                    volume = round(float(splitted_directive[3])/100.0,2)
                    logger.info("-> setting volume to "+str(volume))
                    self.services[Constants.NAO_SERVICE_TTS].setVolume(volume)
                else:
                    self.services[Constants.NAO_SERVICE_TTS].setVolume(self.default_volume)

                if len(splitted_directive)>5 and splitted_directive[4] == "emotion":
                    if splitted_directive[5] == "joy":
                        sentence = "\\style=playful\\ "+sentence


                # sentence += "\RST\ "
                logger.info("-> "+str(sentence))
                self.say(str(sentence))

                self.nao_interface.is_speaking = False
                logger.debug("Setting is_speaking to False")
                # if self.nao_interface.is_listening:
                #     self.nao_interface.services["SpeechRecognizer"].stopListening()


            except Exception:
                logger.warning(traceback.format_exc())
                logger.warning("Could not perform directive ", splitted_directive)
                self.nao_interface.is_speaking = False
                pass

    def say(self, sentence):

        # print("is speaking")
        sub_sentences = sentence.split(".")
        # i = 0
        for ss in sub_sentences:
            id = self.services[Constants.NAO_SERVICE_TTS].pCall("say", str(ss))
            self.services[Constants.NAO_SERVICE_TTS].wait(id)

            # if self.virtual:
            #     tts_engine = pyttsx3.init()
            #     tts_engine.say(str(ss))
            #     tts_engine.runAndWait()
            #     del tts_engine
            # if i<len(sub_sentences)-1:
            #     time.sleep(0.1) #short pause in  betwwen subsentences
            # i += 1
        # if self.is_first_tts:
        #     id = self.services[Constants.NAO_SERVICE_TTS].pCall("say",
        #                                                         "Hey, by the way, when you see that my chest becomes blue, it's because I'm thinking. Please, be patient.")
        #     self.services[Constants.NAO_SERVICE_TTS].wait(id)
        #     self.is_first_tts = False
        logger.debug("FInished saying sentences")


        # print("is not speaking")


