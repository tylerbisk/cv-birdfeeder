from queue import Queue
from threading import Thread
from collections import deque
import time
import cv2


class RecordClip:

    def __init__(self, max_length=48, fps=24):
        self.max_length = max_length
        self.frames = deque(maxlen=max_length)
        self.frames_queue: Queue = None
        self.video_writer = None
        self.current_thread = None
        self.recording = False
        self.fps = fps

    def update(self, frame):
        self.frames.append(frame)
        if self.recording:
            self.frames_queue.put(frame)

    def start_recording(self, output, fourcc):
        self.recording = True
        self.video_writer = cv2.VideoWriter(
            output, fourcc, self.fps,
            (self.frames[0].shape[1], self.frames[0].shape[0]), True)

        self.frames_queue = Queue()

        for frame in range(len(self.frames)):
            self.frames_queue.put(self.frames[frame])

        self.current_thread = Thread(target=self.record, args=())
        self.current_thread.daemon = True
        self.current_thread.start()

    def record(self):
        while self.recording:
            if self.frames_queue.empty() == False:
                self.video_writer.write(self.frames_queue.get())
            else:
                time.sleep(1 / self.fps)

        return

    def stop_recording(self):
        self.recording = False
        self.current_thread.join()
        while self.frames_queue.empty() == False:
            self.video_writer.write(self.frames_queue.get())
        self.video_writer.release()
