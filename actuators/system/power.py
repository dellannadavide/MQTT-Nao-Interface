import traceback

import utils.constants as Constants
from actuators.actuator import Actuator


class Power(Actuator):
    def __init__(self, nao_interface,  id, mqtt_topic, qi_app):
        super(Power, self).__init__(nao_interface, id, mqtt_topic, [Constants.NAO_SERVICE_SYSTEM], qi_app)

    def actuate(self, directive):
        splitted_directive = directive.split(Constants.STRING_SEPARATOR)
        if splitted_directive[0] == Constants.DIRECTIVE_SHUT_DOWN:
            try:
                system = self.session.service("ALSystem")
                system.shutdown()
            except Exception:
                print(traceback.format_exc())
                print("Could not perform directive "+str(splitted_directive)+". If connected to virtual robot: cannot shut a virtual robot down.")
                pass
