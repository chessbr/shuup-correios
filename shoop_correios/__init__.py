# -*- coding: utf-8 -*-
# This file is part of Shoop Correios.
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shoop.apps import AppConfig


class ShoopCorreiosAppConfig(AppConfig):
    name = __name__
    verbose_name = "Shoop Correios"
    label = "shoop_correios"
    provides = {
        "service_provider_admin_form": [
            __name__ + ".forms:CorreiosCarrierForm",
        ],
        "service_behavior_component_form": [
            __name__ + ".forms:CorreiosBehaviorComponentForm",
        ]
    }


default_app_config = __name__ + ".ShoopCorreiosAppConfig"
