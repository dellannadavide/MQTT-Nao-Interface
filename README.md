# MQTT-Nao-Interface: a Python 2.7 interface for the Nao robot based on MQTT
MQTT-Nao-Interface is a Python 2.7 resource that can be used to control a Nao robot via Python and that can receive commands (e.g., from [SONAR](https://github.com/dellannadavide/SONAR)) and publish data (e.g., captured via Nao's sensors) via MQTT.

Below the steps required to install and run MQTT-Nao-Interface.

## 1. Nao Softbank software, installation and setup
Software download page: https://www.aldebaran.com/fr/support/nao-6/downloads-softwares
- **Robot Settings**. Useful for checking and changing settings of Nao (e.g., wifi connection, or updates)
    > Verify installation by inserting Nao's IP address (press chest button on Nao to get it) and pressing Enter

- **Chorégraphe Suite**. Useful for creating and controlling behaviors for Nao; for installing behaviors on the robot; and for running the virtual robot.

  - Verify installation as follows:
    >1. Go to Connection -> Connect to...
    >2. Insert Nao's IP address (as per Robot Settings) in the field "Use fixed IP/hostname"
    >3. Nao should appear in the robot view
    >4. Try to execute a behavior: drag and drop from the Box libraries to the root field one animation (e.g.,the Animation->Moods->Positive->NAO->Happy animation), connect it to the onStart event, and press the green play button. Nao should execute the animation.
    
  - Setup the virtual robot as follows:
    >1. Go to Edit -> Preferences -> Virtual Robot
    >2. Select Robot model NAO H25 (V6)
    >3. Note on the bottom of the panel the **port on which NAOqi is running** (important for interfacing with Python) 
    >4. Press OK, then press Connection -> Connect to virtual robot
    >5. Press OK, then try to execute a behavior: drag and drop from the Box libraries to the root field one animation (e.g.,the Animation->Moods->Positive->NAO->Happy animation), connect it to the onStart event, and press the green play button. The virtual robot should execute the animation.

- **Python 2.7 NAOqi SDK**. Required to control Nao via Python.
  - Follow the installation instructions from Aldebaran [here](http://doc.aldebaran.com/2-8/dev/python/install_guide.html).

## 2. Basic services required to run MQTT-Nao-Interface

### 2.1. MQTT message broker
Communication between the (Python 2.7) MQTT-Nao-Interface and other external services (e.g., [SONAR](https://github.com/dellannadavide/SONAR)) happens via [MQTT](https://en.wikipedia.org/wiki/MQTT) (a lightweight method of carrying out messaging using a publish/subscribe model, and the standard messaging protocol for the Internet of Things). 

Below, it is reported a very quick tutorial on how to install [Eclipse Mosquitto](https://mosquitto.org/), an open source message broker that implements the MQTT protocol, on an Ubuntu distro installed on Windows WSL.

#### 2.1.1. Install Linux on Windows with WSL (see [Microsoft guidelines](https://learn.microsoft.com/en-us/windows/wsl/install))
>1. Open Windows PowerShell with admin rights
>2. Run ``` wsl --install ```
>3. Reboot the system 
>4. Open Microsoft Store and type and get Ubuntu
>5. Follow the instruction in the Ubuntu terminal to create a new UNIX user account.
>6. Run ``` sudo apt update && sudo apt upgrade```  to update packages.

#### 2.2.2. Install and start Mosquitto on Ubuntu
>1. In the Ubuntu terminal, as per step 6 of Sec 2.1.1., add the mosquitto-dev PPA by running first ```sudo apt-add-repository ppa:mosquitto-dev/mosquitto-ppa``` and then ```sudo apt-get update```.
>2. To install Mosquitto, run ``` sudo apt install mosquitto ``` and type ```Y``` when requested.
>3. To start Mosquitto, run ``` sudo service mosquitto start ```



## 3. Setup the MQTT-Nao-Interface
### 3.1. Required software and libraries
MQTT-Nao-Interface is a python resource that runs on Python 2.7. Therefore the basic requirement is [Python 2.7](https://www.python.org/downloads/).

Secondly, the MQTT-Nao-Interface needs the Python 2.7 NAOqi SDK. See section 1 for details on installation.

The MQTT-Nao-Interface also requires a number of Python packages to be installed. 
The list of requirements can be found in the ```requirements.txt``` file. 
A standard way to install all required libraries is to run command ```pip install -r /path/to/requirements.txt```. 
Based on your environment you may adopt the most handy procedure.

MQTT-Nao-Interface relies on an MQTT broker. Follow steps in Section 2 to install it.

Finally, please download in folder ```MQTT-Nao-Interface/sensors/video/data``` the following files (they are not provided to avoid overloading the repository):
- The pre-trained YOLO3 weight file ```yolov3.weights``` (used for object recognition with the COCO dataset). 
You can find the file [here (237 MB)](https://pjreddie.com/media/files/yolov3.weights), or follow the instructions from the [YOLO webpage](https://pjreddie.com/darknet/yolo/) to download it in other ways.
- The pre-trained YOLO3 weight file ```yolov3-hat_2400.weights``` (used for recognition of an helmet/hat). 
You can find the file [here (240 MB)](https://github.com/BlcaKHat/yolov3-Helmet-Detection) in the link called "model". Note that in the linked repository the file that will be downloaded is named ```yolov3-obj_2400.weights```, so please rename it as indicated above.
- The pre-trained shape predictor model ```shape_predictor_68_face_landmarks.dat``` (used for face detection and tracking). You can find a compressed archive version of the file [here (100 MB)](http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2). You need to decompress the file and place the ```.dat``` file in the folder mentioned above.
- The pre-trained model ```emotion-ferplus-8.onnx``` for emotion recognition from faces. You can find it [here (34 MB)](https://github.com/onnx/models/blob/main/vision/body_analysis/emotion_ferplus/model/emotion-ferplus-8.onnx).


### 3.2. Setup and Run
#### 3.2.1. Upload additional behaviors on Nao
[SONAR](https://github.com/dellannadavide/SONAR) can instruct the MQTT-Nao-Interface to execute a number of non-default behaviors on Nao (e.g., some particular movements).
These behaviors can be found in folder ```MQTT-Nao-Interface/lib/Nao_Additional_Behaviors```, which contains a Choreographe project.
In order to upload them on Nao and/or on a virtual robot follow the next steps.
>1. Open Choreographe
>2. Open the project (File -> Open project) contained in the ```Nao_Additional_Behaviors``` folder.
>3. In the ```Robot applications``` panel in Choreographe press the button ```Package and install current project to the robot```. An entry named ```Nao_Additional_Behaviors``` should appear in the list of applications of the robot.
>4. Run, on Choreographe, one of the behaviors (e.g., open ```behaviors/anger/behavior.xar``` and press play after connecting to the (virtual) robot). By doing so all behaviors in the project will be also automatically loaded in the ```.lastUploadedChoreographeBehavior``` application, which is the only application available to the virtual robot.


#### 3.2.1 Run MQTT-Nao-Interface
>1. Start Mosquitto as per section 2.2.1
>2. Turn on Nao, or connect to a virtual robot.
>3. Determine the IP and port of the robot. For Nao, press the chest to obtain its IP address (the default port is ```9559```). For the virtual robot in Choreographe, the IP is ```localhost``` if Choreographe is running on the same machine as the MQTT-Nao-Interface, and the port can be found in the preferences as per Section 1.
>4. Assign the correct IP and port to variables ```ip``` and ```port``` in module ```MQTT-Nao-Interface/main.py```.
>5. Run MQTT-Nao-Interface via ```python MQTT-Nao-Interface/main.py```.




## 4. Mini-Tutorial: Create a new MQTT-Nao-Interface sensor (Object Recognition using Nao buil-in functionality)
In this section we will see how to create a new sensor class which interfaces with NaoQi to collect data from the robot and publishes the collected data to the MQTT broker.

We will use, as an example, a sensor that meant to deal with objects recognition.
Nao has built in functionality, which can be accessed via Choreographe, that allows it to quickly learn new objects. Follow [this tutorial](http://doc.aldebaran.com/2-8/software/choregraphe/tutos/recognize_objects.html#choregraphe-tuto-learn-object) to know how.

In the following, it is assumed that Nao has learned at least one object.

In order to create a new MQTT-Nao-Interface ```sensor``` follow the next steps (note that analogous procedure holds for ```actuators```).
### 4.1. Create a new python module in the ```MQTT-Nao-Interface/sensors/<appropriate_folder>/```.
For our example, we create a module ```detectobject.py``` in folder ```MQTT-Nao-Interface/sensors/video/```.
### 4.2. In the newly created module, define a new class, representing the sensor, and extending the superclass ```Sensor```. 
For our example, we define and initialize a class ```VisionRecognition``` as follows. 
```
class VisionRecognition(Sensor):
""" A simple class to react to object detection events. """
def __init__(self, nao_interface, id, mqtt_topic, freq, qi_app=None):
    super(BuiltInObjectDetector, self).__init__(nao_interface, id, mqtt_topic, [Constants.NAO_SERVICE_MEMORY,
                                                         Constants.NAO_SERVICE_VISION_RECOGNITION], freq, qi_app)
    self.subscribeToServices()
    self.last_detected_object = ""

def subscribeToServices(self):
    self.subscriber = self.services[Constants.NAO_SERVICE_MEMORY].subscriber(Constants.NAO_EVENT_PICTURE_DETECTED)
    self.subscriber.signal.connect(self.on_picture_detected)
    self.subscribe(Constants.NAO_SERVICE_VISION_RECOGNITION, self.id)
```

In the initialization, we call the constructor of the super class by indicating the reference to the ```NaoInterface``` class (```nao_interface```), an id for the sensor class (```id```), the MQTT topic on which the sensor will publish data (```mqtt_topic```), a list of NAOqi service to which we intend to subscribe (```[...]```, note that this list is sensor-specific), the frequency at which we desire the sensor to publish new data (if any) to the MQTT broker (```freq```), and finally a reference to the NAOqi Application (```qi_app```) instantiated in the ```NaoInterface```.

For our example, the list of services that we are interested into includes ```NAO_SERVICE_MEMORY``` and ```NAO_SERVICE_VISION_RECOGNITION``` (i.e., ```"ALMemory"``` and ```"ALVisionRecognition"```, respectively).
    
Furthermore, in the initialization, we invoke function ```subscribeToServices()```, which is also sensor-specific (i.e., it needs to be defined for the particular sensor class), and subscribes the class to events generated by relevant services.
    
In the case of the ```ALVisionRecognition```, the name of the event generated by the service is ```PictureDetected``` (referred below as ```NAO_EVENT_PICTURE_DETECTED```).
    
Note that the signal from the event is connected to a callback class function ```on_picture_detected``` to be defined.

Finally, note that during initialization we are creating a variable ```last_detected_object```, which will be used to store the detected objects (we keep the example for this tutorial simple, but more complex management of sensor data can be introduced)

    
### 4.3. Define the callback class function ```on_picture_detected```.
This function will be invoked every time an object is detected.
The function takes one parameter in input, i.e., the value contained in the event.
```
    def on_picture_detected(self, value):
        """
        Callback for event PictureDetected.
        """
        # Here place your code.
        # Simple example:
        print(value)
        self.last_detected_object = value
```

Note that in the example above, we are directly assigning the value returned by the event to the variable ```last_detected_object```.

However such a value does not only contain the name of the object detected but also several other information.

Please refer to [ALVisionRecognition](http://doc.aldebaran.com/2-8/naoqi/vision/alvisionrecognition.html#alvisionrecognition) for details on the content of the variable.

Note also that event ```PictureDetected``` is raised also when an object that is currently being detected disappears. In this case the content of value will be an empty list (if no object is visible).


### 4.4. Define the class function ```sense```.
This function will be regularly (at a frequency given by the class instance attribute ```freq```) invoked. See the ```run``` function of the superclass ```Sensor``` for more details.
The function should return a string to be published to the MQTT broker on topic ```mqtt_topic```.
If no message should be published, the function should return value ```None```.
```
    def sense(self):
        if self.last_detected_object=="":
            return None
        return self.last_detected_object
```

### 4.5. Instantiate and start the class in the ```NaoInterface``.
In the ```run``` function of the ```NaoInterface``` class in module ```MQTT-Nao-Interface/main.py```,
add a new instance of the new ```VisionRecognition``` in the dictionary containing the services of the nao interface (i.e., to the dictionary ```self.services```) for the case of real robot (i.e., if ```not self.virtual``` is true).

Since we are using built-in features of Nao, this service can only work with the real robot and not with the virtual one.

It is also possible to create other services that do not rely on the built-in features of Nao in an analogous way (see the already implemented set of services for examples).

```
self.services = {
    # SENSORS
    # ... other sensors ...
    "VisionRecognition": VisionRecognition(self, "VisionRecognition", Constants.TOPIC_OBJECT_DETECTION, 1, self.app),
    # ... other sensors ...
    
    # ACTUATORS
    # ... actuators
}
```

### 4.6. Test
Test the sensor by executing steps from section 3.2.1. For this example you need to connect to the real robot.
