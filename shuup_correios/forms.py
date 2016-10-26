# -*- coding: utf-8 -*-
# This file is part of Shuup Correios.
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from shuup.admin.forms import ShuupAdminForm
from shuup_correios.models import CorreiosCarrier, CorreiosBehaviorComponent
from django import forms


class CorreiosCarrierForm(ShuupAdminForm):
    class Meta:
        model = CorreiosCarrier
        exclude = ["identifier"]


class CorreiosBehaviorComponentForm(forms.ModelForm):
    class Meta:
        model = CorreiosBehaviorComponent
        exclude = ["identifier"]

    def __init__(self, *args, **kwargs):
        super(CorreiosBehaviorComponentForm, self).__init__(*args, **kwargs)
        self.fields['cod_servico'].widget.attrs['readonly'] = 'readonly'
