#! /usr/bin/env python
# -*- encoding: UTF-8 -*-

"""Example: A Simple class to get info about face position"""
from datetime import datetime

import cv2
import numpy as np
import qi
import time
import sys
import argparse


import paho.mqtt.client as mqtt
from random import randrange, uniform
import time

from PIL import Image

import utils.constants as Constants
from utils.util import joinStrings
from sensors.sensor import Sensor
from utils.mqttclient import MQTTClient
import vision_definitions
import dlib  # Machine learning library
import imutils  # OpenCV assistance
from imutils import face_utils

import logging
logger = logging.getLogger("mqtt-nao-interface.sensors.video.object_detectorHAT")

class ObjectDetectorHAT(Sensor):
    """
    A simple class to compute data about face position
    """

    def __init__(self, nao_interface, id, mqtt_topic, freq, qi_app=None, virtual=False):
        super(ObjectDetectorHAT, self).__init__(nao_interface, id, mqtt_topic, [], freq, qi_app, virtual)

        # if self.virtual:
        #     """ In case of virtual robot, it is assumed it can be used the camera of the laptop """
        #     self._cameraID = 0
        #     self.capture = cv2.VideoCapture(self._cameraID)
        # else:
        #     self.resolution = vision_definitions.kQVGA#.k960p#.kQVGA  # 320 * 240
        #     self.colorSpace = vision_definitions.kRGBColorSpace
        #
        #     self.fps = 5
        #     self._imgClient = self.subscribe(Constants.NAO_SERVICE_VIDEO, "ObjectDetector", self.resolution, self.colorSpace, self.fps)

        self.lastImage = None

        self.data_folder = "sensors/video/data/"

        # set of 80 class labels
        self.class_labels = ["helmet"]

        # Declare List of colors as an array
        # Green, Blue, Red, cyan, yellow, purple
        # Split based on ',' and for every split, change type to int
        # convert that to a numpy array to apply color mask to the image numpy array
        self.class_colors = ["0,255,0", "0,0,255", "255,0,0", "255,255,0", "0,255,255"]
        self.class_colors = [np.array(every_color.split(",")).astype("int") for every_color in self.class_colors]
        self.class_colors = np.array(self.class_colors)
        self.class_colors = np.tile(self.class_colors, (16, 1))

        # Loading pretrained model
        # input preprocessed blob into model and pass through the model
        # obtain the detection predictions by the model using forward() method
        self.yolo_model = cv2.dnn.readNetFromDarknet(self.data_folder+'yolov3-hat.cfg', self.data_folder+'yolov3-hat_2400.weights')

        # Get all layers from the yolo network
        # Loop and find the last layer (output layer) of the yolo network
        self.yolo_layers = self.yolo_model.getLayerNames()

        self.yolo_output_layer = [self.yolo_layers[yolo_layer[0] - 1] for yolo_layer in
                             self.yolo_model.getUnconnectedOutLayers()]





    def sense(self):
        # frame = None
        # if self.virtual:
        #     ret, frame = self.capture.read()
        #     self.lastImage = frame
        # else:
        #     self.lastImage = self.services[Constants.NAO_SERVICE_VIDEO].getImageRemote(self._imgClient)
        self.lastImage, gray = self.nao_interface.services["NaoImageCollector"].getLastFrame()

        if not self.lastImage is None:
            # if not self.virtual:
            #     imageWidth = self.lastImage[0]
            #     imageHeight = self.lastImage[1]
            #     array = self.lastImage[6]
            #     image_string = str(bytearray(array))
            #     pil_image = Image.frombytes("RGB", (imageWidth, imageHeight), image_string)
            #     open_cv_image = np.array(pil_image)
            #     # Convert RGB to BGR
            #     frame = open_cv_image[:, :, ::-1].copy()

            # img_height = self.lastImage.shape[0]
            # img_width = self.lastImage.shape[1]

            # convert image to blob to pass into model
            img_blob = cv2.dnn.blobFromImage(self.lastImage, 0.003922, (320, 320), swapRB=True, crop=False)
            # recommended by yolo authors, scale factor is 0.003922=1/255, width,height of blob is 320,320
            # accepted sizes are 320x320, 416x416, 609x609. More size means more accuracy but less speed

            # input preprocessed blob into model and pass through the model
            self.yolo_model.setInput(img_blob)
            # obtain the detection layers by forwarding through till the output layer
            obj_detection_layers = self.yolo_model.forward(self.yolo_output_layer)

            print(obj_detection_layers)

            detected_objects = []
            # loop over each of the layer outputs
            for object_detection_layer in obj_detection_layers:
                # loop over the detections
                for object_detection in object_detection_layer:

                    # obj_detections[1 to 4] => will have the two center points, box width and box height
                    # obj_detections[5] => will have scores for all objects within bounding box
                    all_scores = object_detection[5:]
                    predicted_class_id = np.argmax(all_scores)
                    prediction_confidence = all_scores[predicted_class_id]

                    # take only predictions with confidence more than x
                    if prediction_confidence > 0.00:
                        # get the predicted label
                        predicted_class_label = self.class_labels[predicted_class_id]
                        # obtain the bounding box co-oridnates for actual image from resized image size
                        # bounding_box = object_detection[0:4] * np.array(
                        #     [img_width, img_height, img_width, img_height])
                        # (box_center_x_pt, box_center_y_pt, box_width, box_height) = bounding_box.astype("int")
                        # start_x_pt = int(box_center_x_pt - (box_width / 2))
                        # start_y_pt = int(box_center_y_pt - (box_height / 2))
                        # end_x_pt = start_x_pt + box_width
                        # end_y_pt = start_y_pt + box_height
                        #
                        # # get a random mask color from the numpy array of colors
                        # box_color = self.class_colors[predicted_class_id]
                        #
                        # # convert the color numpy array as a list and apply to text and box
                        # box_color = [int(c) for c in box_color]

                        # print the prediction in console
                        detected_objects.append(predicted_class_label)
                        predicted_class_label = "{}: {:.2f}%".format(predicted_class_label,
                                                                     prediction_confidence * 100)
                        logger.info("predicted object {}".format(predicted_class_label))


                        # # draw rectangle and text in the image
                        # cv2.rectangle(frame, (start_x_pt, start_y_pt), (end_x_pt, end_y_pt), box_color, 1)
                        # cv2.putText(frame, predicted_class_label, (start_x_pt, start_y_pt - 5),
                        #             cv2.FONT_HERSHEY_SIMPLEX,
                        #             0.5, box_color, 1)

            if len(detected_objects)==0:
                return None
            ret_val = joinStrings(detected_objects, Constants.STRING_SEPARATOR_INNER)
            return ret_val
        else:
            return None





