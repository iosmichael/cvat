import numpy as np
import os
from django.conf import settings

from .models import Gaze, GazeSerializer
from cvat.apps.engine.log import slogger
from cvat.apps.engine.models import Task

'''
get gaze objects from task id
filter based on frame number from the task segment
'''
def get_gazes_from_db(pk):
	gazes = Gaze.objects.select_related('task').filter(task_id=pk).order_by('frame')
	return gazes

'''
decorator to produce minimum changes to the original code, while achieve similar functionality
'''

def preprocessing_gaze_file(tid, upload_dir, data):
	slogger.glob.info("Preprocessing server files: {}".format(data))
	file_path = None
	# find the file with .npy extension, and remove the path
	for path in data['client_files']:
		if path.split('.')[-1] == 'npy':
			file_path = path
			data['client_files'].remove(path)
	save_gazes_to_db(tid, os.path.join(upload_dir, file_path))
	return tid, data

def save_gazes_to_db(pk, file_path):
	if file_path:
		db_task = Task.objects.prefetch_related("image_set").get(id=pk)
		data = np.load(file_path)
		# sort data based on timestamp
		gazes = []
		start_frame, stop_frame = db_task.start_frame, db_task.stop_frame
		for i, item in enumerate(sorted(list(data), key=lambda x: x['timestamp'])):
			if (start_frame <= i) and (i <= stop_frame):
				gazes.append(Gaze(
					task=db_task,
					frame=i,
					points=item['norm_pos'],
					confidence=item['confidence'],
					topic=item['topic']))
		Gaze.objects.bulk_create(gazes)
		slogger.glob.info("New gaze data created for task {}".format(pk))
	else:
		slogger.glob.info("Couldn't find gaze data for task {}".format(pk))

