# Copyright (C) 2018 Intel Corporation
#
# SPDX-License-Identifier: MIT

import django_rq
import json
import os

from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.db.models import Q
from rules.contrib.views import permission_required, objectgetter

from cvat.apps.authentication.decorators import login_required
from cvat.apps.authentication.auth import has_admin_role
from cvat.apps.engine.log import slogger
from .goturn import run_goturn_thread, clear_goturn_thread

'''
Django REST framework request handler for GoTurn
'''
@login_required
@permission_required(perm=["goturn.tracks.inference"], raise_exception=True)
def inference(request):
    try:
        if request.method == 'GET':
            params = request.GET
        elif request.method == 'POST':
            params = request.POST
        original_data = run_goturn_thread(params['id'], user=request.user)
        slogger.glob.info("goturn annotation for params {} with user: {}, HTTP Method: {}".format(params, request.user, request.method))
        return JsonResponse({"tid": params['id'], 
            "message": "GoTurn generated annotations for task {}".format(params['id']),
            "data": "{}".format(original_data)})
    except Exception as e:
        return HttpResponseBadRequest(str(e))

@login_required
@permission_required(perm=["goturn.tracks.inference"], raise_exception=True)
def clear(request):
    try:
        if request.method == 'GET':
            params = request.GET
        elif request.method == 'POST':
            params = request.POST
        result = clear_goturn_thread(params['id'], user=request.user)

        slogger.glob.info("goturn annotation for params {} with user: {}, HTTP Method: {}".format(params, request.user, request.method))
        return JsonResponse({"tid": params['id'], 
            "message": "GoTurn clearing annotations for task {}".format(params['id']),
            "result (should be empty)": "{}".format(result)})
    except Exception as e:
        return HttpResponseBadRequest(str(e))
