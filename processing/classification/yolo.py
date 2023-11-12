import numpy as np
import imutils
import cv2
import time


class YoloObjectDetection:

    def __init__(self):

        network = cv2.dnn.readNet("yolo/yolov3-tiny.weights", "yolo/yolov3-tiny.cfg")
        
        classes = []
        with open("yolo/coco.names", "r") as f:
            classes = [line.strip() for line in f.readlines()]

        #Determine the output layer names from the YOLO model
        output_layers = network.getUnconnectedOutLayersNames()
        self.network = network
        self.classes = classes
        self.output_layers = output_layers
        self.conf_thresh = 0.01

    def detect_objects(self, image, scale=1):
        blob = cv2.dnn.blobFromImage(image,
                                     scalefactor=0.00392,
                                     size=(160, 160),
                                     mean=(0, 0, 0),
                                     swapRB=True,
                                     crop=False)
        self.network.setInput(blob)
        outputs = self.network.forward(self.output_layers)

        width = image.shape[1]
        height = image.shape[0]
        boxes = []
        confs = []
        class_ids = []
        for output in outputs:
            for detect in output:
                scores = detect[5:]
                class_id = np.argmax(scores)
                conf = scores[class_id]
                if conf > self.conf_thresh:
                    center_x = int(detect[0] * width * scale)
                    center_y = int(detect[1] * height * scale)
                    w = int(detect[2] * width * scale)
                    h = int(detect[3] * height * scale)
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    boxes.append([x, y, w, h])
                    confs.append(float(conf))
                    class_ids.append(class_id)
        return (boxes, confs, class_ids, image)

    def draw_labels(self, boxes, confs, class_ids, image):
        indexes = cv2.dnn.NMSBoxes(boxes, confs, 0.5, 0.4)
        font = cv2.FONT_HERSHEY_PLAIN
        for i in range(len(boxes)):
            if i in indexes:
                x, y, w, h = boxes[i]
                label = str(self.classes[class_ids[i]])
                conf = str(round(confs[i], 3))
                cv2.rectangle(image, (x, y), (x + w, y + h), (255, 255, 0), 2)
                cv2.putText(image, label + ", " + conf, (x, y - 5), font, 1.2,
                            (255, 255, 0), 1)
        return image
