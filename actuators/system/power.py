import traceback

import utils.constants as Constants
from actuators.actuator import Actuator

import logging
logger = logging.getLogger("mqtt-nao-interface.actuators.system.power")

class Power(Actuator):
    def __init__(self, nao_interface,  id, mqtt_topic, qi_app, virtual):
        super(Power, self).__init__(nao_interface, id, mqtt_topic, [Constants.NAO_SERVICE_SYSTEM, Constants.NAO_SERVICE_AUTONOMOUS_LIFE], qi_app, virtual)
        self.wake_up()

    def wake_up(self):
        try:
            self.services[Constants.NAO_SERVICE_AUTONOMOUS_LIFE].setState("solitary")
        except:
            logger.warning(traceback.format_exc())

    def sleep(self):
        try:
            self.services[Constants.NAO_SERVICE_AUTONOMOUS_LIFE].setState("disabled")
        except:
            logger.warning(traceback.format_exc())

    def actuate(self, directive_list):
        for directive in directive_list:
            splitted_directive = directive.split(Constants.STRING_SEPARATOR)
            if splitted_directive[0] == Constants.DIRECTIVE_SHUT_DOWN:
                try:
                    system = self.session.service("ALSystem")
                    system.shutdown()
                except Exception:
                    logger.warning(traceback.format_exc())
                    logger.warning("Could not perform directive "+str(splitted_directive)+". If connected to virtual robot: cannot shut a virtual robot down.")
                    pass
            if splitted_directive[0] == Constants.DIRECTIVE_SLEEP:
                self.nao_interface.setSleeping(True)

