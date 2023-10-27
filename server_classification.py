import threading
import argparse
import datetime
import imutils
import time
import cv2
import pytz
import numpy as np
from imutils.video import VideoStream
import flask
from flask import Response
from flask import Flask
from processing.classification.yolo import YoloObjectDetection
from processing.motion.motion_detection import MotionDetection
from processing.recording.record_video_stream import RecordClip
from processing.email.send_email import send_email
import argparse
import threading
import os
from up import upload_to_youtube

# Video Stream
FRAMERATE = 24
RESOLUTION = (320, 240)
SMALL_RESOLUTION = 160

# motion detection
FRAMES_TO_AVERAGE = 24

# object detection
OBJECTS_TO_RECORD = [14]  # bird only for now

# Youtube
UPLOAD_YOUTUBE = False
CLIENT_SECRET_FILE = 'client_secrets.json'
API_NAME = 'youtube'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# Mail
SEND_MAIL = True
SEND_ATTACHMENT = True
SENDER_EMAIL = "tyler.s.m.eng.project@gmail.com"
SENDER_PASSWORD = "pqsueqfqlhetivzo"
RECEIVER_EMAIL = ["tyler07039@gmail.com"]  # vha3@cornell.edu"]

# Timing
MOTION_INTERVAL = 0.75
OBJECT_DETECT_INTERVAL = 5

# TODO Comment code
# TODO change OBOBJECTS_TO_RECORD to strings
# TODO add argparse for send_mail send_attatch upload_youtube

# initialize output
output = None

# initialize live fps
fps = 0

# create a lock
lock1 = threading.Lock()

# create a flask object
flask_object = Flask(__name__)

video_stream = None

# configure our video recorder
recorder = RecordClip(max_length=FRAMERATE * 2, fps=FRAMERATE)


