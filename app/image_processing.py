import cv2 
import cv2.aruco as aruco
import numpy as np
from utils import get_center_point, template_matching
import cv2 
import cv2.aruco as aruco
import numpy as np
from math import atan2, cos, sin, sqrt, pi, floor
from globals import *
				
class ImageProcessor:
		
		storedDetections = ([], np.array([], int))
		
		def __init__(self):
				# values for aruco markers
				self.adaptiveThreshWinSizeMin = aruco_defaults["adaptiveThreshWinSizeMin"]
				self.adaptiveThreshWinSizeMax = aruco_defaults["adaptiveThreshWinSizeMax"]
				self.adaptiveThreshWinSizeStep = aruco_defaults["adaptiveThreshWinSizeStep"]
				self.adaptiveThreshConstant = aruco_defaults["adaptiveThreshConstant"]
				self.minMarkerPerimeterRate = aruco_defaults["minMarkerPerimeterRate"] # / 1000
				self.maxMarkerPerimeterRate = aruco_defaults["maxMarkerPerimeterRate"] # / 10
				self.polygonalApproxAccuracyRate = aruco_defaults["polygonalApproxAccuracyRate"] # / 1000
				self.cornerRefinementWinSize = aruco_defaults["cornerRefinementWinSize"]
				self.cornerRefinementMaxIterations = aruco_defaults["cornerRefinementMaxIterations"]
				self.minDistanceToBorder = aruco_defaults["minDistanceToBorder"]
				self.minOtsuStdDev = aruco_defaults["minOtsuStdDev"]
				self.perspectiveRemovePixelPerCell = aruco_defaults["perspectiveRemovePixelPerCell"]
				self.storedDetections = ([], [])
		
		def init(self, args, archeReader):
				self.test = args.test 
				self.debug = args.debug
				self.save_frames = args.save_frames
				self.archeReader = archeReader
		
		def clear_stored_markers(self):
				self.storedDetections = ([], [])

		def process_image(self, avaraged_frames, live_frame, segmentIndex):
				image = live_frame.copy()
				avaraged_image = avaraged_frames.copy()

				# Detect markers
				corners, ids = self.check_markers(image)
								
				is_valid, detections = self.validateMarkers(image, corners, ids, segmentIndex)
				
				# raw_image = aruco.drawDetectedMarkers(raw_image, corners, ids)

				# store detections that are valid
				for index, id in enumerate(detections[1]):
						# print("id" ,id)
						if id not in self.storedDetections[1]:
								self.storedDetections[0].append(detections[0][index])
								self.storedDetections[1].append(id)
						else:
								stored_index = self.storedDetections[1].index(id)
								self.storedDetections[0][stored_index] = detections[0][index]

				# Convert ids to a numpy array
				ids_np = np.array(self.storedDetections[1], int)

				# Check if all expected detections are present in storedDetections
				if set(ids_np) == set([segmentIndex, segmentIndex + 1, segmentIndex + COLS, segmentIndex + COLS + 1]):
						is_valid = True
				
				# print("stored_detections", self.storedDetections)
				
				# if stored detection doesnt have specific detection id, add it
				message = self.archeReader.set_detections((self.storedDetections[0], ids_np), avaraged_image, is_valid)
				return is_valid, message
		
		def check_markers(self, image):
				# Load the ArUco dictionary (you may need to adjust the dictionary type)
				aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_1000)
				
				# Initialize the detector parameters
				parameters = aruco.DetectorParameters()
				parameters.adaptiveThreshWinSizeMin = self.adaptiveThreshWinSizeMin
				parameters.adaptiveThreshWinSizeMax = self.adaptiveThreshWinSizeMax
				parameters.adaptiveThreshWinSizeStep = self.adaptiveThreshWinSizeStep
				parameters.adaptiveThreshConstant = self.adaptiveThreshConstant
				parameters.minMarkerPerimeterRate = self.minMarkerPerimeterRate / 1000
				parameters.maxMarkerPerimeterRate = self.maxMarkerPerimeterRate / 10
				parameters.polygonalApproxAccuracyRate = self.polygonalApproxAccuracyRate / 1000
				parameters.cornerRefinementWinSize = self.cornerRefinementWinSize
				parameters.cornerRefinementMaxIterations = self.cornerRefinementMaxIterations
				parameters.minDistanceToBorder = self.minDistanceToBorder
				parameters.perspectiveRemovePixelPerCell = self.perspectiveRemovePixelPerCell
		
				detector = aruco.ArucoDetector(aruco_dict, parameters)
				
				# Step 1: Apply Bilateral Filter for noise reduction while preserving edges
				denoised_image = cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)

				# Step 4: Convert masked image to LAB color space and apply CLAHE to the L channel for contrast enhancement
				lab = cv2.cvtColor(denoised_image, cv2.COLOR_BGR2LAB)
				l, a, b = cv2.split(lab)
				clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
				cl = clahe.apply(l)
				limg = cv2.merge((cl, a, b))

				# Convert the enhanced image back to BGR color space
				enhanced_image = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

				# Step 5: Apply sharpening to make the text more defined
				# Create a kernel for the Unsharp Mask
				gaussian_blur = cv2.GaussianBlur(enhanced_image, (9, 9), 10.0)
				sharpened_image = cv2.addWeighted(enhanced_image, 1.5, gaussian_blur, -0.5, 0)
		
				# Step 6: Convert the sharpened image to grayscale
				gray = cv2.cvtColor(sharpened_image, cv2.COLOR_BGR2GRAY)
				corners, ids, rejectedImgPoints = detector.detectMarkers(gray)
				return corners, ids
				# Detect markers
	
		def validateMarkers(self, image, corners, ids, segmentIndex):
				# make new tuple
				validated_markers = []
				validated_ids = np.array([], int)
				if ids is None:
						return False, ([], [])

				top_left = segmentIndex
				top_right = segmentIndex + 1
				bottom_left = top_left + COLS
				bottom_right = top_right + COLS

				# find if ids contains top_left, top_right, bottom_left, bottom_right
				corner_ids = [top_left, top_right, bottom_left, bottom_right]
				
				# print("corner_ids", corner_ids, segmentIndex, ids)

				for index, id in enumerate(ids):
						if id in corner_ids:
								# remove element from corners
								validated_markers.append(corners[index])
								validated_ids = np.append(validated_ids, id)
								corner_ids.remove(id)
				
				validated_ids = np.array(validated_ids, int)  # Convert to numpy array
				
				#print("validated_ids", validated_ids)

				if len(corner_ids) > 0:
						return False, (validated_markers, validated_ids)

				return True, (validated_markers, validated_ids)
		
		def getDetectedMarkers(self):
				return self.lastDetectMarkers

		def clear(self):
				self.archeReader.clear()