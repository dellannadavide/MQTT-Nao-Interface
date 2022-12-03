import time
import traceback

import utils.constants as Constants
from actuators.actuator import Actuator

import logging
logger = logging.getLogger("mqtt-nao-interface.actuators.posture.posture")

class PostureActuator(Actuator):
    def __init__(self, nao_interface, id, mqtt_topic, qi_app, virtual=False):
        super(PostureActuator, self).__init__(nao_interface, id, mqtt_topic, [Constants.NAO_SERVICE_POSTURE, Constants.NAO_SERVICE_ANIMATION_PLAYER], qi_app, virtual)
        self.speed = 0.8

    def actuate(self, directive_list):
        directive = directive_list[-1] # note: if there is more than one in the list, instead of executing all of them, in the case of posture, I only execute the most recent, because they take a while, so it does not make sense to coumulate them
        #
        # for directive in directive_list:
        splitted_directive = directive.split(Constants.STRING_SEPARATOR)
        logger.info(splitted_directive)
        logger.info(splitted_directive[0] == Constants.DIRECTIVE_GOTOPOSTURE)
        if not self.nao_interface.is_moving:
            self.nao_interface.is_moving = True
            if splitted_directive[0] == Constants.DIRECTIVE_GOTOPOSTURE:
                posture = str(splitted_directive[1])
                try:
                    self.services[Constants.NAO_SERVICE_POSTURE].goToPosture(posture, self.speed)
                except Exception:
                    logger.warning(traceback.format_exc())
                    logger.warning("Could not perform directive "+str(splitted_directive))
                    pass
            if splitted_directive[0] == Constants.DIRECTIVE_PLAYANIMATION:
                animation = str(splitted_directive[1]) #

                try:
                    if self.virtual:
                        # in case of virtual robot no default animation can be called unless a specific behavior is created and is in .lastUploadedChoregrapheBehavior
                        # (at least as far as I understood from https://stackoverflow.com/questions/66444226/pepper-animations-not-working-in-simulation-using-python-sdk)
                        self.services[Constants.NAO_SERVICE_ANIMATION_PLAYER].run(Constants.ADDITIONAL_BEHAVIORS_FOLDER+"/behaviors/"+animation, _async=False)
                    else:
                        animation_path = ""
                        if animation in Constants.NAO_DEFAULT_ANIMATIONS_PATHS.keys():  # if the animation is one of the default ones (e.g., Hey_1) already installed in Nao
                            animation_path = Constants.NAO_DEFAULT_ANIMATIONS_PATHS[animation]
                        else:  # otherwise the behavior, I guess will be installed in a folder that we pupt called behaviors
                            animation_path = Constants.ADDITIONAL_BEHAVIORS_FOLDER+"/behaviors/" + animation
                        self.services[Constants.NAO_SERVICE_ANIMATION_PLAYER].run(animation_path, _async=False)
                    # wait the end of the animation
                    # future.value()
                except Exception:
                    logger.warning(traceback.format_exc())
                    logger.warning("Could not perform directive "+str(splitted_directive))
                    pass

                try:
                    self.services[Constants.NAO_SERVICE_POSTURE].goToPosture("Stand", self.speed)
                except Exception:
                    logger.warning(traceback.format_exc())
                    logger.warning("Could not perform directive "+str(splitted_directive))
                    pass

            self.nao_interface.is_moving = False
