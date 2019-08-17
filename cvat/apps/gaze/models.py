import numpy as np

from django.db import models
from rest_framework import serializers
from cvat.apps.engine.models import FloatArrayField, Task

# Create your models and model serializers here.

class Gaze(models.Model):
	task = models.ForeignKey(Task, on_delete=models.CASCADE)
	frame = models.PositiveIntegerField()
	points = FloatArrayField()
	topic = models.TextField()
	confidence = models.FloatField()

class GazeSerializer(serializers.Serializer):
	frame = models.PositiveIntegerField(default=0)
	points = serializers.ListField(
		child=serializers.FloatField(min_value=0)
	)
	confidence = serializers.FloatField(min_value=0)
	topic = serializers.CharField(max_length=100)
