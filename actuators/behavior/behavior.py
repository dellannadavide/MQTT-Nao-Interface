import time
import traceback

import utils.constants as Constants
from actuators.actuator import Actuator

import logging
logger = logging.getLogger("mqtt-nao-interface.actuators.behavior.behavior")

class BehaviorActuator(Actuator):
    def __init__(self, nao_interface, id, mqtt_topic, qi_app, virtual=False):
        super(BehaviorActuator, self).__init__(nao_interface, id, mqtt_topic, [Constants.NAO_SERVICE_MEMORY,
                                                                Constants.NAO_SERVICE_BEHAVIOR_MANAGER],
                                               qi_app, virtual)
        self.events_to_subscribe_to = [Constants.NAO_EVENT_TRIGGER_LEARN_FACE]
        self.subscriber = {}
        for e in self.events_to_subscribe_to:
            self.subscriber[e] = self.services[Constants.NAO_SERVICE_MEMORY].subscriber(e)
            self.subscriber[e].signal.connect(self.on_event)

        self.getBehaviors()

    def actuate(self, directive):
        splitted_directive = directive.split(Constants.STRING_SEPARATOR)
        logger.info("actuate")
        self.services[Constants.NAO_SERVICE_MEMORY].raiseEvent(Constants.NAO_EVENT_TRIGGER_LEARN_FACE, "Davide")

    def on_event(self, value):
        logger.info("on event")
        logger.info(value)
        self.getBehaviors()


    def getBehaviors(self):
        """
        Know which behaviors are on the robot.
        """

        names = self.services[Constants.NAO_SERVICE_BEHAVIOR_MANAGER].getInstalledBehaviors()
        logger.info("Behaviors on the robot:")
        logger.info(names)

        names = self.services[Constants.NAO_SERVICE_BEHAVIOR_MANAGER].getRunningBehaviors()
        logger.info("Running behaviors:")
        logger.info(names)

    def launchAndStopBehavior(self, behavior_name):
        """
        Launch and stop a behavior, if possible.
        """
        # Check that the behavior exists.
        if (self.services[Constants.NAO_SERVICE_BEHAVIOR_MANAGER].isBehaviorInstalled(behavior_name)):
            # Check that it is not already running.
            if (not self.services[Constants.NAO_SERVICE_BEHAVIOR_MANAGER].isBehaviorRunning(behavior_name)):
                # Launch behavior. This is a blocking call, use _async=True if you do not
                # want to wait for the behavior to finish.
                self.services[Constants.NAO_SERVICE_BEHAVIOR_MANAGER].runBehavior(behavior_name, _async=True)
                time.sleep(0.5)
            else:
                logger.info("Behavior is already running.")

        else:
            logger.warning("Behavior not found.")
            return

        names = self.services[Constants.NAO_SERVICE_BEHAVIOR_MANAGER].getRunningBehaviors()
        logger.info("Running behaviors:")
        logger.info(names)

        # Stop the behavior.
        if (self.services[Constants.NAO_SERVICE_BEHAVIOR_MANAGER].isBehaviorRunning(behavior_name)):
            self.services[Constants.NAO_SERVICE_BEHAVIOR_MANAGER].stopBehavior(behavior_name)
            time.sleep(1.0)
        else:
            logger.info("Behavior is already stopped.")

        names = self.services[Constants.NAO_SERVICE_BEHAVIOR_MANAGER].getRunningBehaviors()
        logger.info("Running behaviors:")
        logger.info(names)

    def defaultBehaviors(self, behavior_name):
        """
        Set a behavior as default and remove it from default behavior.
        """

        # Get default behaviors.
        names = self.services[Constants.NAO_SERVICE_BEHAVIOR_MANAGER].getDefaultBehaviors()
        logger.info("Default behaviors:")
        logger.info(names)

        # Add behavior to default.
        self.services[Constants.NAO_SERVICE_BEHAVIOR_MANAGER].addDefaultBehavior(behavior_name)

        names = self.services[Constants.NAO_SERVICE_BEHAVIOR_MANAGER].getDefaultBehaviors()
        logger.info("Default behaviors:")
        logger.info(names)

        # Remove behavior from default.
        self.services[Constants.NAO_SERVICE_BEHAVIOR_MANAGER].removeDefaultBehavior(behavior_name)

        names = self.services[Constants.NAO_SERVICE_BEHAVIOR_MANAGER].getDefaultBehaviors()
        logger.info("Default behaviors:")
        logger.info(names)
