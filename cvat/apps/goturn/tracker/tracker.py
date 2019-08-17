# OPENCV C++ Python Implementation
# Worked with Python3.4+
# Created by: Michael Liu, For CVAT Adaptation
# Email: x4liu@eng.ucsd.edu
# Date: Friday 09 Aug 2019

import cv2

class GoTurnTracker:
    """tracker class"""

    def __init__(self, deploy_proto, caffe_model):
        self.net = GoNet(deploy_proto, caffe_model)

    def init(self, image_curr, bbox):
        """ initializing the first frame in the video
        """
        bbox = BoundingBox(*bbox)
        self.image_prev = image_curr
        self.bbox_prev_tight = bbox
        self.INPUT_SIZE = 227
        return True

    def update(self, image_curr):

        pad_target_factor = 2.0
        prev_x, prev_y = self.bbox_prev_tight.get_center_x(), self.bbox_prev_tight.get_center_y()
        target_patch_width, target_patch_height = self.bbox_prev_tight.get_width() * pad_target_factor, self.bbox_prev_tight.get_height() * pad_target_factor
        target_patch_x1 = prev_x - self.bbox_prev_tight.get_width() * pad_target_factor / 2 + target_patch_width 
        target_patch_y1 = prev_y - self.bbox_prev_tight.get_height() * pad_target_factor / 2 + target_patch_height

        # make border
        prev_padded = cv2.copyMakeBorder(self.image_prev, (int)(target_patch_height), (int)(target_patch_height), (int)(target_patch_width), (int)(target_patch_width), cv2.BORDER_REPLICATE)
        curr_padded = cv2.copyMakeBorder(image_curr, (int)(target_patch_height), (int)(target_patch_height), (int)(target_patch_width), (int)(target_patch_width), cv2.BORDER_REPLICATE)

        prev_padded = prev_padded[int(target_patch_y1): int(target_patch_y1) + int(target_patch_height), int(target_patch_x1): int(target_patch_x1) + int(target_patch_width)]
        curr_padded = curr_padded[int(target_patch_y1): int(target_patch_y1) + int(target_patch_height), int(target_patch_x1): int(target_patch_x1) + int(target_patch_width)]

        prev_padded = cv2.resize(prev_padded, (self.INPUT_SIZE, self.INPUT_SIZE), 0, 0, cv2.INTER_LINEAR_EXACT)
        curr_padded = cv2.resize(curr_padded, (self.INPUT_SIZE, self.INPUT_SIZE), 0, 0, cv2.INTER_LINEAR_EXACT)
        
        curr_bbox = self.net.inference(prev_padded, curr_padded)
        curr_x1 = target_patch_x1 + (curr_bbox[0, 0] * target_patch_width / self.INPUT_SIZE) - target_patch_width
        curr_y1 = target_patch_y1 + (curr_bbox[0, 1] * target_patch_height / self.INPUT_SIZE) - target_patch_height
        curr_width = (curr_bbox[0, 2] - curr_bbox[0, 0]) * target_patch_width / self.INPUT_SIZE
        curr_height = (curr_bbox[0, 3] - curr_bbox[0, 1]) * target_patch_height / self.INPUT_SIZE
        bbox = BoundingBox(curr_x1, curr_y1, curr_width, curr_height)

        self.image_prev = image_curr
        self.bbox_prev_tight = bbox
        return True, bbox.get_data()

class GoNet:
    """Neural Network Class"""
    def __init__(self, deploy_proto, caffe_model):
        self.net = cv2.dnn.readNetFromCaffe(deploy_proto, caffe_model)
        self.mean = (128, 128, 128)
        self.scaleFactor = 1

    def inference(self, target_image, search_image):
        target_blob = cv2.dnn.blobFromImage(target_image, scalefactor=self.scaleFactor, mean=self.mean)
        search_blob = cv2.dnn.blobFromImage(search_image, scalefactor=self.scaleFactor, mean=self.mean)
        self.net.setInput(target_blob, name='data1')
        self.net.setInput(search_blob, name='data2')
        bbox = self.net.forward()
        return bbox


class BoundingBox:
    def __init__(self, x1, y1, width, height):
        self.x1 = x1
        self.y1 = y1
        self.width = width
        self.height = height

    def get_center_x(self):
        return self.x1 + self.width / 2

    def get_center_y(self):
        return self.y1 + self.height / 2

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_data(self):
        return [self.x1, self.y1, self.width, self.height]