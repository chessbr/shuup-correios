# -*- coding: utf-8 -*-
# This file is part of Shuup Correios.
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shuup_correios.forms import CorreiosBehaviorComponentForm, CorreiosCarrierForm


def test_forms():
    CorreiosBehaviorComponentForm()
    CorreiosCarrierForm()
