import traceback

import utils.constants as Constants
from actuators.actuator import Actuator

import logging
logger = logging.getLogger("mqtt-nao-interface.actuators.system.leds")

class Leds(Actuator):
    def __init__(self, nao_interface, id, mqtt_topic, qi_app):
        super(Leds, self).__init__(nao_interface, id, mqtt_topic, [Constants.NAO_SERVICE_LEDS], qi_app)
        self.initial_color = Constants.COLORS_WHITE
        self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLeds", 1.0)
        self.current_color = self.initial_color
        self.thinking_color = Constants.COLORS_BLUE

    def setThinking(self, thinking):
        if thinking:
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsGreen", 0.0)
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsBlue", 1.0)
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsRed", 0.0)
            self.current_color = self.thinking_color
            self.nao_interface.is_thinking = True
        else:
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLeds", 1.0)
            self.current_color = self.initial_color
            self.nao_interface.is_thinking = False

    def setColorExternal(self, color):
        if color==self.thinking_color:
            self.setThinking(True)
        elif color==self.initial_color:
            self.setThinking(False)
        else:
            self.setColorInner(color)

    def setColorInner(self, color):
        if color == Constants.COLORS_WHITE:
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLeds", 1.0)
            self.current_color = color
        elif color == Constants.COLORS_BLUE:
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsGreen", 0.0)
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsBlue", 1.0)
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsRed", 0.0)
            self.current_color = color
        elif color == Constants.COLORS_GREEN:
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsGreen", 1.0)
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsBlue", 0.0)
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsRed", 0.0)
            self.current_color = color
        elif color == Constants.COLORS_RED:
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsGreen", 0.0)
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsBlue", 0.0)
            self.services[Constants.NAO_SERVICE_LEDS].setIntensity("ChestLedsRed", 1.0)
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

    def actuate(self, directive):
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
                thinking = bool(splitted_directive[1])
                self.setThinking(thinking)

        except Exception:
            logger.warning(traceback.format_exc())
            logger.warning("Could not perform directive "+str(splitted_directive)+". If connected to virtual robot: cannot use leds")
            pass
