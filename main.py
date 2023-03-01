import argparse
import logging
import os
import sys
import time
import traceback
from datetime import datetime

import qi

import utils.constants as Constants
from actuators.posture.posture import PostureActuator
from actuators.speech.tts import TextToSpeech
from actuators.system.leds import Leds
from actuators.system.power import Power
from sensors.audio.mic import MicEnergyDetector
from sensors.audio.speechrecognizer import SpeechRecognizer
from sensors.video.detecthuman import HumanDetector
from sensors.video.emotion_detector import EmotionDetector
from sensors.video.headtracker import HeadTracker
from sensors.video.naoimagecollector import NaoImageCollector
from sensors.video.object_detector import ObjectDetector


def restart_program():
    """Restarts the current program, with file objects and descriptors
       cleanup
    """
    logger.warning("Restarting the program (note: this will work only if program launched via console)...")
    # try:
    #     p = psutil.Process(os.getpid())
    #     for handler in p.open_files() + p.connections():
    #         os.close(handler.fd)
    # except Exception, e:
    #     logging.error(e)

    python = sys.executable
    os.execl(python, python, *sys.argv)



class NaoInterface:
    """ The main class of the MQTT-Nao-Interface"""
    def __init__(self, ip, port, virtual, additional_behaviors_folder):
        self.ip = ip
        self.port = port
        self.virtual = virtual
        self.additional_behaviors_folder = additional_behaviors_folder
        self.services = {}
        self.app = None

        """ Some variables desribing the entire system, used to synchronize the different services """
        self.simulation = False
        self.is_speaking = False
        self.is_listening = False
        self.is_moving = False
        self.is_looking = False
        self.is_thinking = False
        self.last_thinking_time = -1
        self.is_sleeping = False


    def startQIAPP(self):
        """ Starts the NaoQi application to interface with Nao """

        parser = argparse.ArgumentParser()
        parser.add_argument("--ip", type=str, default=self.ip,
                            help="Robot IP address. On robot or Local Naoqi: use '127.0.0.1'.")
        parser.add_argument("--port", type=int, default=port,
                            help="Naoqi port number")

        args = parser.parse_args()
        try:
            # Initialize qi framework.
            connection_url = "tcp://" + args.ip + ":" + str(args.port)
            self.app = qi.Application(["NaoInterface", "--qi-url=" + connection_url])
            self.app.start()
        except RuntimeError:
            logger.error(traceback.format_exc())
            logger.error("Can't connect to Naoqi at ip \"" + args.ip + "\" on port " + str(args.port) + ".\n"
                                                                                                  "Please check that the IP of Nao and the port are correct. "
                                                                                                  "If running the virtual robot you can find the port on Choreographe (Edit-Preferences-Virtual Robot).")
            # sys.exit(1) #i moved this in the run
            return None
        except:
            logger.error(traceback.format_exc())
            logger.error("Can't connect to Naoqi at ip \"" + args.ip + "\" on port " + str(args.port) + ".\n"
                                                                                                 "Please check that the IP of Nao and the port are correct. "
                                                                                                  "If running the virtual robot you can find the port on Choreographe (Edit-Preferences-Virtual Robot).")
            return None

        return self.app


    def handleRuntimeExceptions(self):
        """ restarts the interface when runtime exceptions are thrown """
        logger.info("Closing application")
        self.app.stop()
        logger.info("Asking to every service to prepare to close")
        for s in self.services.keys():
            self.services[s].prepareToEnd()
        time.sleep(2)
        restart_program()

    def setSleeping(self, gotosleep):
        """ Sets all services to sleep, apart from the speech recognizer.
        The speech recognizer remains on, listening to 'wake up' sentence for waking up. """
        if gotosleep:
            while self.is_speaking:  # in case Nao is saying a sentence, I wait for it to finish
                time.sleep(0.1)
            self.is_sleeping = True
            self.services["Power"].sleep()
            if "LedsActuator" in self.services.keys():
                self.services["LedsActuator"].setSleeping(True)
            logger.info("Setting Nao to Sleep (it can be woken up with keywork \"wake up\"). All services but the speech recognition are paused")
            for s in self.services.keys():
                if not s=="SpeechRecognizer":
                    self.services[s].pause()
        else:
            self.is_sleeping = False
            self.services["Power"].wake_up()
            if "LedsActuator" in self.services.keys():
                self.services["LedsActuator"].setSleeping(False)
            logger.info("Waking up Nao. All services are unpaused")
            for s in self.services.keys():
                self.services[s].unpause()


    def run(self):
        """ Runs the interface. Starts the NaoQi app and then starts all services"""
        self.app = self.startQIAPP()
        if not self.app is None:
            """ 
            Here can decide which services to start (comment or uncomment)
            IMPORTANT: some of the following only work with the real robot (the case "not self.virtual")
            It is possible to change the frequency of sensing of the sensors from here
            """

            Constants.ADDITIONAL_BEHAVIORS_FOLDER = self.additional_behaviors_folder

            if not self.virtual:
                micEnDet = MicEnergyDetector(self, "MicEnergyDetector", Constants.TOPIC_MICENERGY, 0.1, self.app)
                naoImageCollector = NaoImageCollector(self, "NaoImageCollector", None, 0.15, self.app)
                self.services = {
                    # ACTUATORS
                    "TextToSpeech": TextToSpeech(self, "TextToSpeech", Constants.TOPIC_DIRECTIVE_TTS, self.app),
                    "Power": Power(self, "Power", Constants.TOPIC_DIRECTIVE_SYSTEM, self.app),
                    "PostureActuator": PostureActuator(self, "PostureActuator", Constants.TOPIC_POSTURE, self.app),
                    # "MotionActuator": MotionActuator(self, "MotionActuator", Constants.TOPIC_MOTION, self.app),
                    # BehaviorActuator(self, "BehaviorActuator", Constants.TOPIC_BEHAVIOR, app),
                    "LedsActuator": Leds(self, "LedsActuator", Constants.TOPIC_LEDS, self.app),
                    # SENSORS
                    "MicEnergyDetector": micEnDet,
                    "NaoImageCollector": naoImageCollector,
                    "SpeechRecognizer": SpeechRecognizer(self, "SpeechRecognizer", Constants.TOPIC_SPEECH, 0.01, micenergy=micEnDet),
                    "HumanDetector": HumanDetector(self, "HumanDetector", Constants.TOPIC_HUMAN_DETECTION, 3, self.app),
                    # "VisionRecognition": VisionRecognition(self, "VisionRecognition", Constants.TOPIC_OBJECT_DETECTION, 1.5, self.app),
                    # human greeter (incl. human detection) (ONLY FOR REAL ROBOT)
                    # DistanceDetector(self, "DistanceDetector", Constants.TOPIC_DISTANCE, 5, app),
                    "HeadTracker": HeadTracker(self, "HeadTracker", Constants.TOPIC_HEAD_TRACKER, 0.5, self.app),
                    "EmotionDetector": EmotionDetector(self, "EmotionDetector", Constants.TOPIC_EMOTION_DETECTION, 2, self.app),
                    "ObjectDetector":ObjectDetector(self, "ObjectDetector", Constants.TOPIC_OBJECT_DETECTION, 3, self.app),
                }
            else:
                naoImageCollector = NaoImageCollector(self, "NaoImageCollector", None, 0.15, self.app, virtual=True)
                self.services = {
                    # SENSORS
                    "NaoImageCollector": naoImageCollector,
                    "SpeechRecognizer": SpeechRecognizer(self, "SpeechRecognizer", Constants.TOPIC_SPEECH, 0.01, virtual=True),  # 0.1
                    "HeadTracker": HeadTracker(self, "HeadTracker", Constants.TOPIC_HEAD_TRACKER, 0.1, self.app, virtual=True),
                    "EmotionDetector": EmotionDetector(self, "EmotionDetector", Constants.TOPIC_EMOTION_DETECTION, 2, self.app),
                    "ObjectDetector":ObjectDetector(self, "ObjectDetector", Constants.TOPIC_OBJECT_DETECTION, 1, virtual=True),
                    # "ObjectDetectorHAT":ObjectDetectorHAT(self, "ObjectDetectorHAT", Constants.TOPIC_OBJECT_DETECTION, 1, virtual=True),
                    # DistanceDetector(self, "DistanceDetector", Constants.TOPIC_DISTANCE, 1, app, virtual=True), #0.2
                    # ACTUATORS
                    "TextToSpeech": TextToSpeech(self, "TextToSpeech", Constants.TOPIC_DIRECTIVE_TTS, self.app, virtual=True),
                    "Power": Power(self, "Power", Constants.TOPIC_DIRECTIVE_SYSTEM, self.app, virtual=True),
                    "PostureActuator": PostureActuator(self, "PostureActuator", Constants.TOPIC_POSTURE, self.app), #doesn't require the virtual to be true?
                    # "MotionActuator": MotionActuator(self, "MotionActuator", Constants.TOPIC_MOTION, self.app, virtual=True)
                    # BehaviorActuator(self, "BehaviorActuator", Constants.TOPIC_BEHAVIOR, app, virtual=True)
                }

            """ Based on the services selected above, run in parallel their corresponding run functions"""
            for s in self.services.keys():
                self.services[s].start()

            for s in self.services.keys():
                self.services[s].unpause()
        else:
            logger.warning("Could not start the qi App. Waiting 5 seconds and then trying to reconnect...")
            time.sleep(5)
            self.run()



