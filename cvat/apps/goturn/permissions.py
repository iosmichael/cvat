# Copyright (C) 2018 Intel Corporation
#
# SPDX-License-Identifier: MIT

import rules

from cvat.apps.authentication.auth import has_admin_role, has_user_role

def setup_permissions():
	rules.add_perm('goturn.tracks.inference', has_admin_role | has_user_role)