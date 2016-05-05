# -*- coding: utf-8 -*-
# This file is part of Shoop Correios.
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from decimal import Decimal

from bs4 import BeautifulSoup
from shoop_correios.correios import _convert_to_int, \
    _convert_currency_to_decimal, _convert_to_bool, \
    CorreiosWS, CorreiosServico, CorreiosWSServerErrorException,\
    CorreiosWSServerTimeoutException
from shoop_correios.packing.correios import CorreiosPackage


def test_convert_service_element():
    CODIGO = '1234'
    VALOR = '432,56'
    PRAZO_ENTREGA = 2
    VALORMAOPROPRIA = '12,23'
    VALORAVISORECEBIMENTO = 'S'
    VALORDECLARADO = '84,43'
    ENTREGADOMICILIAR = 'N'
    ENTREGASABADO = 'S'
    ERRO = 43
    MSGERRO = 'teste 123'
    VALORSEMADICIONAIS = '843,12'
    OBSFIM = 'fim'

    xml_text = """
    <cservico>
        <codigo>{0}</codigo>
        <valor>{1}</valor>
        <prazoentrega>{2}</prazoentrega>
        <valormaopropria>{3}</valormaopropria>
        <valoravisorecebimento>{4}</valoravisorecebimento>
        <valordeclarado>{5}</valordeclarado>
        <entregadomiciliar>{6}</entregadomiciliar>
        <entregasabado>{7}</entregasabado>
        <erro>{8}</erro>
        <msgerro>{9}</msgerro>
        <valorsemadicionais>{10}</valorsemadicionais>
        <obsfim>{11}</obsfim>
    </cservico>
    """.format(CODIGO,
               VALOR,
               PRAZO_ENTREGA,
               VALORMAOPROPRIA,
               VALORAVISORECEBIMENTO,
               VALORDECLARADO,
               ENTREGADOMICILIAR,
               ENTREGASABADO,
               ERRO,
               MSGERRO,
               VALORSEMADICIONAIS,
               OBSFIM)

    bs = BeautifulSoup(xml_text)

    try:
        result = CorreiosWS.CorreiosWSServiceResult.from_service_element(bs.cservico)

        repr(result)
        assert result.codigo == CODIGO
        assert result.valor == _convert_currency_to_decimal(VALOR)
        assert result.prazo_entrega == _convert_to_int(PRAZO_ENTREGA)
        assert result.valor_mao_propria == _convert_currency_to_decimal(VALORMAOPROPRIA)
        assert result.valor_aviso_recebimento == _convert_currency_to_decimal(VALORAVISORECEBIMENTO)
        assert result.valor_declarado == _convert_currency_to_decimal(VALORDECLARADO)
        assert result.entrega_domiciliar == _convert_to_bool(ENTREGADOMICILIAR)
        assert result.entrega_sabado == _convert_to_bool(ENTREGASABADO)
        assert result.erro == _convert_to_int(ERRO)
        assert result.msg_erro == MSGERRO
        assert result.valor_sem_adicionais == _convert_currency_to_decimal(VALORSEMADICIONAIS)
        assert result.obs_fim == OBSFIM

    except CorreiosWSServerTimeoutException as e:
        pytest.skip(str(e))


def test_get_preco_prazo():
    CEP_ORIGEM = '89070400'
    CEP_DESTINO = '89070210'

    PACKAGE = CorreiosPackage()
    PACKAGE._weight = 4000
    PACKAGE._height = 400
    PACKAGE._width = 400
    PACKAGE._length = 400

    COD_EMPRESA = ''
    SENHA = ''

    try:
        result = CorreiosWS.get_preco_prazo(CEP_DESTINO,
                                            CEP_ORIGEM,
                                            CorreiosServico.PAC,
                                            PACKAGE,
                                            COD_EMPRESA,
                                            SENHA,
                                            False,
                                            0.0,
                                            False)

        assert not result is None
        assert result.codigo == CorreiosServico.PAC
        assert result.erro == 0
        assert result.msg_erro == ''
        assert result.valor > Decimal(0.0)


        # ERRORS
        result = CorreiosWS.get_preco_prazo(CEP_DESTINO,
                                            CEP_ORIGEM,
                                            'naoexiste',
                                            PACKAGE,
                                            COD_EMPRESA,
                                            SENHA,
                                            False,
                                            0.0,
                                            False)

        assert not result is None
        assert result.erro != 0
        assert result.msg_erro != ''
        assert result.valor == Decimal(0.0)

    except CorreiosWSServerTimeoutException as e:
        pytest.skip(str(e))

def test_raise_correios_ws_exc():
    try:
        with pytest.raises(CorreiosWSServerErrorException):
            raise CorreiosWSServerErrorException(500, 'a terrible error occured!')
    except CorreiosWSServerTimeoutException as e:
        pytest.skip(str(e))

def test_convert_to_int():
    assert _convert_to_int(None) == 0
    assert _convert_to_int('') == 0
    assert _convert_to_int('lalal') == 0
    assert _convert_to_int('123') == 123

def test_convert_currency_to_decimal():
    assert _convert_currency_to_decimal(None) == Decimal()
    assert _convert_currency_to_decimal('') == Decimal()
    assert _convert_currency_to_decimal('lalal') == Decimal()
    assert _convert_currency_to_decimal('123') == Decimal(123)
    assert _convert_currency_to_decimal('9873,32') - Decimal(9873.32) < 0.00001
    assert _convert_currency_to_decimal('9.873,32') - Decimal(9873.32) < 0.00001
    assert _convert_currency_to_decimal('0,83123') - Decimal(0.83123) < 0.00001

def test_convert_to_bool():
    assert _convert_to_bool('S') == True
    assert _convert_to_bool('s') == True
    assert _convert_to_bool('Y') == False
    assert _convert_to_bool('n') == False
    assert _convert_to_bool('') == False
    assert _convert_to_bool(None) == False
    assert _convert_to_bool(0.32131) == False
