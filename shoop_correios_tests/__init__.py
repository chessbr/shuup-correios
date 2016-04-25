# -*- coding: utf-8 -*-
# This file is part of Shoop Correios.
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shoop_correios.correios import CorreiosWS
from decimal import Decimal


def create_mock_ws_result(with_error=False, mock_data={}):
    ws_result = CorreiosWS.CorreiosWSServiceResult()

    ws_result.codigo = mock_data.get('codigo') or '40010'
    ws_result.valor = mock_data.get('valor') or Decimal(15.10)
    ws_result.prazo_entrega = mock_data.get('prazo_entrega') or 2
    ws_result.valor_mao_propria = mock_data.get('valor_mao_propria') or Decimal()
    ws_result.valor_aviso_recebimento = mock_data.get('valor_aviso_recebimento') or Decimal()
    ws_result.valor_declarado = mock_data.get('valor_declarado') or Decimal()
    ws_result.entrega_domiciliar = mock_data.get('entrega_domiciliar') or False
    ws_result.entrega_sabado = mock_data.get('entrega_sabado') or False

    if with_error:
        ws_result.erro = 10
        ws_result.msg_erro = 'Erro!'
    else:
        ws_result.erro = 0
        ws_result.msg_erro = ''

    ws_result.valor_sem_adicionais = mock_data.get('valor_sem_adicionais') or Decimal()
    ws_result.obs_fim = mock_data.get('obs_fim') or ''
    return ws_result
