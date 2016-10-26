# -*- coding: utf-8 -*-
# This file is part of Shuup Correios.
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import hashlib
import logging
from decimal import Decimal

import requests
import xmltodict
from django.conf import settings
from django.core.cache import caches
from django.utils.encoding import force_bytes, force_text
from requests.exceptions import Timeout

logger = logging.getLogger(__name__)

# URL de acesso ao cálculo de preço e prazo
CORREIOS_WS_PRECO_PRAZO_URL = "http://ws.correios.com.br/calculador/CalcPrecoPrazo.aspx"

# cache
correios_cache = caches[settings.CORREIOS_CACHE_NAME]


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
        def from_service(cls, servico):
            """
            Popula os atributos através dos atributos do elemento XML
            :type servico BeautifulSoup.Tag
            :param servico instancia de uma Tag do BeautifulSoup contendo o serviço (cServico)
            """
            result = cls()

            result.codigo = servico["Codigo"]
            result.valor = _convert_currency_to_decimal(servico.get('Valor'))
            result.prazo_entrega = _convert_to_int(servico.get('PrazoEntrega'))

            result.valor_mao_propria = _convert_currency_to_decimal(servico.get('ValorMaoPropria'))
            result.valor_aviso_recebimento = _convert_currency_to_decimal(servico.get('ValorAvisoRecebimento'))
            result.valor_declarado = _convert_currency_to_decimal(servico.get('ValorValorDeclarado'))
            result.entrega_domiciliar = _convert_to_bool(servico.get('EntregaDomiciliar'))
            result.entrega_sabado = _convert_to_bool(servico.get('EntregaSabado'))

            result.erro = _convert_to_int(servico.get('Erro', 0))
            result.msg_erro = servico.get('MsgErro', '') or ''

            result.valor_sem_adicionais = _convert_currency_to_decimal(servico.get('ValorSemAdicionais', ''))
            result.obs_fim = servico.get('obsFim', '') or ''
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
                        aviso_recebimento=False,
                        min_package_width=Decimal(),
                        min_package_length=Decimal(),
                        min_package_height=Decimal()):
        """
        Calcula o preço e prazo da encomenda através do webservice dos Correios.

        :type cep_destino: string
        :param cep_destino:
            CEP de destino no formato "12345678"
        :type cep_origem: string
        :param cep_destino:
            CEP de origem no formato "12345678"
        :type cod_servico: shuup_correios.base.CorreiosServico
        :param cod_servico:
            Código do serviço dos Correios a se obter o valor e prazo
        :type package: shuup_correios.packing.AbstractPackage
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
        :rtype: shuup_correios.correios.CorreiosWS.CorreiosWSServiceResult

        :param: min_package_width Largura mínima do pacote (mm)
        :param: min_package_length Comprimento mínimo do pacote (mm)
        :param: min_package_height Altura mínima do pacote (mm)
        """

        package_width = max(package.width, min_package_width)
        package_length = max(package.length, min_package_length)
        package_height = max(package.height, min_package_height)

        # VERIFICA SE A REQUISIÇÃO ESTÁ NO CACHE

        # cria uma tupla de parâmetros para criar um chave única para
        # identificar o pacote no cache
        params = (cep_destino, cep_origem, cod_servico, cod_empresa, senha,
                  mao_propria, valor_declarado, aviso_recebimento,
                  package.weight, package_width, package_length, package_height)
        # gera a chave do cache
        cache_key = force_text(hashlib.md5(force_bytes(params)).hexdigest())

        cached_result = correios_cache.get(cache_key)
        if cached_result:
            logger.debug("Correios: Using cached value")
            return cached_result

        payload = {
            "nCdEmpresa": cod_empresa or '',
            "sDsSenha": senha or '',
            "nCdServico": cod_servico,
            "sCepOrigem": cep_origem or '',
            "sCepDestino": cep_destino or '',
            "nVlPeso": package.weight * Decimal(0.001),
            "nCdFormato": CorreiosFormatoEncomenda.CAIXA_PACOTE,
            "nVlComprimento": package_length * Decimal(0.1),
            "nVlAltura": package_height * Decimal(0.1),
            "nVlLargura": package_width * Decimal(0.1),
            "nVlDiametro": 0,
            "sCdMaoPropria": 'S' if mao_propria else 'N',
            "nVlValorDeclarado": valor_declarado or 0.0,
            "sCdAvisoRecebimento": 'S' if aviso_recebimento else 'N',
            "strRetorno": 'xml'
        }

        logger.debug("Correios: Making request")

        try:
            response = requests.post(CORREIOS_WS_PRECO_PRAZO_URL,
                                     params=payload,
                                     timeout=settings.CORREIOS_WEBSERVICE_TIMEOUT)

            if response.status_code == 200:
                # deixa a coisa mais 'fácil' para se obter os valores
                result = xmltodict.parse(response.text)

                is_list = isinstance(result["Servicos"]["cServico"], list)

                if is_list:
                    # obtém o primeiro serviço - só requisitamos um mesmo...
                    servico = result["Servicos"]["cServico"][0]
                else:
                    servico = result["Servicos"]["cServico"]

                result = CorreiosWS.CorreiosWSServiceResult.from_service(servico)

                if result.erro == 0:
                    # sem erros, salva no cache
                    correios_cache.set(cache_key, result)

                return result

            else:
                logger.error("Erro do servidor de WS dos Correios.")
                raise CorreiosWSServerErrorException(response.status_code, response.text)

        except Timeout:
            logger.exception("Timeout de conexão com o WS dos Correios.")
            raise CorreiosWSServerTimeoutException()


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
