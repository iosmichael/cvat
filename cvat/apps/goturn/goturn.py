import os
import copy
import fnmatch
import rq
from cvat.apps.engine.log import slogger
from cvat.apps.engine.models import Task as TaskModel
from cvat.apps.engine.serializers import LabeledDataSerializer
from cvat.apps.engine.annotation import put_task_data, patch_task_data, get_task_data

from .manager import GoTurnManager
from .utils import get_image_data

'''
[Core Tracking Method]
Inference Engine Annotation:
- input:
    * data: image data, provided by ImageLoader.get_image_data(path_to_data)
    * track_annotation: tracks from the TaskSerializer
    * job: Job for updating progress

- output:
    * result: {
        shapes: [],
        tracks: [(generated new tracks)],
        tags: [],
        version: 0
    }
'''
def run_inference_engine_annotation(engine, track_data, restricted=True):
    for i in range(len(track_data)):
        # generate shapes including the original ones
        track_data[i]["shapes"] = engine.get_goturn_shapes(track_data[i])

    result = {
        "shapes": [],
        "tracks": track_data,
        "tags": [],
        "version": 0
    }

    return result, track_data


def clear_goturn_thread(tid, user):
    try:
        result = {
            "shapes": [],
            "tracks": [],
            "tags": [],
            "version": 0
        }

        put_task_data(tid, user, result)
        
        slogger.glob.info("goturn annotation for clearing task {} done".format(tid))
        return result
    except Exception as e:
        try:
            slogger.task[tid].exception("exception was occurred during goturn annotation of the task", exc_info=True)
        except Exception as ex:
            slogger.glob.exception("exception was occurred during goturn annotation of the task {}: {}".format(tid, str(ex)), exc_info=True)
            raise ex
        raise e

def run_goturn_thread(tid, user, restricted=True, reset=False):
    try:
        db_task = TaskModel.objects.get(pk=tid)
        data = get_task_data(tid, user)
        slogger.glob.info("goturn annotation for task :\n{}".format(data))

        result, tracks = run_inference_engine_annotation(
            engine=GoTurnManager(get_image_data(db_task.get_data_dirname())),
            track_data=data["tracks"]
        )

        if result is None:
            slogger.glob.info("goturn annotation for task {} canceled by user".format(tid))
            return

        slogger.glob.info("result: \n {}".format(result))

        serializer = LabeledDataSerializer(data = result)
        if serializer.is_valid(raise_exception=True):
            if reset:
                put_task_data(tid, user, result)
            else:
                patch_task_data(tid, user, result, "update")

        slogger.glob.info("goturn annotation for task {} done".format(tid))
        return result

    except Exception as e:
        try:
            slogger.task[tid].exception("exception was occurred during goturn annotation of the task", exc_info=True)
        except Exception as ex:
            slogger.glob.exception("exception was occurred during goturn annotation of the task {}: {}".format(tid, str(ex)), exc_info=True)
            raise ex
        raise e

