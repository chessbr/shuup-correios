# -*- coding: utf-8 -*-
# This file is part of Shuup Correios.
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shuup.apps import AppConfig


class ShuupCorreiosAppConfig(AppConfig):
    name = __name__
    verbose_name = "Shuup Correios"
    label = "shuup_correios"
    provides = {
        "service_provider_admin_form": [
            __name__ + ".forms:CorreiosCarrierForm",
        ],
        "service_behavior_component_form": [
            __name__ + ".forms:CorreiosBehaviorComponentForm",
        ]
    }


default_app_config = __name__ + ".ShuupCorreiosAppConfig"

__version__ = "1.0.0.post0"
