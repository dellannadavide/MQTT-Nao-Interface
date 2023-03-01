import time
import traceback

import utils.constants as Constants
from actuators.actuator import Actuator

import logging
logger = logging.getLogger("mqtt-nao-interface.actuators.system.leds")

class Leds(Actuator):
    """ Leds actuator. Processes (internal and external) direcctives that change the color of Nao's leds """
    def __init__(self, nao_interface, id, mqtt_topic, qi_app):
        super(Leds, self).__init__(nao_interface, id, mqtt_topic, [Constants.NAO_SERVICE_LEDS], qi_app)
        self.initial_color = Constants.COLORS_RED
        self.default_color = Constants.COLORS_WHITE
        self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLeds", 1.0)
        self.current_color = self.initial_color
        self.thinking_color = Constants.COLORS_BLUE

        self.setColorInner(self.initial_color)

    def setSleeping(self, sleeping):
        if sleeping:
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("FaceLeds", 0.0)
        else:
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("FaceLeds", 1.0)

    def setThinking(self, thinking):
        """
        When thinking is true, the chest is blue
        :param thinking:
        :return:
        """
        # print("in setthinking", thinking)
        self.nao_interface.is_thinking = thinking
        self.nao_interface.last_thinking_time = time.time()
        if thinking:
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsGreen", 0.0)
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsBlue", 1.0)
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsRed", 0.0)
            self.current_color = self.thinking_color
        else:
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLeds", 1.0)
            self.current_color = Constants.COLORS_WHITE

    def setColorExternal(self, color):
        if color==self.thinking_color:
            self.setThinking(True)
        elif color==self.default_color:
            self.setThinking(False)
        else:
            self.setColorInner(color)

    def setColorInner(self, color):
        max_intensity = 1.0
        if self.nao_interface.is_sleeping:
            max_intensity = 0.5
        if color == Constants.COLORS_WHITE:
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLeds", max_intensity)
            self.current_color = color
        elif color == Constants.COLORS_BLUE:
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsGreen", 0.0)
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsBlue", max_intensity)
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsRed", 0.0)
            self.current_color = color
        elif color == Constants.COLORS_GREEN:
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsGreen", max_intensity)
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsBlue", 0.0)
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsRed", 0.0)
            self.current_color = color
        elif color == Constants.COLORS_RED:
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsGreen", 0.0)
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsBlue", 0.0)
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsRed", max_intensity)
            self.current_color = color
        elif color == Constants.COLORS_YELLOW:
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsGreen", max_intensity)
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsBlue", 0.0)
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsRed", max_intensity)
            self.current_color = color
        else:
            logger.warning("Color " + str(color) +" unknown.")

    def setColor(self, color, external_command=False):
        try:
            if external_command:
                self.setColorExternal(color)
            else:
                if not self.nao_interface.is_thinking:
                    self.setColorInner(color)
        except RuntimeError:
            self.handleRUntimeException()

    def actuate(self, directive_list):
        for directive in directive_list:
            logger.debug("Actuatinig directive {}".format(directive))
            splitted_directive = directive.split(Constants.STRING_SEPARATOR)
            try:
                if splitted_directive[0] == Constants.DIRECTIVE_LED_CHANGE_COLOR:
                    if self.current_color=="white":
                        self.setColor("blue",external_command=True)
                        # self.thinking_color = True
                    else:
                        #important here to set first the thinking false
                        # self.thinking_color = False
                        self.setColor("white", external_command=True)
                if splitted_directive[0] == Constants.DIRECTIVE_LED_SET_COLOR:
                    new_col = splitted_directive[1]
                    self.setColor(new_col, external_command=True)

                if splitted_directive[0] == Constants.DIRECTIVE_LED_SET_THINKING:
                    thinking = (splitted_directive[1] == "True")
                    logger.debug("setting thinking to {}".format(thinking))
                    self.setThinking(thinking)

            except Exception:
                logger.warning(traceback.format_exc())
                logger.warning("Could not perform directive "+str(splitted_directive)+". If connected to virtual robot: cannot use leds")
                pass
