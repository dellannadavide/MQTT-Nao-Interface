import math
import time
import traceback

import utils.constants as Constants
from actuators.actuator import Actuator

import logging
logger = logging.getLogger("mqtt-nao-interface.actuators.posture.motion")

class MotionActuator(Actuator):
    """ An actuator of motions (e.g., head movements)"""
    def __init__(self, nao_interface, id, mqtt_topic, qi_app, virtual=False):
        super(MotionActuator, self).__init__(nao_interface, id, mqtt_topic, [Constants.NAO_SERVICE_MOTION], qi_app, virtual)
        self.speed = 0.3

    def actuate(self, directive_list):
        for directive in directive_list:
            splitted_directive = directive.split(Constants.STRING_SEPARATOR)
            logger.info(splitted_directive)
            logger.info(splitted_directive[0] == Constants.DIRECTIVE_MOVEHEAD)
            if splitted_directive[0] == Constants.DIRECTIVE_MOVEHEAD:
                if not self.nao_interface.is_looking and not self.nao_interface.is_moving:
                    self.nao_interface.is_looking = True
                    # self.nao_interface.is_moving = True
                    # in this case splitted_directive[1] is the "HeadYaw" value and splitted_directive[2] is the "HeadPitch" value
                    # values are assumed to be in angles
                    headpitch = (float(splitted_directive[1])*math.pi)/180.0
                    headyaw = (float(splitted_directive[2])*math.pi)/180.0
                    try:
                        self.services[Constants.NAO_SERVICE_MOTION].setAngles("HeadYaw", headyaw, self.speed)
                        self.services[Constants.NAO_SERVICE_MOTION].setAngles("HeadPitch", headpitch, self.speed)
                        time.sleep(3)
                        self.services[Constants.NAO_SERVICE_MOTION].setAngles("HeadYaw", 0.0, self.speed)
                        self.services[Constants.NAO_SERVICE_MOTION].setAngles("HeadPitch", 0.0, self.speed)
                    except Exception:
                        logger.warning(traceback.format_exc())
                        logger.warning("Could not perform directive "+str(splitted_directive))
                        pass
                    self.nao_interface.is_looking = False
                    # self.nao_interface.is_moving = False



