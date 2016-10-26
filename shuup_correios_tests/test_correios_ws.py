# -*- coding: utf-8 -*-
# This file is part of Shuup Correios.
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from decimal import Decimal
import requests
from mock import patch, Mock

import pytest
import xmltodict
from shuup_correios.correios import (CorreiosServico, CorreiosWS,
                                     CorreiosWSServerErrorException,
                                     CorreiosWSServerTimeoutException,
                                     _convert_currency_to_decimal,
                                     _convert_to_bool, _convert_to_int)
from django.core.cache import caches
from shuup_order_packager.package import SimplePackage


def test_convert_service():
    _CODIGO = '1234'
    _VALOR = '432,56'
    _PRAZO_ENTREGA = 2
    _VALORMAOPROPRIA = '12,23'
    _VALORAVISORECEBIMENTO = 'S'
    _VALORDECLARADO = '84,43'
    _ENTREGADOMICILIAR = 'N'
    _ENTREGASABADO = 'S'
    _ERRO = 43
    _MSGERRO = 'teste 123'
    _VALORSEMADICIONAIS = '843,12'
    _OBSFIM = 'fim'

    xml_text = """
    <cResultado xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://tempuri.org/">
        <Servicos>
            <cServico>
                <Codigo>{0}</Codigo>
                <Valor>{1}</Valor>
                <PrazoEntrega>{2}</PrazoEntrega>
                <ValorMaoPropria>{3}</ValorMaoPropria>
                <ValorAvisoRecebimento>{4}</ValorAvisoRecebimento>
                <ValorValorDeclarado>{5}</ValorValorDeclarado>
                <EntregaDomiciliar>{6}</EntregaDomiciliar>
                <EntregaSabado>{7}</EntregaSabado>
                <Erro>{8}</Erro>
                <MsgErro>{9}</MsgErro>
                <ValorSemAdicionais>{10}</ValorSemAdicionais>
                <obsFim>{11}</obsFim>
            </cServico>
        </Servicos>
    </cResultado>
    """.format(_CODIGO,
               _VALOR,
               _PRAZO_ENTREGA,
               _VALORMAOPROPRIA,
               _VALORAVISORECEBIMENTO,
               _VALORDECLARADO,
               _ENTREGADOMICILIAR,
               _ENTREGASABADO,
               _ERRO,
               _MSGERRO,
               _VALORSEMADICIONAIS,
               _OBSFIM)

    d = xmltodict.parse(xml_text)

    result = CorreiosWS.CorreiosWSServiceResult.from_service(d['cResultado']['Servicos']['cServico'])

    repr(result)
    assert result.codigo == _CODIGO
    assert result.valor == _convert_currency_to_decimal(_VALOR)
    assert result.prazo_entrega == _convert_to_int(_PRAZO_ENTREGA)
    assert result.valor_mao_propria == _convert_currency_to_decimal(_VALORMAOPROPRIA)
    assert result.valor_aviso_recebimento == _convert_currency_to_decimal(_VALORAVISORECEBIMENTO)
    assert result.valor_declarado == _convert_currency_to_decimal(_VALORDECLARADO)
    assert result.entrega_domiciliar == _convert_to_bool(_ENTREGADOMICILIAR)
    assert result.entrega_sabado == _convert_to_bool(_ENTREGASABADO)
    assert result.erro == _convert_to_int(_ERRO)
    assert result.msg_erro == _MSGERRO
    assert result.valor_sem_adicionais == _convert_currency_to_decimal(_VALORSEMADICIONAIS)
    assert result.obs_fim == _OBSFIM


