import cv2
from globals import *
import numpy as np
import cv2.aruco as aruco
from utils import list_ports, load_templates, get_center_point, template_matching, draw_lines
from flask_server import app, sendVideoOutput, sendAvaragedOutput, sendCroppedOutput, imageProcessor, sendLiveOutput
import threading
import queue
from kiosk import run_kiosk

FRAME_BUFFER_SIZE = 10  # Number of frames to average

ready_to_read = False
thread_flask = None

server_url = "http://{}:{}/".format(FLASK_SERVER_IP, FLASK_SERVER_PORT)

lines_image = draw_lines()

class ArcheReader:
	
	capture = None
 
	frame_buffer = []

	crop_size = 200
 
	roi_corners = None
 
	frames_displaying_grid = None
	
	def __init__(self, args):
		print("init")
		# check if test mode
		self.test = args.test 
		self.debug = args.debug
		
		self.test_parameters = args.parameters
		
		self.frames_displaying_grid = 0
  
		self.detections = [[],[]]
		
		self.detections_queue = queue.Queue()  # Queue for passing detections between threads
		self.cropped_queue = queue.Queue()  # Queue for passing detections between threads
		self.avarage_queue = queue.Queue()  # Queue for passing detections between threads
	
		imageProcessor.init(args, self)
  
		self.roi_corners = None
  
		# start flask
		if (args.flask):
			thread_flask = threading.Thread(target=app.run, args=(FLASK_SERVER_IP, FLASK_SERVER_PORT,))
			thread_flask.start()
		
		if (args.kiosk):
			thread_kiosk = threading.Thread(target=run_kiosk, args=(server_url, False))
			thread_kiosk.start()


		# load templates
		self.templates = load_templates(FOLDER_PATH)
				
		self.save_frames = args.save_frames
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
		
		
		cv2.namedWindow('arche-reading')
		if self.test_parameters:
			self.createTrackbars()
		self.init()
		
	def init(self):
		# if test enabled, use static image
		self.run_opencv()
		#thread_opencv.start()
	
	def start_cam(self):
		# detect available cameras
		_,working_ports,_ = list_ports()
		print("working_ports", working_ports)
		
	def createTrackbars(self):
		# Create trackbars
		cv2.createTrackbar('adaptiveThreshWinSizeMin', 'arche-reading', aruco_defaults["adaptiveThreshWinSizeMin"], 100, self.on_trackbar)
		cv2.createTrackbar('adaptiveThreshWinSizeMax', 'arche-reading', aruco_defaults["adaptiveThreshWinSizeMax"], 100, self.on_trackbar)
		cv2.createTrackbar('adaptiveThreshWinSizeStep', 'arche-reading', aruco_defaults["adaptiveThreshWinSizeStep"], 100, self.on_trackbar)
		cv2.createTrackbar('adaptiveThreshConstant', 'arche-reading', aruco_defaults["adaptiveThreshConstant"], 100, self.on_trackbar)
		cv2.createTrackbar('minMarkerPerimeterRate', 'arche-reading', aruco_defaults["minMarkerPerimeterRate"], 1000, self.on_trackbar)
		cv2.createTrackbar('maxMarkerPerimeterRate', 'arche-reading', aruco_defaults["maxMarkerPerimeterRate"], 100,  self.on_trackbar)
		cv2.createTrackbar('polygonalApproxAccuracyRate', 'arche-reading', aruco_defaults["polygonalApproxAccuracyRate"], 1000, self.on_trackbar)
		cv2.createTrackbar('cornerRefinementWinSize', 'arche-reading', aruco_defaults["cornerRefinementWinSize"], 100, self.on_trackbar)
		cv2.createTrackbar('cornerRefinementMaxIterations', 'arche-reading', aruco_defaults["cornerRefinementMaxIterations"], 100, self.on_trackbar)
		cv2.createTrackbar('minDistanceToBorder', 'arche-reading', aruco_defaults["minDistanceToBorder"], 100, self.on_trackbar)
		cv2.createTrackbar('perspectiveRemovePixelPerCell', 'arche-reading', aruco_defaults["perspectiveRemovePixelPerCell"], 100, self.on_trackbar)


	def on_trackbar(self, value):
		# Update parameters based on trackbar values
		self.adaptiveThreshWinSizeMin = cv2.getTrackbarPos('adaptiveThreshWinSizeMin', 'arche-reading')
		self.adaptiveThreshWinSizeMax = cv2.getTrackbarPos('adaptiveThreshWinSizeMax', 'arche-reading')
		self.adaptiveThreshWinSizeStep = cv2.getTrackbarPos('adaptiveThreshWinSizeStep', 'arche-reading')
		self.adaptiveThreshConstant = cv2.getTrackbarPos('adaptiveThreshConstant', 'arche-reading')
		self.minMarkerPerimeterRate = cv2.getTrackbarPos('minMarkerPerimeterRate', 'arche-reading')
		self.maxMarkerPerimeterRate = cv2.getTrackbarPos('maxMarkerPerimeterRate', 'arche-reading')
		self.polygonalApproxAccuracyRate = cv2.getTrackbarPos('polygonalApproxAccuracyRate', 'arche-reading')
		self.cornerRefinementWinSize = cv2.getTrackbarPos('cornerRefinementWinSize', 'arche-reading')
		self.cornerRefinementMaxIterations = cv2.getTrackbarPos('cornerRefinementMaxIterations', 'arche-reading')
		self.minDistanceToBorder = cv2.getTrackbarPos('minDistanceToBorder', 'arche-reading')
		self.perspectiveRemovePixelPerCell = cv2.getTrackbarPos('perspectiveRemovePixelPerCell', 'arche-reading')

		print("cornerRefinementWinSize", self.cornerRefinementWinSize)
		print("cornerRefinementMaxIterations", self.cornerRefinementMaxIterations)
		print("minDistanceToBorder", self.minDistanceToBorder)
		print("perspectiveRemovePixelPerCell", self.perspectiveRemovePixelPerCell)
		print("adaptiveThreshWinSizeMin", self.adaptiveThreshWinSizeMin)
		print("adaptiveThreshWinSizeMax", self.adaptiveThreshWinSizeMax)
		print("adaptiveThreshWinSizeStep", self.adaptiveThreshWinSizeStep)
		print("adaptiveThreshConstant", self.adaptiveThreshConstant)
		print("minMarkerPerimeterRate", self.minMarkerPerimeterRate)
		print("maxMarkerPerimeterRate", self.maxMarkerPerimeterRate)
		print("polygonalApproxAccuracyRate", self.polygonalApproxAccuracyRate)
		
	def run_opencv(self):
		
		# create window
		cv2.startWindowThread()
		cv2.namedWindow("arche-reading")
		cv2.namedWindow("cropped")

		while True:
			
			 # display image
			image = self.get_image()
	 
			interface_image = image.copy()
			
			video_output = image.copy()
	 
			avarage_frames = None
			
			if self.test_parameters:
				video_output = self.test_detection(video_output)
			else:
				# Check the queue for new detections
				try:
						self.detections = self.detections_queue.get_nowait()  
						if len(self.detections[0]) == 4 and len(self.detections[1]) == 4:
							segment_data, roi_cropped = self.process_detections(self.detections, image)
							data_message = self.decode_segment_data(segment_data)
							self.sendSocketData(data_message)
							print("segment_data", segment_data)
							cv2.imshow('cropped', roi_cropped)
				except queue.Empty:
						pass
				try:
						roi_cropped = self.cropped_queue.get_nowait()  
						cv2.imshow('cropped', roi_cropped)
				except queue.Empty:
						pass
					
			output_image = video_output.copy()
	 
			# Convert the image to LAB color space
			lab = cv2.cvtColor(output_image, cv2.COLOR_BGR2LAB)
			# Separate the LAB channels
			l, a, b = cv2.split(lab)
			# Apply CLAHE to the L channel
			clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
			cl = clahe.apply(l)
			# Merge the enhanced L channel with the original A and B channels
			limg = cv2.merge((cl, a, b))

			# Convert the image back to BGR color space
			output_image = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
			
			# more red channel
			# output_image[:, :, 2] = cv2.addWeighted(output_image[:, :, 2], 1.90, np.zeros(output_image[:, :, 2].shape, output_image[:, :, 2].dtype), 0, 0)
			
			# increase contrast
			output_image = cv2.convertScaleAbs(output_image, alpha=0.79, beta=1)

			video_output = output_image.copy()
	 
			# if len(self.detections[0]) == 4 and len(self.detections[1]) == 4:
			corners, ids = imageProcessor.check_markers(image)
			video_output = aruco.drawDetectedMarkers(video_output, corners, ids)
			
			# display grid lines
			if self.roi_corners is not None:
				video_output = self.display_grid_lines(video_output)
				self.frames_displaying_grid += 1
				if (self.frames_displaying_grid > 30):
					self.roi_corners = None
					self.frames_displaying_grid = 0
     
			# send video to web
			# sendCroppedOutput(output_image)
	 
			self.frame_buffer.append(output_image)
			if len(self.frame_buffer) > FRAME_BUFFER_SIZE:
				# clear array
				self.frame_buffer = []
	 
			if len(self.frame_buffer) == FRAME_BUFFER_SIZE:
				# Compute the average image
				averaged_frame = np.mean(self.frame_buffer, axis=0).astype(np.uint8)
				self.avarage_queue.put(averaged_frame)
		
			# send video to flask
			sendVideoOutput(video_output)
			# sendVideoOutput(interface_image)
			
			# send live output
			sendLiveOutput(output_image)
			
			# try if avaraged frames is available
			try:
				avarage_frames = self.avarage_queue.get_nowait()
				cv2.imshow('avarage_frames', avarage_frames)
			except queue.Empty:
				pass
			
			
			if avarage_frames is not None:
				sendAvaragedOutput(avarage_frames)
	 
			cv2.imshow('arche-reading', video_output)
			if cv2.waitKey(1) & 0xFF == ord('q'):
				break

		# When everything done, release the capture
		self.capture.release()
		cv2.destroyAllWindows()
	
	def process_detections(self, new_detections, image):
		
		markers = new_detections[0]
		ids = new_detections[1]
		
		corners = [] # list of tuples (center_point, id)
		
		for index, marker in enumerate(markers):
			center_point = get_center_point(marker)
			corners.append((ids[index], center_point))
		
		# order corners
		ordered_corners = sorted(corners, key=lambda x: x[0])
		ordered_center_points = [corner[1] for corner in ordered_corners]
		ordered_center_points = [ordered_corners[0][1], ordered_corners[1][1], ordered_corners[3][1], ordered_corners[2][1]]
		
		# Define the ROI using the corner points of the markers
		roi_corners = np.array([marker for marker in ordered_center_points], dtype=np.int32)
		roi_corners = roi_corners.reshape((-1, 1, 2))
		
		# Create a mask for the ROI
		mask = np.zeros_like(image)
		cv2.fillPoly(mask, [roi_corners], (255, 255, 255))
		
		# Apply the mask to the original image
		roi_image = cv2.bitwise_and(image, mask)
		
		# Get the bounding box of the ROI
		x, y, w, h = cv2.boundingRect(roi_corners)
		
		# Crop the image using the bounding box
		roi_cropped = roi_image[y:y+h, x:x+w]
		
		# size of output image segment
		output_width = SEGMENT_OUTPUT_WIDTH
		output_height = SEGMENT_OUTPUT_HEIGHT

		# Define the coordinates of the output rectangle
		output_rect = np.array([[0, 0], [output_width - 1, 0], [output_width - 1, output_height - 1], [0, output_height - 1]], dtype=np.float32)

		# Calculate the perspective transformation matrix
		perspective_matrix = cv2.getPerspectiveTransform(roi_corners.astype(np.float32), output_rect)

		# Apply the perspective transformation to the original image
		rect_roi = cv2.warpPerspective(image, perspective_matrix, (output_width, output_height))

		roi_cropped = rect_roi
		
		segment_data, roi_cropped = self.get_segment_data(roi_cropped)
	
		# blank canvas for the lines to be placed on the image on the roi_corners		
		
		return segment_data, roi_cropped, roi_corners
	
	def get_segment_data(self, roi_cropped):    
		# rotate 90 degrees
		_w = SEGMENT_OUTPUT_WIDTH
		_h = SEGMENT_OUTPUT_HEIGHT
		#padding = 35
		padding_right = PADDING_RIGHT
		padding_left = PADDING_LEFT
		padding_top = PADDING_TOP
		padding_bottom = PADDING_BOTTOM
		# Calculate the dimensions of each segment
		segment_width = (_w - (padding_right + padding_left)) // INNER_COLS
		segment_height = ((_h - (padding_top + padding_bottom))  // INNER_ROWS)
		
		#gray_image = cv2.cvtColor(roi_cropped, cv2.COLOR_BGR2GRAY)
				
		# Step 1: Apply Bilateral Filter for noise reduction while preserving edges
		denoised_image = cv2.bilateralFilter(roi_cropped, d=9, sigmaColor=75, sigmaSpace=75)

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

		# Alternative: Use Laplacian for additional edge enhancement (optional)
		laplacian = cv2.Laplacian(sharpened_image, cv2.CV_64F)
		laplacian = np.uint8(np.absolute(laplacian))
		enhanced_sharpened = cv2.addWeighted(sharpened_image, 0.8, laplacian, 0.2, 0)

		roi_cropped = enhanced_sharpened.copy()
	
		# remove blue channel
		# roi_cropped[:, :, 0] = cv2.addWeighted(roi_cropped[:, :, 0], 1.50, np.zeros(roi_cropped[:, :, 0].shape, roi_cropped[:, :, 0].dtype), 0, 0)
		
		segment_data = []
		index = 0
		# Loop through the grid and extract each segment
		for j in range(INNER_COLS):
			for i in range(INNER_ROWS):
				if i < 2 and j < 2:
					continue
				if i < 2 and j > INNER_COLS - 3:
					continue
				if i > INNER_ROWS - 3 and j < 2:
					continue
				if i > INNER_ROWS - 3 and j > INNER_COLS - 3:
					continue
	 
				# Calculate the coordinates for the current segment
				x_start = j * segment_width + padding_left
				y_start = i * segment_height + padding_top + 0
				x_end = (j + 1) * segment_width + padding_left
				y_end = (i + 1) * segment_height + padding_top + 0
				segment_corners = np.array([[x_start, y_start], [x_end, y_start], [x_end, y_end], [x_start, y_end]], dtype='float32')

				# draw rect from segment_corners
				for k in range(4):
					start_point = segment_corners[k]
					end_point = segment_corners[(k + 1) % 4]
					# convert to int 
					start_point = (int(start_point[0]), int(start_point[1]))
					end_point = (int(end_point[0]), int(end_point[1]))
					roi_cropped = cv2.line(roi_cropped, start_point, end_point, (0, 255, 0), 2)
		
				# Extract the segment
				segment = roi_cropped[y_start:y_end, x_start:x_end]
		
				# gray segment
				gray_segment = cv2.cvtColor(segment, cv2.COLOR_BGR2GRAY)
				
				# improve contrast
				# gray_segment = cv2.equalizeHist(gray_segment)
				
								
				# Perform template matching
				matched_template, matched_filename, percentage = template_matching(gray_segment, self.templates)
				matched_filename = matched_filename.split(".")[0]
				matched_filename = matched_filename.split("_")[0]
				roi_cropped = cv2.putText(roi_cropped, matched_filename, (x_start, y_start+20),  cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0) )
				roi_cropped = cv2.putText(roi_cropped, percentage, (x_start, y_start+40),  cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0) )
				roi_cropped = cv2.putText(roi_cropped, str(index), (x_start, y_start+60),  cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0) )
				index += 1
				
				# segment data
				data = {
						"matched_filename": matched_filename,
						"row": i,
						"col": j,
						#"image": gray_segment,
				}
				segment_data.append(data)
				# cv2.imshow(f'Segment ({i}, {j})', segment)
		# invert data
		return segment_data, roi_cropped
	
	def decode_segment_data(self, segment_data):
		# read data from top to bottom and left to right
		segment_data = sorted(segment_data, key=lambda x: (x["col"], x["row"]))
		s = ""
		for d in segment_data:
			if d["matched_filename"] == '10':
				s += "0"
			elif d["matched_filename"] == '20':
				s += "X"
			else:
				s += d["matched_filename"]
		return s
		
	def display_detections(self, new_detections, video_output):
		# Update the OpenCV display with new detections
		# This method should be called from the main thread
		print("New Detections:", new_detections)
		markers = new_detections[0]
		#ids = new_detections[1]
		
		# no need to draw ids
		#ids = []
		
		# diaplay markers here:
		image = aruco.drawDetectedMarkers(video_output, markers, np.array([]))
		return image
		
	def set_detections(self, detections, image, is_valid):
		self.detections = detections
		# Put the new detections in the queue for the main thread to pick up
		# self.detections_queue.put(detections)
		if is_valid:
			segment_data, roi_cropped, roi_corners = self.process_detections(self.detections, image)
			self.roi_corners = roi_corners
			self.cropped_queue.put(roi_cropped)
			data_message = self.decode_segment_data(segment_data)
			return data_message
		else:
			self.roi_corners = None
			return ""
		
	def clear(self):
		# Clear the detections
		self.detections = ([], [])
		self.detections_queue.put(([], []))  
	
	def get_image(self):
		# if test enabled, use static image
		if self.test:
			path = TEST_FILE
			frame = cv2.imread(path)
			return frame
		# get current frame from webcam
		if self.capture == None:
			self.start_cam()
			self.capture = cv2.VideoCapture(WEBCAM)
			#self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
		if self.capture.isOpened():
			#do something
			ret, frame = self.capture.read()
			return frame
		else:
			print("Cannot open camera")

	def sendSocketData(self, data_message):
		print("sendSocketData", data_message)
		# socketio.emit('detection_data', {'data': data_message})
		# socketio.send('detection_data', data)
	
	def display_grid_lines(self, image):
		# Assume SEGMENT_OUTPUT_WIDTH and SEGMENT_OUTPUT_HEIGHT are defined for lines_image dimensions
		# Define source points for `lines_frame` (100x100 canvas corners)
		src_points = np.float32([[0, 0], [SEGMENT_OUTPUT_WIDTH-1, 0], 
														[SEGMENT_OUTPUT_WIDTH-1, SEGMENT_OUTPUT_HEIGHT-1], 
														[0, SEGMENT_OUTPUT_HEIGHT-1]])

		# Define the destination points for `roi_corners`
		dst_points = np.float32(self.roi_corners).reshape(-1, 2)

		# Compute the perspective transformation matrix
		transform_matrix = cv2.getPerspectiveTransform(src_points, dst_points)

		lines_image_rgba = cv2.cvtColor(lines_image, cv2.COLOR_BGR2BGRA)

		black_mask = cv2.cvtColor(lines_image, cv2.COLOR_BGR2GRAY) == 0
		lines_image_rgba[:, :, 3] = np.where(black_mask, 0, 255).astype(np.uint8)


		# Warp `lines_image` to the size and shape of `roi_corners`
		warped_lines = cv2.warpPerspective(lines_image_rgba, transform_matrix, (image.shape[1], image.shape[0]))

		# Ensure the `image` image is in RGBA format for alpha blending
		image_rgba = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

		# Separate the color and alpha channels from `warped_lines`
		overlay_color = warped_lines[:, :, :3]
		overlay_alpha = warped_lines[:, :, 3] / 255.0  # Normalize alpha to range [0, 1]

		# Blend the warped overlay onto `video_output_rgba` only where overlay is non-transparent
		for c in range(3):  # Loop over color channels (B, G, R)
				image_rgba[:, :, c] = (1.0 - overlay_alpha) * image_rgba[:, :, c] + overlay_alpha * overlay_color[:, :, c]
	
		image = cv2.cvtColor(image_rgba, cv2.COLOR_BGRA2BGR)
		return image
 
	def test_detection(self, raw_image):
		image = raw_image.copy()
		# Convert the image to grayscale (if necessary)
		gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

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
		
		# detect markers
		detector = aruco.ArucoDetector(aruco_dict, parameters)
		
		# Detect markers
		corners, ids, rejectedImgPoints = detector.detectMarkers(gray)
		
		image = aruco.drawDetectedMarkers(image, corners, ids)
		return image