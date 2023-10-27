import threading
import argparse
import datetime
import imutils
import time
import cv2
import numpy as np
from imutils.video import VideoStream
import flask
from flask import Response
from flask import Flask

FRAMERATE = 24
RESOLUTION = (640, 480)
FRAMES_TO_AVERAGE = 48

# initialize output
output = None

# initialize live fps
fps = 0

# create a lock
lock1 = threading.Lock()

# create a flask object
flask_object = Flask(__name__)

# configure our video stream
video_stream = VideoStream(usePiCamera=False,
                           resolution=RESOLUTION,
                           framerate=FRAMERATE).start()

# wait while camera turns on
time.sleep(1)


def detect_motion():
    # ensure global access to our variables
    global video_stream
    global output
    global lock1
    global fps

    prev_frame_time = 0
    frame_time = 0

    while True:
        # shrink and convert the image to grayscale
        #     to make motion detection faster
        current_frame = imutils.resize(video_stream.read(), 320)

        frame_time = time.time()
        fps = 1 / (frame_time - prev_frame_time)
        prev_frame_time = frame_time

        fps_text = "FPS: " + str(np.minimum(int(fps), FRAMERATE))

        text_size, _ = cv2.getTextSize(fps_text, cv2.FONT_HERSHEY_COMPLEX, 0.5,
                                       1)
        cv2.rectangle(current_frame, (5 - 1, 15 - text_size[1]),
                      (5 + text_size[0] + 1, 15 + 1), (255, 255, 255), -1)
        cv2.putText(current_frame,
                    "FPS: " + str(np.minimum(int(fps), FRAMERATE)), (5, 15),
                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 0), 1)

        # dont go updating global variables without a lock
        with lock1:
            output = current_frame.copy()


def create_output():
    global output
    global lock1

    while output is None:
        # do nothing and wait
        continue

    while True:

        with lock1:
            (retval, image) = cv2.imencode(".jpg", output)

        # if retval is False
        if not retval:
            # skip a frame
            continue

        # convert to byte array so we can use it in html
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + bytearray(image) +
               b'\r\n')


# point our flask object to index.html for the website...
@flask_object.route('/')
def index():
    return flask.render_template("index2.html")


# ... and to our frame as a byte array (create_output()) for the video_feed
@flask_object.route('/video_feed')
def video_feed():
    return Response(
        create_output(),  # TODO: understand mimetype
        mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == '__main__':
    # we detect motion and send those frames to global var output
    thread = threading.Thread(target=detect_motion, args=())
    thread.daemon = True
    thread.start()

    # our flask object grabs those frames and creates output simultaneously
    flask_object.run(host='0.0.0.0',
                     port=8000,
                     debug=True,
                     threaded=True,
                     use_reloader=False)

#just in case something goes wrong
video_stream.stop()