def test_get_preco_prazo_success():
    _CODIGO = CorreiosServico.PAC
    _VALOR = '432,56'
    _PRAZO_ENTREGA = 2
    _VALORMAOPROPRIA = '12,23'
    _VALORAVISORECEBIMENTO = 'S'
    _VALORDECLARADO = '84,43'
    _ENTREGADOMICILIAR = 'N'
    _ENTREGASABADO = 'S'
    _ERRO = 0
    _MSGERRO = ''
    _VALORSEMADICIONAIS = '843,12'
    _OBSFIM = 'fim'

    _CEP_ORIGEM = '89070400'
    _CEP_DESTINO = '89070210'

    _PACKAGE = SimplePackage()
    _PACKAGE._weight = 4000
    _PACKAGE._height = 400
    _PACKAGE._width = 400
    _PACKAGE._length = 400

    _COD_EMPRESA = ''
    _SENHA = ''

    xml_text = """<Servicos>
            <cServico>
                <Codigo>{0}</Codigo>
                <Valor>{1}</Valor>
                <PrazoEntrega>{2}</PrazoEntrega>
                <ValorMaoPropria>{3}</ValorMaoPropria>
                <ValorAvisoRecebimento>{4}</ValorAvisoRecebimento>
                <ValorValorDeclarado>{5}</ValorValorDeclarado>
                <EntregaDomiciliar>{6}</EntregaDomiciliar>
                <EntregaSabado>{7}</EntregaSabado>
                <Erro>{8}</Erro>
                <MsgErro>{9}</MsgErro>
                <ValorSemAdicionais>{10}</ValorSemAdicionais>
                <obsFim>{11}</obsFim>
            </cServico>
        </Servicos>
    """.format(_CODIGO,
               _VALOR,
               _PRAZO_ENTREGA,
               _VALORMAOPROPRIA,
               _VALORAVISORECEBIMENTO,
               _VALORDECLARADO,
               _ENTREGADOMICILIAR,
               _ENTREGASABADO,
               _ERRO,
               _MSGERRO,
               _VALORSEMADICIONAIS,
               _OBSFIM)

    response_mock = Mock(status_code=200, text=xml_text)

    args = (_CEP_DESTINO, _CEP_ORIGEM, _CODIGO, _PACKAGE,
            _COD_EMPRESA, _SENHA, False, 0.0, False)

    with patch.object(requests, "post", return_value=response_mock):
        result = CorreiosWS.get_preco_prazo(*args)

        assert result is not None
        assert result.codigo == _CODIGO
        assert result.erro == 0
        assert result.msg_erro == ''
        assert result.valor == _convert_currency_to_decimal(_VALOR)

    # Multiplos servicos
    xml_text = """<Servicos>
            <cServico>
                <Codigo>{0}</Codigo>
                <Valor>{1}</Valor>
                <PrazoEntrega>{2}</PrazoEntrega>
                <ValorMaoPropria>{3}</ValorMaoPropria>
                <ValorAvisoRecebimento>{4}</ValorAvisoRecebimento>
                <ValorValorDeclarado>{5}</ValorValorDeclarado>
                <EntregaDomiciliar>{6}</EntregaDomiciliar>
                <EntregaSabado>{7}</EntregaSabado>
                <Erro>{8}</Erro>
                <MsgErro>{9}</MsgErro>
                <ValorSemAdicionais>{10}</ValorSemAdicionais>
                <obsFim>{11}</obsFim>
            </cServico>
            <cServico>
                <Codigo>1321312</Codigo>
                <Valor>3132,123</Valor>
                <PrazoEntrega>14</PrazoEntrega>
                <ValorMaoPropria>N</ValorMaoPropria>
                <ValorAvisoRecebimento>N</ValorAvisoRecebimento>
                <ValorValorDeclarado>0,00</ValorValorDeclarado>
                <EntregaDomiciliar>N</EntregaDomiciliar>
                <EntregaSabado>N</EntregaSabado>
                <Erro>0</Erro>
                <MsgErro></MsgErro>
                <ValorSemAdicionais>0,00</ValorSemAdicionais>
                <obsFim></obsFim>
            </cServico>
        </Servicos>
    """.format(_CODIGO,
               _VALOR,
               _PRAZO_ENTREGA,
               _VALORMAOPROPRIA,
               _VALORAVISORECEBIMENTO,
               _VALORDECLARADO,
               _ENTREGADOMICILIAR,
               _ENTREGASABADO,
               _ERRO,
               _MSGERRO,
               _VALORSEMADICIONAIS,
               _OBSFIM)

    response_mock = Mock(status_code=200, text=xml_text)

    with patch.object(requests, "post", return_value=response_mock):
        # deve retornar o primeiro item
        result = CorreiosWS.get_preco_prazo(*args)

        assert result.codigo == _CODIGO
        assert result.valor == _convert_currency_to_decimal(_VALOR)
        assert result.prazo_entrega == _convert_to_int(_PRAZO_ENTREGA)
        assert result.valor_mao_propria == _convert_currency_to_decimal(_VALORMAOPROPRIA)
        assert result.valor_aviso_recebimento == _convert_currency_to_decimal(_VALORAVISORECEBIMENTO)
        assert result.valor_declarado == _convert_currency_to_decimal(_VALORDECLARADO)
        assert result.entrega_domiciliar == _convert_to_bool(_ENTREGADOMICILIAR)
        assert result.entrega_sabado == _convert_to_bool(_ENTREGASABADO)
        assert result.erro == _convert_to_int(_ERRO)
        assert result.msg_erro == _MSGERRO
        assert result.valor_sem_adicionais == _convert_currency_to_decimal(_VALORSEMADICIONAIS)
        assert result.obs_fim == _OBSFIM

    # troca o cache dummy pelo default, que deve estar na memória
    import shuup_correios
    with patch.object(shuup_correios.correios, "correios_cache", new=caches["default"]):
        with patch.object(requests, "post", return_value=response_mock):
            CorreiosWS.get_preco_prazo(*args)
            CorreiosWS.get_preco_prazo(*args)
            CorreiosWS.get_preco_prazo(*args)

            cache = caches["default"]
            assert len(cache._cache.values()) == 1


