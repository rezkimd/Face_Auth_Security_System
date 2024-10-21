"""
    Requirements
    python 3.7.7
    numpy==1.21.6
    opencv-contrib-python==4.1.2.30
    Pillow==9.5.0
"""

import sys
import time
import os
import numpy as np
from PIL import Image
import cv2
import serial

# Adjust the COM port and baud rate according to your setup
COM_PORT = 'COM3'  # Replace with your ESP32's COM port
BAUD_RATE = 115200
TIMEOUT = 1  # Timeout for reading from the serial port

esp32_serial = serial.Serial(COM_PORT, BAUD_RATE, timeout=TIMEOUT)

path = "user_image"
name = ""
if not os.path.exists("user_image"):
    os.mkdir("user_image")
    # print("Directory " , dirName ,  " Created ")

def communicate():
    # Initialize the serial connection
    try:
        print(f"Connected to {COM_PORT} at {BAUD_RATE} baud.")
        time.sleep(2)  # Wait for ESP32 to reboot and establish the serial connection

        while True:
            # Check if data is available from the ESP32
            if esp32_serial.in_waiting > 0:
                received_data = esp32_serial.readline().decode('utf-8').strip()
                print(f"Received from ESP32: {received_data}")

                # If the ESP32 sends "Infrared trigger", send "Notif accepted"
                if received_data == "Infrared trigger":
                    detection()
                    
    except serial.SerialException as e:
        print(f"Error connecting to {COM_PORT}: {e}")
    except KeyboardInterrupt:
        print("Program terminated by user.")
    finally:
        if esp32_serial.is_open:
            # esp32_serial.close()
            print("Serial connection closed.")


def get_unique_face_id(face_id):
    # Check if any file with the current face_id exists in the 'user_image' folder
    while any(f"face.{face_id}." in filename for filename in os.listdir("user_image")):
        face_id += 1  # Increment face_id if it's already used
    return face_id

def read_names_from_file(file_path):
    """Read names from a given file and return them as a list."""
    try:
        with open(file_path, 'r') as file:
            # Read each line and strip whitespace
            names = [line.strip() for line in file.readlines()]
        return names
    except Exception as e:
        print(f"Error reading names from file: {e}")
        return []

def training_data():
    # used to recognize faces in images and videos
    recognizer = cv2.face.LBPHFaceRecognizer_create()

    # creates an instance of a face detection classifier using the Haar Cascade classifier
    # pre-trained model for detecting faces in images
    dectector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

    def Images_And_Labels(path):
        imagesPaths = [os.path.join(path, f) for f in os.listdir(path)]
        faceSamples = []
        ids = []

        for imagePath in imagesPaths:
            gray_image = Image.open(imagePath).convert("L")  # convert to grayscale
            img_arr = np.array(gray_image, "uint8")  # creating array

            # extracts the label (id) from the image file name
            id = int(os.path.split(imagePath)[-1].split(".")[1])

            # detects faces in the image using the face detection classifier
            faces = dectector.detectMultiScale(img_arr)

            for x, y, w, h in faces:
                faceSamples.append(img_arr[y : y + h, x : x + w])
                ids.append(id)
        return faceSamples, ids

    print("Training Data...please wait...!!!")
    faces, ids = Images_And_Labels(path)

    # trains the face recognizer using the loaded face data (faces) and labels (ids).
    recognizer.train(faces, np.array(ids))
    # saves the trained recognizer to a YAML file called 'trained_data.yml'.
    recognizer.write("trained_data.yml")    

    print("data Trained successfully !!!!")

