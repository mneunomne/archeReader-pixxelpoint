from flask import Flask, render_template, Response
from flask_socketio import SocketIO, send, emit
from image_processing import ImageProcessor
import numpy as np
import cv2
from globals import SEGMENT_OUTPUT_WIDTH, SEGMENT_OUTPUT_HEIGHT, FLASK_SERVER_IP, FLASK_SERVER_PORT, MAX_ATTEMPTS

app = Flask(__name__, static_url_path='', static_folder='static', template_folder='static')

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# socketio.run(app)

video_output = None
cropped_output = None
avaraged_output = None
live_output = None
capture_avarage_frames = False

# make cropped image blank with SEGMENT_OUTPUT_WIDTH and SEGMENT_OUTPUT_HEIGHT with 3 channels using opencv / np
# cropped_output = np.zeros((SEGMENT_OUTPUT_HEIGHT, SEGMENT_OUTPUT_WIDTH, 3), np.uint8)
# video_output = np.zeros((SEGMENT_OUTPUT_HEIGHT, SEGMENT_OUTPUT_WIDTH, 3), np.uint8)

current_segment_index = 0

imageProcessor = ImageProcessor()

def sendVideoOutput(frame):
    global video_output
    video_output = frame

def sendLiveOutput(frame):
    global live_output
    live_output = frame

def sendAvaragedOutput(frame):
		global avaraged_output
		avaraged_output = frame	

def sendCroppedOutput(frame):
    global cropped_output
    cropped_output = frame

def gen_frames():  # generate frame by frame from camera
    global video_output
    while True:
        # Capture frame-by-frame
        if video_output is None:
            break
        else:
            frame = video_output.copy()
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

def getState():
    global ready_to_read
    return ready_to_read

@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/cropped_image')
def cropped_image():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_cropped(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_avaraged_frames')
def get_avaraged_frames():
    global avaraged_output
    global capture_avarage_frames
    capture_avarage_frames = True
    attempts = 0
    while avaraged_output is None and attempts < 100:
      attempts = attempts + 1
    if avaraged_output is None:
      return Response('timeout', mimetype='text/plain')
    else:
      return Response('done', mimetype='text/plain')

@app.route('/movement_end/<int:direction>')
def on_movement_end(direction):
    global ready_to_read
    ready_to_read = True
    print('movement end', direction)
    return Response('done', mimetype='text/plain')

@app.route('/test/<string:json>', methods=['GET', 'POST'])
def test(json):
    global video_output
    print('video_output', video_output)
    if video_output is None:
        print('cropped_output is None')
        return Response('fail', mimetype='text/plain')
    else:
        imageProcessor.process_image(video_output)
    ready_to_read = True
    print('received test', json)
    return Response('done', mimetype='text/plain')

@app.route('/on_segment/<int:segmentIndex>', methods=['GET', 'POST'])
def on_segment(segmentIndex):
    print('received segmentIndex', segmentIndex)
    global avaraged_output
    if avaraged_output is None:
        print('avaraged_output is None')
        return Response('fail', mimetype='text/plain')
    else:
        imageProcessor.clear_stored_markers()
        is_valid = False
        attempts = 0
        while not is_valid and attempts < MAX_ATTEMPTS:
            attempts = attempts + 1
            is_valid, msg = imageProcessor.process_image(avaraged_output, live_output, segmentIndex)
            print('is_valid', is_valid, attempts)
            if is_valid: 
                attempts = MAX_ATTEMPTS
        if is_valid:
            print('msg', msg)
            return Response(msg, mimetype='text/plain')
        else:
            return Response('fail', mimetype='text/plain')

@app.route('/clear', methods=['GET', 'POST'])
def on_clear():
    imageProcessor.clear()
    return Response('ok', mimetype='text/plain')

@app.route('/cropped_feed')
def cropped_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_cropped(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

@app.route('/dates')
def dates():
    """Video streaming home page."""
    return render_template('dates.html')