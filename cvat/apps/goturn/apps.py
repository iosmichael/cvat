# Copyright 2019 GURU Lab
#
# SPDX-License-Identifier: MIT

from django.apps import AppConfig


class GoTurnAnnotationConfig(AppConfig):
    name = "cvat.apps.goturn"

    def ready(self):
        from .permissions import setup_permissions

        setup_permissions()