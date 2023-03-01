import threading
import traceback
from abc import abstractmethod
from utils.mqttclient import MQTTClient
import utils.constants as Constants
import time

import logging
logger = logging.getLogger("mqtt-nao-interface.sensors.sensor")

class Sensor(threading.Thread):
    """
        This class is used as a parent of subclasses representing sensors of the robot (e.g., microphone).
        It extends threads so that every sensor can run in parallel.
        It instantiates, at creation, a class of mqtt client where sensors publish collected and processed data
    """
    def __init__(self, nao_interface, id, mqtt_topic, nao_services, freq, qi_app=None, virtual=False):
        """
        Init function
        :param nao_interface: a pointer to the NaoInterface class
        :param id: an id (string) for the actuator
        :param mqtt_topic: a mqtt topic (string). the sensor will publish messages on that topic to communicate data
        :param nao_services: the list of Nao services to which the sensor needs to subscribe to collect data
        :param freq: the frequency at which the sensor detects data
        :param qi_app: a pointer to the naoqi app
        :param virtual: a boolean indicating whether the interface is running with virtual (true) or real (false) robot
        """
        super(Sensor, self).__init__()
        self.is_paused = True
        self.nao_interface = nao_interface
        self.id = id
        self.app = qi_app
        self.requires_app = (not qi_app is None)
        self.virtual = virtual
        self.mqtt_topic = mqtt_topic
        self.freq = freq
        self.nao_services = nao_services
        self.services = {}
        self.connectServices()
        self.subscribers_to_services = {}


        self.mqtt_client = MQTTClient(Constants.MQTT_BROKER_ADDRESS, "NAOInterface_MQTTPublisher_Sensor_" + self.id,
                                      Constants.MQTT_CLIENT_TYPE_PUBLISHER, None, None)
        self.mqtt_client.startLoop()

    def connectServices(self):
        """ Connects to all indicated services"""
        if not self.app is None:
            self.session = self.app.session
            self.services = {}
            for s in self.nao_services:
                try:
                    self.services[s] = self.session.service(s)
                except:
                    logger.warning("Cannot find service " + str(s))

    def subscribe(self, name_service, name_subscriber, *args):
        """
        Subscribes to one nao service
        :param name_service: name of the service
        :param name_subscriber: id of the subscriber
        :param args: arguments for the service
        :return: a reference to the service, or None
        """
        try:
            subs = self.services[name_service].getSubscribers()
            for s in subs:
                if str(s).startswith(name_subscriber):
                    self.services[name_service].unsubscribe(s)

            if name_service in self.subscribers_to_services.keys():
                self.subscribers_to_services[name_service].append(name_subscriber)
            else:
                self.subscribers_to_services[name_service] = [name_subscriber]

            return self.services[name_service].subscribe(name_subscriber, *args)
        except:
            pass
        return None


    def handleRUntimeException(self):
        """
        Propagates upwards a runtime exception
        :return:
        """
        self.nao_interface.handleRuntimeExceptions()

    def prepareToEnd(self):
        """ If specific sensors have other tasks to do, they will override this method and call it via super"""
        self.mqtt_client.stopLoop()
        self.mqtt_client.disconnect()
        for service in self.subscribers_to_services.keys():
            for subscriber in self.subscribers_to_services[service]:
                self.services[service].unsubscribe(subscriber)

    def pause(self):
        """ Pauses the sensor """
        self.is_paused = True

    def unpause(self):
        """ Unpauses the sensor """
        self.is_paused = False

    def run(self):
        """
        As long as the sensor is not paused, this function is continuously executed at intervals of self.freq seconds
        At every execution, it executes function self.sense() to collect data, and publishes collected data to the
        mqtt topic.
        self.sense() is sensor-specific, i.e., the method is abstract and implemented by the specific sensors
        :return:
        """
        while True:
            if not self.is_paused:
                data_to_publish = None
                try:
                    data_to_publish = self.sense()
                except (RuntimeError, KeyError) as re:
                    logger.error(traceback.format_exc())
                    logger.error("Runtime or Key Error. Waiting 5 seconds and then rebooting...")
                    time.sleep(5)
                    self.handleRUntimeException()
                except:
                    logger.warning(traceback.format_exc())
                    pass

                if not data_to_publish is None and not self.mqtt_topic is None:
                    self.mqtt_client.publish(self.mqtt_topic, data_to_publish)
            time.sleep(self.freq)

    @abstractmethod
    def sense(self):
        pass

    @abstractmethod
    def subscribeToServices(self):
        pass
