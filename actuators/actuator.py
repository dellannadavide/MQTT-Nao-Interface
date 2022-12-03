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
    def __init__(self, nao_interface, id, mqtt_topic, nao_services, qi_app=None, virtual=False):
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


        self.received_directives = []

        self.mqtt_client = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAOInterface_MQTTListener_Actuator_"+self.id,
                                      Constants.MQTT_CLIENT_TYPE_LISTENER, mqtt_topic, self.on_message)

    def connectServices(self):
        if not self.app is None:
            self.session = self.app.session
            self.services = {}
            for s in self.nao_services:
                try:
                    self.services[s] = self.session.service(s)
                except:
                    logger.warning("Cannot find service "+str(s))

    def on_message(self, client, userdata, message):
        rec_m = str(message.payload.decode("utf-8"))
        logger.info("{} received message: {}".format(self.__class__.__name__, rec_m))
        self.received_directives.insert(0, rec_m)

    def getDirective(self):
        directive_list_from_oldest = []
        nr_rec_in = len(self.received_directives)
        for i in range(nr_rec_in):
            b = self.received_directives.pop()
            directive_list_from_oldest.append(b)
        return directive_list_from_oldest


    def handleRUntimeException(self):
        self.nao_interface.handleRuntimeExceptions()

    def prepareToEnd(self):
        """ If specific actuators have other tasks to do, they will override this method and call it via super"""
        self.mqtt_client.stopLoop()
        self.mqtt_client.disconnect()

    def pause(self):
        self.is_paused = True

    def unpause(self):
        self.is_paused = False

    def run(self):
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

