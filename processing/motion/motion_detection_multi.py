import numpy as np
import imutils
import cv2


class MotionDetectionMulti:

    def __init__(self):
        self.average = None
        self.alpha = 0.1

    def update_average(self, image):
        if self.average is None:
            self.average = image.copy().astype("float")
            return

        cv2.accumulateWeighted(image, self.average, alpha=self.alpha)

    def detect_motion(self, image, threshold=25):
        #difference between current *image* and *self.average*
        difference = cv2.absdiff(self.average.astype("uint8"), image)

        # areas with motion set to 255
        thresh = cv2.threshold(difference, threshold, 255,
                               cv2.THRESH_BINARY)[1]

        # erode and dilate to remove noise
        thresh = cv2.erode(thresh, None, iterations=2)
        thresh = cv2.dilate(thresh, None, iterations=2)

        # put a box around the white regions
        contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)

        #return the box and the image
        ret = []
        for contour in contours:
            (x, y, w, h) = cv2.boundingRect(contour)
            ret += [(x, x + w, y, y + h)]
        return ret
