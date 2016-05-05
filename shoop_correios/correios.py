# -*- coding: utf-8 -*-
# This file is part of Shoop Correios.
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import requests

from decimal import Decimal
from django.utils.log import getLogger
from django.conf import settings
from bs4 import BeautifulSoup
from requests.exceptions import Timeout

logger = getLogger(__name__)

# URL de acesso ao cálculo de preço e prazo
CORREIOS_WS_PRECO_PRAZO_URL = "http://ws.correios.com.br/calculador/CalcPrecoPrazo.aspx"


class CorreiosServico(object):
    """ Serviço de entrega dos Correios  """

    ESEDEX = '99999'
    PAC = '41106'
    SEDEX = '40010'
    SEDEX_A_COBRAR = '40045'
    SEDEX_10 = '40215'
    SEDEX_HOJE = '40290'


class CorreiosFormatoEncomenda(object):
    """ Formato da encomenda """
    CAIXA_PACOTE = 1
    ROLO_PRISMA = 2
    ENVELOPE = 3


class CorreiosWSServerTimeoutException(Timeout):
    """ Classe para exceções de Timeout de conexão com os Correios """
    pass

class CorreiosWSServerErrorException(Exception):
    """ Classe para exceções de status diferentes de HTTP 200 recebidos do servidor dos Correios """

    content = ""
    http_status_code = -1

    def __init__(self, http_status_code, content=None):
        self.content = content
        self.http_status_code = http_status_code

    def __repr__(self, *args, **kwargs):
        return "<CorreiosWSServerErrorException: http_status_code:{0}> "\
               "content={1}".format(self.http_status_code, self.content)


