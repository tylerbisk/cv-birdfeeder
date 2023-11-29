import cv2
import imutils
import numpy as np


class MotionDetection:
    def __init__(self):
        self.average = None
        self.alpha = 0.1

    def update_average(self, image):
        if self.average is None:
            self.average = image.copy().astype("float")
            return

        cv2.accumulateWeighted(image, self.average, alpha=self.alpha)

    def detect_motion(self, image, scale, threshold=25):
        # difference between current *image* and *self.average*
        difference = cv2.absdiff(self.average.astype("uint8"), image)

        # areas with motion set to 255
        thresh = cv2.threshold(difference, threshold, 255, cv2.THRESH_BINARY)[1]

        # erode and dilate to remove noise
        thresh = cv2.erode(thresh, None, iterations=2)
        thresh = cv2.dilate(thresh, None, iterations=2)

        # put a box around the white regions
        contours = cv2.findContours(
            thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        contours = imutils.grab_contours(contours)

        # return the box and the image
        width = image.shape[1]
        height = image.shape[0]
        x1 = np.inf
        x2 = -np.inf
        y1 = np.inf
        y2 = -np.inf
        for contour in contours:
            (x, y, w, h) = cv2.boundingRect(contour)
            w = int(w * scale)
            h = int(h * scale)
            x = int(x * scale)
            y = int(y * scale)
            x1 = np.minimum(x1, x)
            x2 = np.maximum(x2, x + w)
            y1 = np.minimum(y1, y)
            y2 = np.maximum(y2, y + h)
        return (x1, x2, y1, y2)