def classify(args):
    # ensure global access to our variables
    global video_stream
    global output
    global lock1
    global fps
    global recorder

    use_pi_camera = args.use_pi_camera
    # yolo_network = args.yolo_network

    prev_frame_time = 0
    frame_time = 0

    # configure our video stream
    video_stream = VideoStream(usePiCamera=use_pi_camera,
                               resolution=RESOLUTION,
                               framerate=FRAMERATE).start()

    # wait while camera turns on
    time.sleep(1)

    # initialize our modules
    object_detection = YoloObjectDetection()
    motion_detection = MotionDetection()
    boxes = []
    confs = []
    class_ids = []
    motion = True
    current_frame = None
    current_frame_big = None
    current_time = last_motion_detected = last_object_detection = last_motion_detection = last_recorded_frame = last_object = time.time(
    )
    frames = 0

    while True:
        current_time = time.time()
        # shrink and convert the image to grayscale
        #     to make motion detection faster
        current_frame_big = video_stream.read()
        # current_frame_big = cv2.imread("dog.jpeg")
        current_frame = imutils.resize(current_frame_big, SMALL_RESOLUTION)
        current_frame_big = imutils.resize(current_frame_big, RESOLUTION[0])
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)

        # blur the image to reduce false positives from noise,
        # especially in night mode
        gray_frame = cv2.GaussianBlur(gray_frame, (5, 5), sigmaX=0, sigmaY=0)

        # detect objects for a few seconds if motion is detected
        if (current_time -
                last_motion_detection) >= MOTION_INTERVAL and motion == False:
            last_motion_detection = current_time
            (x1, x2, y1, y2) = motion_detection.detect_motion(gray_frame)
            # if there was motion detected
            if (x1 != np.inf and x2 != -np.inf and y1 != np.inf
                    and y2 != -np.inf):
                last_motion_detected = current_time
                motion = True

        # detect objects if motion
        scale = RESOLUTION[0] / SMALL_RESOLUTION
        if motion and (current_time - last_object_detection >=
                       OBJECT_DETECT_INTERVAL):
            last_object_detection = current_time
            (boxes, confs, class_ids,
             current_frame) = object_detection.detect_objects(current_frame,
                                                              scale=scale)

        if (current_time - last_motion_detected) > 6 and motion:
            motion = False

        current_frame_big = object_detection.draw_labels(
            boxes, confs, class_ids, current_frame_big)

        ### Recording ###
        # check to see if specific object was seen
        myset = set(OBJECTS_TO_RECORD) & set(class_ids)
        if bool(myset) or (motion and frames >= FRAMERATE*5): ## Record all motion, delete `or motion` later
            ### Record all motion, delete later
            if not myset:
                myset = set([14])
            ### Record all motion, delete later
            object = myset.pop()
            label = str(object_detection.classes[object])
            last_object = current_time

            if recorder.recording == False:
                print("now recording video of a " + label)
                timestamp = datetime.datetime.now(
                    tz=pytz.timezone('US/Eastern'))
                filename = "/home/pi/Documents/cv-birdfeeder/videos/{}_{}.mp4".format(
                    label, timestamp.strftime("%m_%d_%Y--%H_%M_%S"))
                recorder.start_recording(filename,
                                         cv2.VideoWriter_fourcc(*"mp4v"))

        if current_time - last_recorded_frame >= 1 / FRAMERATE:
            last_recorded_frame = current_time
            recorder.update(current_frame_big)
            # delete this later (only needed for motion recording so we dont record on first frame)
            if frames < FRAMERATE*6:
                frames += 1

        if recorder.recording and (current_time - last_object) >= (
                recorder.max_length / FRAMERATE):
            message = "Detected a " + label
            print(message)
            recorder.stop_recording()
            response = None
            if UPLOAD_YOUTUBE:
                title = label + " at " + str(timestamp)
                # command = """python upload_video.py --file="{}" --title="{}" --noauth_local_webserver --description="Uploaded automatically" --keywords="raspberry,pi,embedded,system" --category="22" --privacyStatus="private" """.format(
                #     filename, filename)
                response = upload_to_youtube(CLIENT_SECRET_FILE, API_NAME,
                                             API_VERSION, filename, title,
                                             SCOPES)
            if SEND_MAIL:
                if response is not None:
                    link = "https://www.youtube.com/watch?v=" + str(
                        response['id'])
                else:
                    link = None
                send_email(SENDER_EMAIL, RECEIVER_EMAIL, SENDER_PASSWORD,
                           message, link, SEND_ATTACHMENT, timestamp, filename)

        # feed in the frame to the motion detector for next time
        motion_detection.update_average(gray_frame)

        frame_time = time.time()
        fps = 1 / (frame_time - prev_frame_time)
        prev_frame_time = frame_time

        fps_text = "FPS: " + str(np.minimum(int(fps), FRAMERATE))

        text_size, _ = cv2.getTextSize(fps_text, cv2.FONT_HERSHEY_COMPLEX, 0.5,
                                       1)
        cv2.rectangle(current_frame_big, (5 - 1, 15 - text_size[1]),
                      (5 + text_size[0] + 1, 15 + 1), (255, 255, 255), -1)
        cv2.putText(current_frame_big,
                    "FPS: " + str(np.minimum(int(fps), FRAMERATE)), (5, 15),
                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 0), 1)

        # dont go updating global variables without a lock
        with lock1:
            output = current_frame_big.copy()

        time.sleep(1/(FRAMERATE*4))


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


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--use_pi_camera',
                        default=1,
                        type=int,
                        help='Whether to use Pi Camera or Web Camera')
    # parser.add_argument(
    #     '--yolo_network',
    #     type=str,
    #     default="tiny",
    #     help="Whether to use the 'tiny' yolo network or the regular one")

    return parser.parse_args()


if __name__ == '__main__':
    # we detect motion and send those frames to global var output
    args = get_args()
    thread = threading.Thread(target=classify, args=[args])
    thread.daemon = True
    thread.start()
    
    # Email ourselves the IP address and server address of the device
    send_email(SENDER_EMAIL, RECEIVER_EMAIL, SENDER_PASSWORD,
                           "Birdfeeder Details", None, True, datetime.datetime.now(tz=pytz.timezone('US/Eastern')), "/home/pi/Documents/ip.txt")
    
    # our flask object grabs those frames and creates output simultaneously
    flask_object.run(host='0.0.0.0',
                     port=8000,
                     debug=True,
                     threaded=True,
                     use_reloader=False)
    
    thread_count = threading.active_count()
    try:
        while True:
            time.sleep(60)
            if threading.active_count() < thread_count:
                os._exit(1)
    except KeyboardInterrupt:
        os._exit(1)

#just in case something goes wrong
video_stream.stop()
