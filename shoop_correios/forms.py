# -*- coding: utf-8 -*-
# This file is part of Shoop Correios.
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from shoop.admin.forms import ShoopAdminForm
from shoop_correios.models import CorreiosCarrier, CorreiosBehaviorComponent
from django import forms

class CorreiosCarrierForm(ShoopAdminForm):
    class Meta:
        model = CorreiosCarrier
        exclude = ["identifier"]

class CorreiosBehaviorComponentForm(forms.ModelForm):
    class Meta:
        model = CorreiosBehaviorComponent
        exclude = ["identifier"]