if __name__ == "__main__":
    now = datetime.now()
    exec_timestamp = str(now.strftime("%Y%m%d%H%M%S"))
    """ An id to give to the execution (e.g., used to identify the logs of participants) """
    # exp_id = "jeec1"
    exp_id = "dda"
    """ The type of agent being executed (N.B., only to reflect the SONAR counterpart in the name of the log) """
    agent_type = "parrot_agent"
    # agent_type = "baseline_agent"
    agent_type = "sonar_agent"

    log_folder = "./log/"
    log_path_name = log_folder + exp_id+"_mqtt_nao_interface_" + agent_type + "_" + exec_timestamp + ".log"

    logging.getLogger().setLevel(logging.DEBUG)
    logFormatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    fileHandler = logging.FileHandler(log_path_name, mode="a+")
    fileHandler.setFormatter(logFormatter)
    logging.getLogger().addHandler(fileHandler)

    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    logging.getLogger().addHandler(consoleHandler)

    logger = logging.getLogger("mqtt-nao-interface")

    """ Comment/uncomment one of the following three blocks, and modify the parameters, based on the context """
    # IF RUNNING NAO ON A DIFFERENT ADDRESS
    ip = "172.19.67.246"
    port = 9559
    virtual = False
    additional_behaviors_folder = "nao_additional_behaviors-2870f3"

    # IF RUNNING NAO ON SAME LOCAL ADDRESS
    # ip = "nao.local"
    # port = 9559
    # virtual = False
    # additional_behaviors_folder = "nao_additional_behaviors-2870f3"

    # IF RUNNING THE VIRTUAL ROBOT ON CHOREOGRAPH
    ip = "localhost"
    port = 50148
    virtual = True
    additional_behaviors_folder = ".lastUploadedChoregrapheBehavior"

    """ Runs the interface """
    nao_interface = NaoInterface(ip, port, virtual, additional_behaviors_folder)
    nao_interface.run()









