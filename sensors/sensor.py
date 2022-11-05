import threading
import traceback
from abc import abstractmethod
from utils.mqttclient import MQTTClient
import utils.constants as Constants
import time


class Sensor(threading.Thread):
    def __init__(self, nao_interface, id, mqtt_topic, nao_services, freq, qi_app=None, virtual=False):
        super(Sensor, self).__init__()
        self.is_paused = False
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
        if not self.app is None:
            self.session = self.app.session
            self.services = {}
            for s in self.nao_services:
                try:
                    self.services[s] = self.session.service(s)
                except:
                    print("WARNING: Cannot find service " + str(s))

    def subscribe(self, name_service, name_subscriber, *args):
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
        self.nao_interface.handleRuntimeExceptions()

    def prepareToEnd(self):
        """ If specific sensors have other tasks to do, they will override this method and call it via super"""
        self.mqtt_client.stopLoop()
        self.mqtt_client.disconnect()
        for service in self.subscribers_to_services.keys():
            for subscriber in self.subscribers_to_services[service]:
                self.services[service].unsubscribe(subscriber)

    def pause(self):
        self.is_paused = True

    def unpause(self):
        self.is_paused = False

    def run(self):
        while True:
            if not self.is_paused:
                data_to_publish = None
                try:
                    data_to_publish = self.sense()
                except (RuntimeError, KeyError) as re:
                    print(traceback.format_exc())
                    print("Runtime or Key Error. Waiting 5 seconds and then rebooting...")
                    time.sleep(5)
                    self.handleRUntimeException()
                    # self.app = self.nao_interface.startQIAPP()
                    # self.connectServices()
                    # self.subscribeToServices()
                except:
                    print(traceback.format_exc())
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
