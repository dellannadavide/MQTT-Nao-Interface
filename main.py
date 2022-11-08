import traceback
import os
from datetime import datetime

import logging
import qi
import time
import sys
import argparse
import utils.constants as Constants
from actuators.posture.posture import PostureActuator
from actuators.speech.tts import TextToSpeech
from actuators.system.leds import Leds
from sensors.audio.mic import MicEnergyDetector
from sensors.video.detecthuman import HumanDetector
from sensors.video.emotion_detector import EmotionDetector
from sensors.video.headtracker import HeadTracker
from sensors.video.naoimagecollector import NaoImageCollector
from sensors.video.object_detector import ObjectDetector

from sensors.audio.speechrecognizer import SpeechRecognizer


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
    def __init__(self, ip, port, virtual, additional_behaviors_folder):
        self.ip = ip
        self.port = port
        self.virtual = virtual
        self.additional_behaviors_folder = additional_behaviors_folder
        self.simulation = False
        self.is_speaking = False
        self.is_moving = False
        self.is_looking = False
        self.is_thinking = False
        self.is_starting = False
        self.services = {}
        self.app = None

    def startQIAPP(self):
        # if not self.app is None:
        #     # print("stopping")
        #     # qi._stopApplication()
        #     # qi._app = None
        #     # time.sleep(2)
        #     self.app = None

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
        logger.info("Closing application")
        self.app.stop()
        logger.info("Asking to every service to prepare to close")
        for s in self.services:
            s.prepareToEnd()
        time.sleep(2)
        restart_program()


    def run(self):
        self.app = self.startQIAPP()
        if not self.app is None:
            """ 
            Here can decide which services to start (comment or uncomment)
            IMPORTANT: some of the following only work with the real robot
            """
            # TODO TO INCLUDE THE VIDEO-RELATED ONES

            Constants.ADDITIONAL_BEHAVIORS_FOLDER = self.additional_behaviors_folder

            if not self.virtual:
                micEnDet = MicEnergyDetector(self, "MicEnergyDetector", Constants.TOPIC_MICENERGY, 0.1, self.app)
                naoImageCollector = NaoImageCollector(self, "NaoImageCollector", None, 0.15, self.app)
                self.services = {
                    # SENSORS
                    "MicEnergyDetector": micEnDet,
                    "NaoImageCollector": naoImageCollector,
                    "SpeechRecognizer": SpeechRecognizer(self, "SpeechRecognizer", Constants.TOPIC_SPEECH, 0.1, micenergy=micEnDet),
                    "HumanDetector": HumanDetector(self, "HumanDetector", Constants.TOPIC_HUMAN_DETECTION, 3, self.app),
                    # human greeter (incl. human detection) (ONLY FOR REAL ROBOT)
                    # DistanceDetector(self, "DistanceDetector", Constants.TOPIC_DISTANCE, 5, app),
                    "HeadTracker": HeadTracker(self, "HeadTracker", Constants.TOPIC_HEAD_TRACKER, 1, self.app),
                    "EmotionDetector": EmotionDetector(self, "EmotionDetector", Constants.TOPIC_EMOTION_DETECTION, 2, self.app),
                    "ObjectDetector":ObjectDetector(self, "ObjectDetector", Constants.TOPIC_OBJECT_DETECTION, 3, self.app),
                    # ACTUATORS
                    "TextToSpeech": TextToSpeech(self, "TextToSpeech", Constants.TOPIC_DIRECTIVE, self.app),
                    # Power(self, "PowerShutter", Constants.TOPIC_DIRECTIVE, app),
                    "PostureActuator": PostureActuator(self, "PostureActuator", Constants.TOPIC_POSTURE, self.app),
                    # "MotionActuator": MotionActuator(self, "MotionActuator", Constants.TOPIC_MOTION, self.app),
                    # BehaviorActuator(self, "BehaviorActuator", Constants.TOPIC_BEHAVIOR, app),
                    "LedsActuator": Leds(self, "LedsActuator", Constants.TOPIC_LEDS, self.app)
                }
            else:
                naoImageCollector = NaoImageCollector(self, "NaoImageCollector", None, 0.15, self.app, virtual=True)
                self.services = {
                    # SENSORS
                    "NaoImageCollector": naoImageCollector,
                    "SpeechRecognizer": SpeechRecognizer(self, "SpeechRecognizer", Constants.TOPIC_SPEECH, 0.1, virtual=True),  # 0.1
                    "HeadTracker": HeadTracker(self, "HeadTracker", Constants.TOPIC_HEAD_TRACKER, 0.1, self.app, virtual=True),
                    "EmotionDetector": EmotionDetector(self, "EmotionDetector", Constants.TOPIC_EMOTION_DETECTION, 1, self.app),
                    "ObjectDetector":ObjectDetector(self, "ObjectDetector", Constants.TOPIC_OBJECT_DETECTION, 1, virtual=True),
                    # DistanceDetector(self, "DistanceDetector", Constants.TOPIC_DISTANCE, 1, app, virtual=True), #0.2
                    # ACTUATORS
                    "TextToSpeech": TextToSpeech(self, "TextToSpeech", Constants.TOPIC_DIRECTIVE, self.app, virtual=True),
                    "PostureActuator": PostureActuator(self, "PostureActuator", Constants.TOPIC_POSTURE, self.app), #doesn't require the virtual to be true?
                    # "MotionActuator": MotionActuator(self, "MotionActuator", Constants.TOPIC_MOTION, self.app, virtual=True)
                    # BehaviorActuator(self, "BehaviorActuator", Constants.TOPIC_BEHAVIOR, app, virtual=True)
                }

            """ Based on the services selected above, run in parallel their corresponding run functions"""
            run_functions = []
            for s in self.services.keys():
                self.services[s].start()
                # run_functions.append(s.run)
            # runInParallel2(*run_functions)
            # print("WARNING you disabled speechrecognizer in the virtual robot")
        else:
            logger.warning("Could not start the qi App. Waiting 5 seconds and then trying to reconnect...")
            time.sleep(5)
            self.run()