class CorreiosWS(object):
    """ Classe que comunica com o WebService dos Correios """

    class CorreiosWSServiceResult(object):
        """ Classe que representa o retorno de um serviço do WS dos Correios """

        codigo = ''
        valor = Decimal()
        prazo_entrega = 0
        valor_mao_propria = Decimal()
        valor_aviso_recebimento = Decimal()
        valor_declarado = Decimal()
        entrega_domiciliar = True
        entrega_sabado = True
        erro = 0
        msg_erro = ''
        valor_sem_adicionais = Decimal()
        obs_fim = ''

        def __repr__(self, *args, **kwargs):
            return "<CorreiosWSServiceResult: codigo={0}, valor={1}, prazo_entrega={2}>, "\
                   "valor_mao_propria={3}, valor_aviso_recebimento={4}, valor_valor_declarado={5}, "\
                   "entrega_domiciliar={6}, entrega_sabado={7}, erro={8}, msg_erro={9}, "\
                   "valor_sem_adicionais={10}, obs_fim={11}>".format(self.codigo,
                                                                     self.valor,
                                                                     self.prazo_entrega,
                                                                     self.valor_mao_propria,
                                                                     self.valor_aviso_recebimento,
                                                                     self.valor_declarado,
                                                                     self.entrega_domiciliar,
                                                                     self.entrega_sabado,
                                                                     self.erro,
                                                                     self.msg_erro,
                                                                     self.valor_sem_adicionais,
                                                                     self.obs_fim)

        @classmethod
        def from_service_element(cls, servico):
            """
            Popula os atributos através dos atributos do elemento XML
            :type servico BeautifulSoup.Tag
            :param servico instancia de uma Tag do BeautifulSoup contendo o serviço (cServico)
            """
            result = cls()

            result.codigo = servico.codigo.get_text() if servico.codigo else ''
            result.valor = _convert_currency_to_decimal(servico.valor.get_text()) if servico.valor else Decimal()
            result.prazo_entrega = _convert_to_int(servico.prazoentrega.get_text()) if servico.prazoentrega else 0

            result.valor_mao_propria = _convert_currency_to_decimal(servico.valormaopropria.get_text()) if servico.valormaopropria else Decimal()
            result.valor_aviso_recebimento = _convert_currency_to_decimal(servico.valoravisorecebimento.get_text()) if servico.valoravisorecebimento else Decimal()
            result.valor_declarado = _convert_currency_to_decimal(servico.valordeclarado.get_text()) if servico.valordeclarado else Decimal()
            result.entrega_domiciliar = _convert_to_bool(servico.entregadomiciliar.get_text()) if servico.entregadomiciliar else False
            result.entrega_sabado = _convert_to_bool(servico.entregasabado.get_text()) if servico.entregasabado else False

            result.erro = _convert_to_int(servico.erro.get_text()) if servico.erro else 0
            result.msg_erro = servico.msgerro.get_text() if servico.msgerro else ''

            result.valor_sem_adicionais = _convert_currency_to_decimal(servico.valorsemadicionais.get_text()) if servico.valorsemadicionais else Decimal()
            result.obs_fim = servico.obsfim.get_text() if servico.obsfim else ''
            return result

    @classmethod
    def get_preco_prazo(cls,
                        cep_destino,
                        cep_origem,
                        cod_servico,
                        package,
                        cod_empresa=None,
                        senha=None,
                        mao_propria=False,
                        valor_declarado=0.0,
                        aviso_recebimento=False):
        """
        Calcula o preço e prazo da encomenda através do webservice dos Correios.

        :type cep_destino: string
        :param cep_destino:
            CEP de destino no formato "12345678"
        :type cep_origem: string
        :param cep_destino:
            CEP de origem no formato "12345678"
        :type cod_servico: shoop_correios.base.CorreiosServico
        :param cod_servico:
            Código do serviço dos Correios a se obter o valor e prazo
        :type package: shoop_correios.packing.AbstractPackage
        :param package: informações do pacote a ser eviado
        :type cod_empresa: string
        :param cod_empresa:
            Código da empresa
        :type senha: string
        :param senha:
            Senha
        :type mao_propria: bool
        :param mao_propria:
            Indica se deve utilizar o serviço de Mão Própria
        :type valor_declarado: decimal.Decimal
        :param valor_declarado:
            Indica o valor para o serviço de Valor Declarado
        :type aviso_recebimento: bool
        :param aviso_recebimento:
            Indica se deve utilizar o serviço de Aviso de Recebimento
        :return: Resultado do serviço dos correios
        :rtype: shoop_correios.correios.CorreiosWS.CorreiosWSServiceResult
        """

        payload = {
            "nCdEmpresa": cod_empresa or '',
            "sDsSenha": senha or '',
            "nCdServico": cod_servico,
            "sCepOrigem": cep_origem or '',
            "sCepDestino": cep_destino or '',
            "nVlPeso": package.weight / Decimal(1000.0),
            "nCdFormato": CorreiosFormatoEncomenda.CAIXA_PACOTE,
            "nVlComprimento": package.length / Decimal(10.0),
            "nVlAltura": package.height / Decimal(10.0),
            "nVlLargura": package.width / Decimal(10.0),
            "nVlDiametro": 0,
            "sCdMaoPropria": 'S' if mao_propria else 'N',
            "nVlValorDeclarado": valor_declarado or 0.0,
            "sCdAvisoRecebimento": 'S' if aviso_recebimento else 'N',
            "strRetorno": 'xml'
        }

        try:
            response = requests.post(CORREIOS_WS_PRECO_PRAZO_URL,
                                     params=payload,
                                     timeout=settings.CORREIOS_WEBSERVICE_TIMEOUT)

            if response.status_code == 200:
                # deixa a coisa mais 'fácil' para se obter os valores
                bs = BeautifulSoup(response.text)

                if bs.Servicos:
                    # obtém o primeiro serviço - só requisitamos um mesmo...
                    servico = bs.servicos.find_all('cservico')[0]
                else:
                    servico = bs.cservico

                return CorreiosWS.CorreiosWSServiceResult.from_service_element(servico)

            else:
                logger.error("Erro do servidor de WS dos Correios.")
                raise CorreiosWSServerErrorException(response.status_code, response.text)

        except Timeout:
            logger.exception("Timeout de conexão com o WS dos Correios.")
            raise CorreiosWSServerTimeoutException()

## Utils
def _convert_to_int(value):
    """
    Converte um valor em int
    """
    try:
        return int(value)
    except:
        return 0

def _convert_currency_to_decimal(currency):
    """
    Converte um valor de texto em moeda nacional em Decimal
    O valor deve ser uma string e o valor deve possuir o separador
    de decimais com virgula, ex: 5.123,49
    """
    try:
        return Decimal(currency.replace('.', '').replace(',', '.') or 0.0)
    except:
        return Decimal()

def _convert_to_bool(value):
    """ Converte valores `S` e `N` para True e False, respectivamente """
    try:
        if value and value.upper() == 'S':
            return True
    except:
        pass
    return False