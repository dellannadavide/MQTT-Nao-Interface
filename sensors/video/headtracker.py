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
import dlib  # Machine learning library
import imutils  # OpenCV assistance
from imutils import face_utils

class HeadTracker(Sensor):
    """
    A simple class to compute data about face position
    """

    def __init__(self, nao_interface, id, mqtt_topic, freq, qi_app=None, virtual=False):
        super(HeadTracker, self).__init__(nao_interface, id, mqtt_topic, [], freq, qi_app, virtual)
        #
        # if self.virtual:
        #     """ In case of virtual robot, it is assumed it can be used the camera of the laptop """
        #     self._cameraID = 0
        #     self.capture = cv2.VideoCapture(self._cameraID)
        # else:
        #     self.resolution = vision_definitions.kQVGA#.k960p#.kQVGA  # 320 * 240
        #     self.colorSpace = vision_definitions.kRGBColorSpace
        #
        #     self.fps = 5
        #     self._imgClient = self.subscribe(Constants.NAO_SERVICE_VIDEO, "HeadTracker", self.resolution, self.colorSpace, self.fps)

        self.lastImage = None

        self.data_folder = "sensors/video/data/"

        self.landmarks_predictor_path = self.data_folder+"shape_predictor_68_face_landmarks.dat"
        self.landmarks_detector = dlib.get_frontal_face_detector()  # Call the face detector. Only the face is detected.
        self.landmarks_predictor = dlib.shape_predictor(self.landmarks_predictor_path)  # Output landmarks such as eyes and nose from the face

        self.face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.mouth_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

        self.ref_image = cv2.imread(self.data_folder+"camimage.png")
        # find the face width(pixels) in the reference_image
        # self.ref_image_face_width, self.ref_image_eyes_width, self.ref_image_mouth_width = self.face_data(self.ref_image)
        self.ref_image_face_width, self.ref_image_eyes_width = self.face_data(self.ref_image)
        self.Known_distance = 40
        self.Known_width = 13
        self.Known_width_eyes = 3
        self.Known_width_mouth = 4
        self.Focal_length_found_face = self.Focal_Length_Finder(
            self.Known_distance, self.Known_width, self.ref_image_face_width)
        self.Focal_length_found_eyes = self.Focal_Length_Finder(
            self.Known_distance, self.Known_width_eyes, self.ref_image_eyes_width)
        # self.Focal_length_found_mouth = self.Focal_Length_Finder(
        #     self.Known_distance, self.Known_width_mouth, self.ref_image_mouth_width)
        print(self.Focal_length_found_face)
        print(self.Focal_length_found_eyes)
        # print(self.Focal_length_found_mouth)

    def sense(self):
        # frame = None
        # if self.virtual:
        #     ret, frame = self.capture.read()
        #     self.lastImage = frame
        # else:
        #     self.lastImage = self.services[Constants.NAO_SERVICE_VIDEO].getImageRemote(self._imgClient)

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
        self.lastImage, gray = self.nao_interface.services["NaoImageCollector"].getLastFrame()
        # print(self.lastImage)
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

            # frame = imutils.resize(frame, width=1000)  # Adjust the display size of the frame image
            # gray = cv2.cvtColor(self.lastImage, cv2.COLOR_BGR2GRAY)  # Convert to gray scale

            # calling face_data function to find
            # the width of face(pixels) in the frame
            face_width_in_frame, eyes_width_in_frame = self.face_data(gray)
            # face_width_in_frame, eyes_width_in_frame, mouth_width_in_frame = self.face_data(gray)
            estimated_distance = -1
            if (face_width_in_frame != 0):
                estimated_distance = self.Distance_finder(
                    self.Focal_length_found_face, self.Known_width, face_width_in_frame)
                # print("face estimated distance ", estimated_distance)
            elif (eyes_width_in_frame != 0):
                estimated_distance = self.Distance_finder(
                    self.Focal_length_found_face, self.Known_width_eyes, eyes_width_in_frame)
                if estimated_distance > 50:
                    estimated_distance = -1
                # print("eyes estimated distance ", estimated_distance)
            # elif (mouth_width_in_frame != 0):
            #     estimated_distance = self.Distance_finder(
            #         self.Focal_length_found_face, self.Known_width_mouth, mouth_width_in_frame)
            #     if estimated_distance > 50:
            #         estimated_distance = -1
            #     print("mouth estimated distance ", estimated_distance)
            if estimated_distance != -1:
                estimated_distance = estimated_distance/100.0

            rects = self.landmarks_detector(gray, 0)  # Detect face from gray
            image_points = None

            for rect in rects:
                shape = self.landmarks_predictor(gray, rect)
                shape = face_utils.shape_to_np(shape)

                for (x, y) in shape:  # Plot 68 landmarks on the entire face
                    cv2.circle(self.lastImage, (x, y), 1, (255, 255, 255), -1)

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

                size = self.lastImage.shape

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


                return self.getReturnVal(yaw, pitch, roll, estimated_distance)

            else:
                return self.getReturnVal(0, 0, 0, estimated_distance)

        else:
            return None

    def getReturnVal(self, yaw, pitch, roll, estimated_distance):
        if int(yaw)==0 and int(pitch)==0 and int(roll)==0 and float(estimated_distance)==-1.0:
            return None
        else:
            list_retval = ["yaw", str(int(yaw)), "pitch", str(int(pitch)), "roll", str(int(roll)), "dist",
                                   str(float(estimated_distance))]
            list_retval
            ret_val = joinStrings(list_retval, Constants.STRING_SEPARATOR_INNER)
            print(list_retval)
            return ret_val

    def face_data(self, gray_image):
        face_width = 0  # making face width to zero
        eyes_width = 0
        mouth_width = 0
        # converting color image to gray scale image
        # gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # detecting face in the image
        faces = self.face_detector.detectMultiScale(gray_image, 1.3, 5)

        # looping through the faces detect in the image
        # getting coordinates x, y , width and height
        for (x, y, h, w) in faces:
            # # draw the rectangle on the face
            # cv2.rectangle(image, (x, y), (x + w, y + h), GREEN, 2)
            # # getting face width in the pixels
            face_width = w

        eyes = self.eye_detector.detectMultiScale(gray_image)
        for (ex, ey, ew, eh) in eyes:
            # cv2.rectangle(image, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
            eyes_width = ew #assuming they are the same or so

        # mouth = self.mouth_detector.detectMultiScale(gray_image, minNeighbors=120)
        # for (sX, sY, sW, sH) in mouth:
        #     # draw the smile bounding box
        #     # cv2.rectangle(image, (sX, sY), (sX + sW, sY + sH), (255, 0, 0), 2)
        #     mouth_width = sW
        #     break

        # return the face width in pixel
        # return face_width, eyes_width, mouth_width
        return face_width, eyes_width

    # focal length finder function
    def Focal_Length_Finder(self, measured_distance, real_width, width_in_rf_image):
        # finding the focal length
        focal_length = (width_in_rf_image * measured_distance) / real_width
        return focal_length

    # distance estimation function
    def Distance_finder(self, Focal_Length, real_face_width, face_width_in_frame):
        distance = (real_face_width * Focal_Length) / face_width_in_frame

        # return the distance
        return distance




