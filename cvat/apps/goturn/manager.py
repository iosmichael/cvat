import copy
import os
from cvat.apps.engine.models import ShapeType
from cvat.apps.engine.log import slogger
from .image_loader import ImageLoader
from .tracker.tracker import GoTurnTracker

class GoTurnManager:

    def __init__(self, imageList):
        path = os.getcwd()
        GOTURN_INSTALL_PATH = "/home/django/cvat/apps/goturn/tracker"
        self.tracker = GoTurnTracker(deploy_proto=os.path.join(GOTURN_INSTALL_PATH, 'goturn.prototxt'), caffe_model=os.path.join(GOTURN_INSTALL_PATH, 'goturn.caffemodel'))
        slogger.glob.info("current work directory: {} should be {}".format(os.getcwd(), GOTURN_INSTALL_PATH))
        self.imageList = imageList
        slogger.glob.info("imageList: {}".format(self.imageList))
        self.imageLoader = ImageLoader(self.imageList)

    '''
    Implementation of GoTurn Tracking Algorithm on One Track
    - input:
        * track: {
            'shapes': [
                shape: {
                    frame: int
                    attributes: {...deepcopy}
                    outside
                }
            ]
        }
    '''
    def get_goturn_shapes(self, track):
        '''Need to Create a GoTurn Tracker'''
        shapes = []
        curr_frame = track["shapes"][0]["frame"]
        prev_shape = {}

        for shape in track["shapes"]:
            if prev_shape:
                assert shape["frame"] > curr_frame
                for attr in prev_shape["attributes"]:
                    if attr["spec_id"] not in map(lambda el: el["spec_id"], shape["attributes"]):
                        shape["attributes"].append(copy.deepcopy(attr))
                if not prev_shape["outside"]:
                    # implement goturn algorithm here
                    if shape["frame"] > curr_frame + 1:
                        shapes.extend(self.goturn_infer(prev_shape, shape))

            shape["keyframe"] = True
            shapes.append(shape)
            curr_frame = shape["frame"]
            prev_shape = shape
        return shapes
    
    def goturn_infer(self, start_shape, end_shape):
        shapes = []
        xtl, ytl, xbr, ybr = start_shape['points']
        ok = self.tracker.init(self.imageLoader[start_shape['frame']], [xtl, ytl, xbr - xtl, ybr - ytl])
        if not ok:
            return []

        for frame in range(start_shape['frame'] + 1, end_shape['frame']):
            shape = copy.deepcopy(start_shape)
            shape.pop("id", [])
            ok, pts = self.tracker.update(self.imageLoader[frame])
            shape['points'] = [pts[0], pts[1], pts[0] + pts[2], pts[1] + pts[3]]
            if not ok:
                break
            shape['keyframe'] = False
            shape['frame'] = frame
            shapes.append(shape)

        return shapes
