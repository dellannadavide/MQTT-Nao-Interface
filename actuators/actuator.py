import threading
import time
import traceback
from abc import abstractmethod
from utils.mqttclient import MQTTClient
from time import sleep
import utils.constants as Constants

import logging
logger = logging.getLogger("mqtt-nao-interface.actuators.actuator")

class Actuator(threading.Thread):
    """
    This class is used as a parent of subclasses representing actuators of the robot (e.g., a text to speech actuator).
    It extends threads so that every actuator can run in parallel.
    It instantiates, at creation, a class of mqtt client
    """
    def __init__(self, nao_interface, id, mqtt_topic, nao_services, qi_app=None, virtual=False):
        """
        Init function
        :param nao_interface: a pointer to the NaoInterface class
        :param id: an id (string) for the actuator
        :param mqtt_topic: a mqtt topic (string). the actuator will listen to messages on that topic to receive directives
        :param nao_services: the list of Nao services to which the actuator needs to connect
        :param qi_app: a pointer to the naoqi app
        :param virtual: a boolean indicating whether the interface is running with virtual (true) or real (false) robot
        """
        super(Actuator, self).__init__()
        self.is_paused = True
        self.nao_interface = nao_interface
        self.id = id
        self.app = qi_app
        self.requires_app = (not qi_app is None)
        self.virtual = virtual
        self.nao_services = nao_services
        self.services = {}
        self.connectServices()

        """ A buffer of received directives not yet processed"""
        self.received_directives = []

        self.mqtt_client = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAOInterface_MQTTListener_Actuator_"+self.id,
                                      Constants.MQTT_CLIENT_TYPE_LISTENER, mqtt_topic, self.on_message)

    def connectServices(self):
        """ Connects to all indicated services"""
        if not self.app is None:
            self.session = self.app.session
            self.services = {}
            for s in self.nao_services:
                try:
                    self.services[s] = self.session.service(s)
                except:
                    logger.warning("Cannot find service "+str(s))

    def on_message(self, client, userdata, message):
        """
         Function automatically called whenever a message is received on the specified MQTT topic.
         Whenever a directive is received, it is inserted in the self.received_directives list
         which acts as a buffer of directives to process
        :param client:
        :param userdata:
        :param message: the mqtt meessage, contains the directive
        :return:
        """
        rec_m = str(message.payload.decode("utf-8", errors="ignore"))
        logger.info("{} received message: {}".format(self.__class__.__name__, rec_m))
        self.received_directives.insert(0, rec_m)

    def getDirective(self):
        """
        Returns all directives contained in the buffer of directives yet to process.
        It removes them from the buffer.
        This function is called cyclically unless the actuator is paused
        :return:
        """
        directive_list_from_oldest = []
        nr_rec_in = len(self.received_directives)
        for i in range(nr_rec_in):
            b = self.received_directives.pop()
            directive_list_from_oldest.append(b)
        return directive_list_from_oldest


    def handleRUntimeException(self):
        """
        Propagates upwards a runtime exception
        :return:
        """
        self.nao_interface.handleRuntimeExceptions()

    def prepareToEnd(self):
        """ If specific actuators have other tasks to do, they will override this method and call it via super"""
        self.mqtt_client.stopLoop()
        self.mqtt_client.disconnect()

    def pause(self):
        """ Pauses the actuator """
        self.is_paused = True

    def unpause(self):
        """ Unpauses the actuator """
        self.is_paused = False

    def run(self):
        """
        As long as the actuator is not paused, this function is continuously executed.
        It retrieves the directives received in the last time period and actuates them.
        Actuation is actuator-specific, i.e., the method actuate is abstract and implemented by the specific actuators
        :return:
        """
        while True:
            if not self.is_paused:
                try:
                    directive_list = self.getDirective()
                    if len(directive_list) == 0:
                        pass
                    else:
                        self.actuate(directive_list)
                except RuntimeError:
                    logger.error(traceback.format_exc())
                    logger.error("Runtime or Key Error. Waiting 5 seconds and then rebooting...")
                    time.sleep(5)
                    self.handleRUntimeException()
                    # self.app = self.nao_interface.startQIAPP()
                    # self.connectServices()

    @abstractmethod
    def actuate(self, directive_list):
        pass

