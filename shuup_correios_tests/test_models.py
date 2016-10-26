# -*- coding: utf-8 -*-
# This file is part of Shuup Correios.
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from decimal import Decimal
from mock import patch
from shuup_correios.correios import CorreiosWS, CorreiosWSServerTimeoutException
from shuup_correios.models import CorreiosCarrier, CorreiosBehaviorComponent


def test_models():
    CorreiosCarrier().get_service_choices()


def test_behavior_component():
    component = CorreiosBehaviorComponent()

    result1 = CorreiosWS.CorreiosWSServiceResult()
    result1.erro = 1
    result1.valor = Decimal()
    result1.msg_erro = 'erro1'

    result2 = CorreiosWS.CorreiosWSServiceResult()
    result2.erro = 2
    result2.valor = Decimal()
    result2.msg_erro = 'erro2'

    result3 = CorreiosWS.CorreiosWSServiceResult()
    result3.valor = Decimal()
    result3.erro = 0

    results = [result1, result2, result3]

    with patch.object(component, '_pack_source', return_value=[1, 2, 3]):
        with patch.object(component, '_get_correios_results', return_value=results):
            assert len(component.get_unavailability_reasons(None, None)) == 2
            list(component.get_costs(None, None))
            component.get_delivery_time(None, None)

    # check for CorreiosWSServerTimeoutException
    with patch.object(CorreiosBehaviorComponent, '_pack_source', return_value=[1, 2, 3]):
        with patch.object(CorreiosBehaviorComponent, '_get_correios_results') as mock:
            mock.side_effect = CorreiosWSServerTimeoutException()
            errors = component.get_unavailability_reasons(None, None)
            assert len(errors) == 1
            list(component.get_costs(None, None))
            component.get_delivery_time(None, None)
