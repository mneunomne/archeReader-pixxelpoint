import cv2 
import numpy as np
import os
from globals import SEGMENT_OUTPUT_WIDTH, SEGMENT_OUTPUT_HEIGHT, INNER_COLS, INNER_ROWS, PADDING_RIGHT, PADDING_LEFT, PADDING_TOP, PADDING_BOTTOM

def list_ports():
    """
    Test the ports and returns a tuple with the available ports and the ones that are working.
    """
    non_working_ports = []
    dev_port = 0
    working_ports = []
    available_ports = []
    while len(non_working_ports) < 6: # if there are more than 5 non working ports stop the testing. 
        camera = cv2.VideoCapture(dev_port)
        if not camera.isOpened():
            non_working_ports.append(dev_port)
            # print("Port %s is not working." %dev_port)
        else:
            is_reading, img = camera.read()
            w = camera.get(3)
            h = camera.get(4)
            if is_reading:
                # print("Port %s is working and reads images (%s x %s)" %(dev_port,h,w))
                working_ports.append(dev_port)
            else:
                # print("Port %s for camera ( %s x %s) is present but does not reads." %(dev_port,h,w))
                available_ports.append(dev_port)
        dev_port +=1
    return available_ports,working_ports,non_working_ports


def get_center_point(corners):
    # Calculate the average of x-coordinates and y-coordinates
    avg_x = np.mean(corners[:, :, 0])
    avg_y = np.mean(corners[:, :, 1])
    return int(avg_x), int(avg_y)

def load_templates(folder_path):
    templates = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.png'):
            print("filename", filename)
            # Load the SVG file using your preferred method
            # Convert the SVG to a raster image (e.g., PNG) and append it to templates
            # You'll need to replace the next line with actual code to convert SVG to image
            path = os.path.join(folder_path, filename)
            template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            templates.append((template, filename))
    return templates

def template_matching(segment, templates):
    best_match_score = float('-inf')
    best_template = None

    for (template, filename) in templates:
        result = cv2.matchTemplate(segment, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, _, _ = cv2.minMaxLoc(result)
        if max_val > best_match_score:
            best_match_score = max_val
            best_template = template, filename, str(float("{:.3f}".format(best_match_score)))
    return best_template

def perspective_transform(segment, segment_corners):
    # Define the destination points for the transformation (7x8 rectangular shape)
    dst = np.array([[0, 0], [segment.shape[1] - 1, 0], [segment.shape[1] - 1, segment.shape[0] - 1], [0, segment.shape[0] - 1]], dtype='float32')

    # Apply perspective transformation
    M = cv2.getPerspectiveTransform(segment_corners, dst)
    warped_segment = cv2.warpPerspective(segment, M, (segment.shape[1], segment.shape[0]))

    return warped_segment

def draw_lines():
		# transparent canvas
		lines_frame = np.zeros((SEGMENT_OUTPUT_HEIGHT, SEGMENT_OUTPUT_WIDTH, 3), np.uint8)
		lines_frame = cv2.cvtColor(lines_frame, cv2.COLOR_BGR2BGRA)
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
					lines_frame = cv2.line(lines_frame, start_point, end_point, (0, 255, 0), 2)
		return lines_frame
		