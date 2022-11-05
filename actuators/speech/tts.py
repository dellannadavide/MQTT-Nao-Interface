import time
import traceback
# import pyttsx3


import utils.constants as Constants
from actuators.actuator import Actuator


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
        print(splitted_directive)
        if splitted_directive[0] == "say":
            try:
                # sentence = "\RSPD=" + str(tts.getParameter("Speed (%)")) + "\ "
                # sentence += "\VCT=" + str(tts.getParameter("Voice shaping (%)")) + "\ "
                sentence = str(splitted_directive[1])
                if splitted_directive[2] == "volume":
                    volume = round(float(splitted_directive[3])/100.0,2)
                    print("-> setting volume to "+str(volume))
                    self.services[Constants.NAO_SERVICE_TTS].setVolume(volume)
                else:
                    self.services[Constants.NAO_SERVICE_TTS].setVolume(self.default_volume)
                # sentence += "\RST\ "
                print("-> "+str(sentence))
                self.say(str(sentence))


            except Exception:
                print(traceback.format_exc())
                print("Could not perform directive ", splitted_directive)
                pass

    def say(self, sentence):
        self.nao_interface.is_speaking = True
        # print("is speaking")
        sub_sentences = sentence.split(".")
        for ss in sub_sentences:
            id = self.services[Constants.NAO_SERVICE_TTS].pCall("say", str(ss))
            self.services[Constants.NAO_SERVICE_TTS].wait(id)

            # if self.virtual:
            #     tts_engine = pyttsx3.init()
            #     tts_engine.say(str(ss))
            #     tts_engine.runAndWait()
            #     del tts_engine

            time.sleep(0.1) #short pause in  betwwen subsentences

        # if self.is_first_tts:
        #     id = self.services[Constants.NAO_SERVICE_TTS].pCall("say",
        #                                                         "Hey, by the way, when you see that my chest becomes blue, it's because I'm thinking. Please, be patient.")
        #     self.services[Constants.NAO_SERVICE_TTS].wait(id)
        #     self.is_first_tts = False

        self.nao_interface.is_speaking = False
        # print("is not speaking")