if __name__ == "__main__":
    now = datetime.now()
    exec_timestamp = str(now.strftime("%Y%m%d%H%M%S"))
    log_folder = "./log/"
    log_path_name = log_folder + "mqtt_nao_interface_" + exec_timestamp + ".log"

    # logging.basicConfig(level=logging.INFO,
    #                     format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    #                     handlers=[
    #                         logging.FileHandler(log_path_name, mode="a+"),
    #                         logging.StreamHandler(sys.stdout)
    #                     ])


    logging.getLogger().setLevel(logging.INFO)

    logFormatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    fileHandler = logging.FileHandler(log_path_name, mode="a+")
    fileHandler.setFormatter(logFormatter)
    logging.getLogger().addHandler(fileHandler)

    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    logging.getLogger().addHandler(consoleHandler)

    logger = logging.getLogger("mqtt-nao-interface")

    #IF RUNNING NAO ON A DIFFERENT ADDRESS
    ip = "172.19.67.246"
    port = 9559
    virtual = False
    additional_behaviors_folder = "nao_additional_behaviors-2870f3"
    #IF RUNNING NAO ON SAME LOCAL ADDRESS
    # ip = "nao.local"
    # port = 9559
    # virtual = False
    # additional_behaviors_folder = "nao_additional_behaviors-2870f3"
    #IF RUNNING THE VIRTUAL ROBOT ON CHOREOGRAPH
    ip = "localhost"
    port = 52497
    virtual = True
    additional_behaviors_folder = ".lastUploadedChoregrapheBehavior"

    nao_interface = NaoInterface(ip, port, virtual, additional_behaviors_folder)
    nao_interface.run()









