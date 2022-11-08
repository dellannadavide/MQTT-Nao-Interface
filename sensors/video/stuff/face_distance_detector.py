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

class FaceDistanceDetector(Sensor):
    """
    A simple class to compute data about face position
    """

    def __init__(self, nao_interface, id, mqtt_topic, freq, qi_app=None):
        super(FaceDistanceDetector, self).__init__(nao_interface, id, mqtt_topic, [Constants.NAO_SERVICE_VIDEO], freq, qi_app)

        self.resolution = vision_definitions.k960p#.kQVGA  # 320 * 240
        self.colorSpace = vision_definitions.kRGBColorSpace
        self._cameraID = 0
        self.fps = 5

        self.subscribeToServices()


        self.lastImage = None

        self.predictor_path = "sensors/video/data/shape_predictor_68_face_landmarks.dat"
        self.detector = dlib.get_frontal_face_detector()  # Call the face detector. Only the face is detected.
        self.predictor = dlib.shape_predictor(self.predictor_path)  # Output landmarks such as eyes and nose from the face

    def subscribeToServices(self):
        self._imgClient = self.subscribe(Constants.NAO_SERVICE_VIDEO, "HeadTracker", self.resolution, self.colorSpace, self.fps)


    def sense(self):
        self.lastImage = self.services[Constants.NAO_SERVICE_VIDEO].getImageRemote(self._imgClient)
        # print(self.lastImage)
        # print(self._imgClient=="")
        # lastImage_string = str(bytearray(self.lastImage[6]))

        # print(lastImage_string)

        #decode the image for opencv2
        # nparr = np.fromstring(lastImage_string, np.uint8)
        # frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        #
        # frame = cv2.imdecode(bytearray(self.lastImage[6]), cv2.IMREAD_COLOR)
        #
        if not self.lastImage is None:
            imageWidth = self.lastImage[0]
            imageHeight = self.lastImage[1]
            array = self.lastImage[6]
            image_string = str(bytearray(array))
            pil_image = Image.frombytes("RGB", (imageWidth, imageHeight), image_string)
            open_cv_image = np.array(pil_image)
            # Convert RGB to BGR
            frame = open_cv_image[:, :, ::-1].copy()

            # frame = imutils.resize(frame, width=1000)  # Adjust the display size of the frame image
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert to gray scale
            rects = self.detector(gray, 0)  # Detect face from gray
            image_points = None

            for rect in rects:
                shape = self.predictor(gray, rect)
                shape = face_utils.shape_to_np(shape)

                for (x, y) in shape:  # Plot 68 landmarks on the entire face
                    cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)

                image_points = np.array([
                    tuple(shape[30]),  # Nose tip
                    tuple(shape[21]),
                    tuple(shape[22]),
                    tuple(shape[39]),
                    tuple(shape[42]),
                    tuple(shape[31]),
                    tuple(shape[35]),
                    tuple(shape[48]),
                    tuple(shape[54]),
                    tuple(shape[57]),
                    tuple(shape[8]),
                ], dtype='double')

            if len(rects) > 0:
                model_points = np.array([
                    (0.0, 0.0, 0.0),  # 30
                    (-30.0, -125.0, -30.0),  # 21
                    (30.0, -125.0, -30.0),  # 22
                    (-60.0, -70.0, -60.0),  # 39
                    (60.0, -70.0, -60.0),  # 42
                    (-40.0, 40.0, -50.0),  # 31
                    (40.0, 40.0, -50.0),  # 35
                    (-70.0, 130.0, -100.0),  # 48
                    (70.0, 130.0, -100.0),  # 54
                    (0.0, 158.0, -10.0),  # 57
                    (0.0, 250.0, -50.0)  # 8
                ])

                size = frame.shape

                focal_length = size[1]
                center = (size[1] // 2, size[0] // 2)  # Face center coordinates

                camera_matrix = np.array([
                    [focal_length, 0, center[0]],
                    [0, focal_length, center[1]],
                    [0, 0, 1]
                ], dtype='double')

                dist_coeffs = np.zeros((4, 1))

                (success, rotation_vector, translation_vector) = cv2.solvePnP(model_points, image_points, camera_matrix,
                                                                              dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)
                # Rotation matrix and Jacobian
                (rotation_matrix, jacobian) = cv2.Rodrigues(rotation_vector)
                mat = np.hstack((rotation_matrix, translation_vector))

                # yaw,pitch,Take out roll
                (_, _, _, _, _, _, eulerAngles) = cv2.decomposeProjectionMatrix(mat)
                yaw = eulerAngles[1]
                pitch = eulerAngles[0]
                roll = eulerAngles[2]

                list_ret_val = ["yaw", str(int(yaw)), "pitch", str(int(pitch)), "roll", str(int(roll))]
                print(list_ret_val)
                ret_val = joinStrings(list_ret_val, Constants.STRING_SEPARATOR_INNER)

                return ret_val
            else:
                return None
        else:
            return None