def face_generator():
    global name
    cam = cv2.VideoCapture(0)  # used to create video which is used to capture images
    cam.set(3, 640)
    cam.set(4, 480)
    dectector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    # this file is used to detect a object in an image
    face_id = get_unique_face_id(1)
    name = input("enter name :")
    sample = 20

    # Create a file to save the names
    with open("user_information/face_names.txt", "a") as name_file:
        name_file.write(f"{face_id},{name}\n")  # Save face_id and name
    
    for f in os.listdir(path):  # remove old images from user data folder if present
        os.remove(os.path.join(path, f))
    print("taking sample image of user ...please look at camera")
    time.sleep(2)

    count = 0
    while True:
        ret, img = cam.read()  # read the frames using above created objects
        converted_image = cv2.cvtColor(
            img, cv2.COLOR_BGR2GRAY
        )  # converts image to black and white
        faces = dectector.detectMultiScale(
            converted_image, 1.3, 5
        )  # detect face in image

        for x, y, w, h in faces:

            cv2.rectangle(
                img, (x, y), (x + w, y + h), (255, 0, 0), 2
            )  # creates frame around face
            count += 1
            # print(count)

            cv2.imwrite(
                f"user_image/face.{face_id}.{count}.jpg",
                converted_image[y : y + h, x : x + w],
            )
            # To caputure image and save in user_image folder

            cv2.imshow("image", img)  # displays image on window

        k = cv2.waitKey(1) & 0xFF
        if k == 27:
            break
        elif count >= sample:
            break
    print("Image Samples taken succefully !!!!.")
    training_data()
    cam.release()
    cv2.destroyAllWindows()

def detection():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("trained_data.yml")  # loaded trained model
    cascadePath = "haarcascade_frontalface_default.xml"
    faceCascade = cv2.CascadeClassifier(cascadePath)

    font = cv2.FONT_HERSHEY_SIMPLEX  # denotes fonts size

    # id = 3  # number of persons your want to recognize
    # Read names from file
    names = read_names_from_file("user_information/face_names.txt")
    cam = cv2.VideoCapture(0)  # used to create video which is used to capture images
    cam.set(3, 640)
    cam.set(4, 480)

    # define min window size to be recognize as a face
    minW = 0.1 * cam.get(3)
    maxW = 0.1 * cam.get(4)
    
    unrecognized_time_start = time.time()  # Start time for unrecognized timer
    recognized = False
    
    while True:
        if cam is None or not cam.isOpened():
            print("Warning: unable to open video source: ")

        ret, img = cam.read()  # read the frames using above created objects
        if ret == False:
            print("unable to detect img")
        converted_image = cv2.cvtColor(
            img, cv2.COLOR_BGR2GRAY
        )  # converts image to black and white

        faces = faceCascade.detectMultiScale(
            converted_image,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(int(minW), int(minW)),
        )
        
        cv2.imshow("Camera", img)
        k = cv2.waitKey(10) & 0xFF
        if k == 27:  # Press 'Esc' to exit
            break
        
        for x, y, w, h in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            id, accuracy = recognizer.predict(converted_image[y: y + h, x: x + w])
            cv2.imshow("camera", img)
            k = cv2.waitKey(10) & 0xFF
            if k == 27:
                break
        # Check if the id is within the valid range
        # Check if the id is within the valid range
            if 0 <= id < len(names):  # Ensure the id is valid
                name = names[id]  # Get the name corresponding to the id
                accuracy_text = f"{round(100 - accuracy)}%"
                recognized = True

                
                # Display text on image
                cv2.putText(img, f"Hello, {name}", (x + 5, y - 5), font, 1, (255, 0, 255), 2)
                cv2.putText(img, f"{accuracy_text}", (x + 5, y + h - 5), font, 1, (255, 255, 0), 1)

                # Close after recognizing
                esp32_serial.write(("Hello, Master").encode('utf-8'))
                time.sleep(10)  # Optional: delay for a couple of seconds before closing
                cam.release()
                cv2.destroyAllWindows()
                return 
        
        # Check if the face remains unrecognized for 10 seconds
        if not recognized and time.time() - unrecognized_time_start >= 10:
            print("Face not recognized for 10 seconds, closing...")
            esp32_serial.write(("Not recognized").encode('utf-8'))
            time.sleep(10)  # Optional: delay for a couple of seconds before closing
            cam.release()
            cv2.destroyAllWindows()
            return 

def main_menu():
    print("\t\t\t ##### Welcome to Face Authentication System #####")
    print("Please choose an option:")
    print("1. Capture images for a new user")
    print("2. Train data for face authentication")
    print("3. Test face authentication")
    print("4. Exit")

    choice = input("Enter the number of your choice: ")

    if choice == '1':
        face_generator()
    elif choice == '2':
        training_data()
    elif choice == '3':
        detection()
    elif choice == '4':
        print("Thank you for using this application! Goodbye!")
        sys.exit()
    else:
        print("Invalid choice, please try again.")
        main_menu()


# Start the application by showing the main menu
# main_menu()

communicate()
