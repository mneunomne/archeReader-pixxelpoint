import os
from dotenv import load_dotenv

# load .env file
load_dotenv()

# get environment variables
WEBCAM = int(os.environ.get("WEBCAM"))

# flask server settings
FLASK_SERVER_IP = os.environ.get("FLASK_SERVER_IP")
FLASK_SERVER_PORT = int(os.environ.get("FLASK_SERVER_PORT"))

# size of cropped images
SEGMENT_WIDTH = 100
SEGMENT_HEIGHT = 100

SEGMENT_OUTPUT_WIDTH = 700
SEGMENT_OUTPUT_HEIGHT = 800

# ceramic data (ammount of fiducial markers) 
COLS = 10
ROWS = 10
INNER_COLS = 7
INNER_ROWS = 8

# detections attempts
MAX_ATTEMPTS = 100

# paths
FOLDER_PATH = 'app/numerals__old/'
TEST_FILE = 'app/test_images/pixxel_test_0.png'

# aruco marker settings
aruco_defaults = {
  "adaptiveThreshWinSizeMin": 3,
  "adaptiveThreshWinSizeMax": 25,
  "adaptiveThreshWinSizeStep": 3,
  "adaptiveThreshConstant": 2,
  "minMarkerPerimeterRate": 224,
  "maxMarkerPerimeterRate": 69,
  "polygonalApproxAccuracyRate": 69,
  "cornerRefinementWinSize": 17,
  "cornerRefinementMaxIterations": 24,
  "minDistanceToBorder": 1,
  "minOtsuStdDev": 5,
  "perspectiveRemovePixelPerCell": 8,
  "adaptiveThreshWinSize": 23,
}