def test_get_preco_prazo_errors():
    xml_text = """<Servicos>
        <cServico>
          <Codigo>41106</Codigo>
          <Valor>0,00</Valor>
          <PrazoEntrega>0</PrazoEntrega>
          <ValorMaoPropria>0,00</ValorMaoPropria>
          <ValorAvisoRecebimento>0,00</ValorAvisoRecebimento>
          <ValorValorDeclarado>0,00</ValorValorDeclarado>
          <EntregaDomiciliar />
          <EntregaSabado />
          <Erro>-20</Erro>
          <MsgErro>errrrrrrroor</MsgErro>
          <ValorSemAdicionais>0,00</ValorSemAdicionais>
          <obsFim />
        </cServico>
      </Servicos>
    """

    response_mock = Mock(status_code=200, text=xml_text)
    _PACKAGE = SimplePackage()

    with patch.object(requests, "post", return_value=response_mock):
        result = CorreiosWS.get_preco_prazo("312321321321",
                                            "312312321",
                                            'naoexiste',
                                            _PACKAGE,
                                            "321312",
                                            "31312",
                                            False,
                                            0.0,
                                            False)

        assert result is not None
        assert result.erro == -20
        assert result.msg_erro == 'errrrrrrroor'
        assert result.valor == Decimal(0.0)

    # must throw exception
    response_mock = Mock(status_code=500, text=xml_text)

    with patch.object(requests, "post", return_value=response_mock):
        with pytest.raises(CorreiosWSServerErrorException):
            result = CorreiosWS.get_preco_prazo("312321321321",
                                                "312312321",
                                                'naoexiste',
                                                _PACKAGE,
                                                "321312",
                                                "31312",
                                                False,
                                                0.0,
                                                False)

    with patch.object(requests, "post") as mock:
        mock.side_effect = requests.exceptions.Timeout("peeeee")

        with pytest.raises(CorreiosWSServerTimeoutException):
            result = CorreiosWS.get_preco_prazo("312321321321",
                                                "312312321",
                                                'naoexiste',
                                                _PACKAGE,
                                                "321312",
                                                "31312",
                                                False,
                                                0.0,
                                                False)


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
    assert _convert_to_bool('S')
    assert _convert_to_bool('s')
    assert _convert_to_bool('Y') is False
    assert _convert_to_bool('n') is False
    assert _convert_to_bool('') is False
    assert _convert_to_bool(None) is False
    assert _convert_to_bool(0.32131) is False


def test_correios_exception():
    exc = CorreiosWSServerErrorException(1234, "nothing")
    repr(exc)
