# install opencv "pip install opencv-python"
import cv2

# distance from camera to object(face) measured
# centimeter
Known_distance = 75

# width of face in the real world or Object Plane
# centimeter
Known_width = 13
Known_width_eyes = 3
Known_width_mouth = 4

# Colors
GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# defining the fonts
fonts = cv2.FONT_HERSHEY_COMPLEX


# face detector object
face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
mouth_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

# focal length finder function
def Focal_Length_Finder(measured_distance, real_width, width_in_rf_image):
    # finding the focal length
    focal_length = (width_in_rf_image * measured_distance) / real_width
    return focal_length


# distance estimation function
def Distance_finder(Focal_Length, real_face_width, face_width_in_frame):
    distance = (real_face_width * Focal_Length) / face_width_in_frame

    # return the distance
    return distance


def face_data(image):
    face_width = 0  # making face width to zero
    eyes_width = 0
    mouth_width = 0
    # converting color image to gray scale image
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # detecting face in the image
    faces = face_detector.detectMultiScale(gray_image, 1.3, 5)

    # looping through the faces detect in the image
    # getting coordinates x, y , width and height
    face_x = 0
    face_y = 0
    for (x, y, h, w) in faces:
        # draw the rectangle on the face
        cv2.rectangle(image, (x, y), (x + w, y + h), GREEN, 2)
        # getting face width in the pixels
        face_width = w
        face_x = x
        face_y = y

    eyes = eye_detector.detectMultiScale(gray_image)
    for (ex, ey, ew, eh) in eyes:
        cv2.rectangle(image, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
        eyes_width = ew #assuming they are the same or so

    mouth = mouth_detector.detectMultiScale(gray_image, minNeighbors=100)
    for (sX, sY, sW, sH) in mouth:
        # draw the smile bounding box
        cv2.rectangle(image, (sX, sY), (sX + sW, sY + sH), (255, 0, 0), 2)
        mouth_width = sW
        break

    # return the face width in pixel
    return face_width, eyes_width, mouth_width


# reading reference_image from directory
ref_image = cv2.imread("data/Ref_image.png")

# find the face width(pixels) in the reference_image
ref_image_face_width, ref_image_eyes_width, ref_image_mouth_width = face_data(ref_image)

# get the focal by calling "Focal_Length_Finder"
# face width in reference(pixels),
# Known_distance(centimeters),
# known_width(centimeters)
Focal_length_found = Focal_Length_Finder(
    Known_distance, Known_width, ref_image_face_width)

print(Focal_length_found)


Focal_length_found_eyes = Focal_Length_Finder(
    Known_distance, Known_width_eyes, ref_image_eyes_width)

print(Focal_length_found_eyes)

Focal_length_found_mouth = Focal_Length_Finder(
    Known_distance, Known_width_mouth, ref_image_mouth_width)

print(Focal_length_found_mouth)

# show the reference image
# cv2.imshow("ref_image", ref_image)

# initialize the camera object so that we
# can get frame from it
cap = cv2.VideoCapture(0)

# looping through frame, incoming from
# camera/video
while True:

    # reading the frame from camera
    _, frame = cap.read()

    # calling face_data function to find
    # the width of face(pixels) in the frame
    face_width_in_frame, eyes_width_in_frame, mouth_width_in_frame = face_data(frame)

    # check if the face is zero then not
    # find the distance
    if (face_width_in_frame != 0) or (eyes_width_in_frame != 0) or (mouth_width_in_frame != 0): # could ignore this and make isntead if eyes visible
        # finding the distance by calling function
        # Distance finder function need
        # these arguments the Focal_Length,
        # Known_width(centimeters),
        # and Known_distance(centimeters)
        Distance = Distance_finder(
            Focal_length_found, Known_width, face_width_in_frame)
        Distanceeyes = Distance_finder(
            Focal_length_found, Known_width_eyes, eyes_width_in_frame)
        Distancemouth = Distance_finder(
            Focal_length_found, Known_width_mouth, mouth_width_in_frame)

        # draw line as background of text
        cv2.line(frame, (30, 30), (230, 30), RED, 32)
        cv2.line(frame, (30, 30), (230, 30), BLACK, 28)

        # Drawing Text on the screen
        cv2.putText(
            frame, "Distance: {} CM, {} CM, {} CM".format(round(Distance, 2),round(Distanceeyes, 2), round(Distancemouth, 2)), (30, 35),
            fonts, 0.6, GREEN, 2)
    # else:


    # show the frame on the screen
    cv2.imshow("frame", frame)

    # quit the program if you press 'q' on keyboard
    if cv2.waitKey(1) == ord("q"):
        break

# closing the camera
cap.release()

# closing the windows that are opened
cv2.destroyAllWindows()