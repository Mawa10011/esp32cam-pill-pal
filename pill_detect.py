

# ESP32-CAM pill detection and pixel comparison code
# uses camera stream from ESP32-CAM and arduino IDE to capture stills


# IMPORT LIBRARIES
# ------------------------------
import requests # send http requests to cam
import numpy as np # handles image data as arrays
import cv2 # decode, process, save images
import time # for time b/w captures
import os # file managing
# ------------------------------


# CONSTANTS
# ------------------------------
CAMERA_IP = "172.20.10.9" # esp32 cameras ip
IMAGE_NUM = 3 # num of images kept at a time
images = [] # stores most recent captured imsgs
detection_enabled = True # allows global detection
# ------------------------------




# CAPTURE IMAGES
# ------------------------------
def capture_image(filename):
  """
  captures 1 grayscale image at a time from the esp32 camera and 
  saves it to the file.
  """

  capture_url = f"http://{CAMERA_IP}/capture" # capture image
  response = requests.get(capture_url) # request jpg image
  image_bytes = np.frombuffer(response.content, np.uint8) # convert ray bytes to NumPy array
  image = cv2.imdecode(image_bytes, cv2.IMREAD_GRAYSCALE) # convert into OpenCV image in grayscale

  # safety (decoding error check)
  if image is None:
    print("safety check failed: decoding image error.")
    return None
  
  # save image 2 disk
  cv2.imwrite(filename, image)
  print(f"-- image saved as {filename} -- \n") # successful run prompt

  return image
# ------------------------------




# COMPARE IMAGES
# ------------------------------
def compare_images(img1, img2, threshold=5000):
  """
  checks if enough pixels changed between each image.
  """

  # make sure theres images
  if img1 is None or img2 is None:
    return False
  
  # pixel x pixel diff
  difference = cv2.absdiff(img1, img2) # num of diff pixels
  numPix_change = np.sum(difference > 20) # check for enough change

  print(f"{numPix_change} pixels changed \n") # num of pixels changed prompt

  # returns True if enough pixels changed
  return numPix_change > threshold
# ------------------------------




# IMAGE BUFFER
# ------------------------------
def initialize_images():
  """
  first set of images for comparison.
  """
  global images
  images = []

  # initial images for rolling buffer
  for i in range(IMAGE_NUM):
    filename= f"snapshot_{i+1}.jpg"
    img = capture_image(filename)
    images.append(img)
# ------------------------------



# MAIN DETECTION
# ------------------------------
def check_for_pill():
  """
  tracks whether a pill has been 'taken'.
  returns True if pill has been detected for the first time, and returns False otherwise.
  """
  
  global images, detection_enabled

  # skip detection if system is disabled
  if not detection_enabled:
    return False

  # make sure we have at least 2 images to compare
  if len(images) < 2:
    return False

  # compare two most recent images
  if compare_images(images[-2], images[-1]):
    print(f"!! motion detected !! \n")
    return True
  
  # remove 3rd image file (oldest)
  if os.path.exists("snapshot_1.jpg"):
    os.remove("snapshot_1.jpg")

  # shift img buffer
  images = images[1:]

  # switch around image names to fix order
  for i in range(len(images)):
    old = f"snapshot_{i+2}.jpg"
    new = f"snapshot_{i+1}.jpg"

    if os.path.exists(new):
      os.remove(new)
    os.rename(old, new)

  # capture new image and add it to the list
  new_file = f"snapshot_{len(images)+1}.jpg"
  images.append(capture_image(new_file))

  return False
# ------------------------------