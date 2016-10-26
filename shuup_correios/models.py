# -*- coding: utf-8 -*-
# This file is part of Shuup Correios.
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

import logging
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from shuup.core.fields import MeasurementField
from shuup.core.models._service_base import (ServiceBehaviorComponent,
                                             ServiceChoice, ServiceCost)
from shuup.core.models._service_shipping import Carrier
from shuup.utils.dates import DurationRange
from shuup.utils.importing import cached_load
from shuup_correios.correios import (CorreiosServico, CorreiosWS,
                                     CorreiosWSServerTimeoutException)
from shuup_order_packager.constraints import (SimplePackageDimensionConstraint,
                                              WeightPackageConstraint)

logger = logging.getLogger(__name__)
KG_TO_G = Decimal(1000)


class CorreiosCarrier(Carrier):
    CORREIOS_SERVICES_MAP = {
        'PAC': CorreiosServico.PAC,
        'SEDEX': CorreiosServico.SEDEX,
        'SEDEX_10': CorreiosServico.SEDEX_10,
        'SEDEX_A_COBRAR': CorreiosServico.SEDEX_A_COBRAR,
        'SEDEX_HOJE': CorreiosServico.SEDEX_HOJE,
        'ESEDEX': CorreiosServico.ESEDEX
    }

    class Meta:
        verbose_name = _("Correios")
        verbose_name_plural = _("Correios")

    def create_service(self, choice_identifier, **kwargs):
        service = super(CorreiosCarrier, self).create_service(choice_identifier, **kwargs)
        service_code = CorreiosCarrier.CORREIOS_SERVICES_MAP.get(choice_identifier)

        if service_code:
            service.behavior_components.add(CorreiosBehaviorComponent.objects.create(cod_servico=service_code))

        service.save()
        return service

    def get_service_choices(self):
        return [
            ServiceChoice('PAC', _('PAC')),
            ServiceChoice('SEDEX', _('Sedex')),
            ServiceChoice('SEDEX_10', _('Sedex 10')),
            ServiceChoice('SEDEX_A_COBRAR', _('Sedex a cobrar')),
            ServiceChoice('SEDEX_HOJE', _('Sedex Hoje')),
            ServiceChoice('ESEDEX', _('eSedex')),
        ]


class CorreiosBehaviorComponent(ServiceBehaviorComponent):
    CORREIOS_SERVICOS_CHOICES = (
        (CorreiosServico.PAC, '({0}) PAC'.format(CorreiosServico.PAC)),
        (CorreiosServico.SEDEX, '({0}) Sedex'.format(CorreiosServico.SEDEX)),
        (CorreiosServico.SEDEX_10, '({0}) Sedex 10'.format(CorreiosServico.SEDEX_10)),
        (CorreiosServico.SEDEX_A_COBRAR, '({0}) Sedex a cobrar'.format(CorreiosServico.SEDEX_A_COBRAR)),
        (CorreiosServico.SEDEX_HOJE, '({0}) Sedex Hoje'.format(CorreiosServico.SEDEX_HOJE)),
        (CorreiosServico.ESEDEX, '({0}) eSedex'.format(CorreiosServico.ESEDEX)),
    )

    name = _("Serviço dos Correios")
    help_text = _("Configurações do serviço")

    cod_servico = models.CharField("Código do serviço",
                                   max_length=10,
                                   help_text="Código atribuído automaticamente ao criar o serviço.",
                                   choices=CORREIOS_SERVICOS_CHOICES)

    cod_servico_contrato = models.CharField("Código do serviço em contrato",
                                            null=True, blank=True, max_length=10,
                                            help_text="Informe o código do serviço em contrato, se existir. "
                                                      "Quando há um contrato com os Correios, "
                                                      "é necessário informar este código para que "
                                                      "ele seja utilizado no cálculo dos preços e prazos.")

    cep_origem = models.CharField("CEP de origem",
                                  max_length=8, default='99999999',
                                  help_text="CEP de origem da encomenda. Apenas números, sem hífen.")

    cod_empresa = models.CharField("Código da empresa",
                                   max_length=30, blank=True, null=True,
                                   help_text="Seu código administrativo junto à ECT, se existir. "
                                             "O código está disponível no corpo do "
                                             "contrato firmado com os Correios.")

    senha = models.CharField("Senha",
                             max_length=30, blank=True, null=True,
                             help_text="Senha para acesso ao serviço, associada ao seu "
                                       "código administrativo, se existir. "
                                       "A senha inicial corresponde aos 8 primeiros dígitos "
                                       "do CNPJ informado no contrato.")

    mao_propria = models.BooleanField("Mão própria?",
                                      default=False,
                                      help_text="Indica se a encomenda será entregue "
                                                "com o serviço adicional mão própria.")

    valor_declarado = models.BooleanField("Valor declarado?",
                                          default=False,
                                          help_text="Indica se a encomenda será entregue "
                                                    "com o serviço adicional valor declarado.")

    aviso_recebimento = models.BooleanField("Aviso de recebimento?",
                                            default=False,
                                            help_text="Indica se a encomenda será entregue "
                                                      "com o serviço adicional aviso de recebimento.")

    additional_delivery_time = models.PositiveIntegerField("Prazo adicional",
                                                           blank=True,
                                                           default=0,
                                                           validators=[MinValueValidator(0)],
                                                           help_text="Indica quantos dias devem ser somados "
                                                                     "ao prazo original retornado pelo serviço dos Correios. "
                                                                     "O prazo será somado no prazo de cada encomenda diferente.")

    additional_price = models.DecimalField("Preço adicional",
                                           blank=True,
                                           max_digits=9, decimal_places=2, default=Decimal(),
                                           validators=[MinValueValidator(Decimal(0))],
                                           help_text="Indica o valor, em reais, a ser somado "
                                                     "ao preço original retornado pelo serviço dos Correios. "
                                                     "O preço será somado no valor de cada encomenda diferente.")

    max_weight = MeasurementField(verbose_name="Peso máximo da embalagem (kg)",
                                  unit="kg",
                                  blank=True,
                                  validators=[MinValueValidator(Decimal(0))],
                                  default=Decimal(),
                                  help_text="Indica o peso máximo admitido para esta modalidade.")

    min_length = MeasurementField(verbose_name="Comprimento mínimo (mm)",
                                  unit="mm",
                                  default=110,
                                  validators=[MinValueValidator(Decimal(0))],
                                  help_text="Indica o comprimento mínimo "
                                            "para caixas e pacotes.")

    max_length = MeasurementField(verbose_name="Comprimento máximo (mm)",
                                  unit="mm",
                                  default=1050,
                                  validators=[MinValueValidator(Decimal(0))],
                                  help_text="Indica o comprimento máximo "
                                            "para caixas e pacotes.")

    min_width = MeasurementField(verbose_name="Largura mínima (mm)",
                                 unit="mm",
                                 default=160,
                                 validators=[MinValueValidator(Decimal(0))],
                                 help_text="Indica a largura mínima "
                                           "para caixas e pacotes.")

    max_width = MeasurementField(verbose_name="Largura máxima",
                                 unit="mm",
                                 default=1050,
                                 validators=[MinValueValidator(Decimal(0))],
                                 help_text="Indica a largura máxima "
                                           "para caixas e pacotes.")

    min_height = MeasurementField(verbose_name="Altura mínima (mm)",
                                  unit="mm",
                                  default=20,
                                  validators=[MinValueValidator(Decimal(0))],
                                  help_text="Indica a altura mínima "
                                            "para caixas e pacotes.")

    max_height = MeasurementField(verbose_name="Altura máxima (mm)",
                                  unit="mm",
                                  default=1050,
                                  validators=[MinValueValidator(Decimal(0))],
                                  help_text="Indica a altura máxima "
                                            "para caixas e pacotes.")

    max_edges_sum = MeasurementField(verbose_name="Soma máxima das dimensões (L + A + C) (mm)",
                                     unit="mm",
                                     default=2000,
                                     validators=[MinValueValidator(Decimal(0))],
                                     help_text="Indica a soma máxima das dimensões de "
                                               "altura + largura + comprimento "
                                               "para caixas e pacotes.")

    def get_unavailability_reasons(self, service, source):
        """
        :type service: Service
        :type source: shuup.core.order_creator.OrderSource
        :rtype: Iterable[ValidationError]
        """

        errors = []
        packages = self._pack_source(source)

        if packages:
            try:
                results = self._get_correios_results(source, packages)

                if results:
                    for result in results:
                        if result.erro != 0:
                            logger.warn("{0}: {1}".format(result.erro, result.msg_erro))
                            errors.append(ValidationError("Alguns itens não poderão ser "
                                                          "entregues pelos Correios.", code=result.erro))
            except CorreiosWSServerTimeoutException:
                errors.append(ValidationError("Não foi possível contatar os serviços dos Correios."))

        else:
            errors.append(ValidationError("Alguns itens não puderam ser empacotados nos requisitos dos Correios."))

        return errors

    def get_costs(self, service, source):
        """
        Return costs for for this object. This should be implemented
        in subclass. This method is used to calculate price for
        ``ShippingMethod`` and ``PaymentMethod`` objects.

        :type service: Service
        :type source: shuup.core.order_creator.OrderSource
        :rtype: Iterable[ServiceCost]
        """
        packages = self._pack_source(source)

        try:
            results = self._get_correios_results(source, packages)
            total_price = Decimal()

            for result in results:
                if result.erro == 0:
                    total_price = total_price + result.valor
                else:
                    total_price = 0
                    logger.critical("CorreiosWS: Erro {0} ao calcular "
                                    "preço e prazo para {2}: {1}".format(result.erro,
                                                                         result.msg_erro,
                                                                         source))
                    break

            if total_price > 0:
                yield ServiceCost(source.create_price(total_price + self.additional_price))

        except CorreiosWSServerTimeoutException:
            pass

    def get_delivery_time(self, service, source):
        """
        :type service: Service
        :type source: shuup.core.order_creator.OrderSource
        :rtype: shuup.utils.dates.DurationRange|None
        """

        packages = self._pack_source(source)

        try:
            results = self._get_correios_results(source, packages)
        except CorreiosWSServerTimeoutException:
            return None

        max_days = 1
        min_days = 0

        for result in results:
            if result.erro == 0:
                max_days = max(max_days, result.prazo_entrega)
                min_days = result.prazo_entrega if not min_days else min(min_days, result.prazo_entrega)

            else:
                logger.critical("CorreiosWS: Erro {0} ao calcular "
                                "preço e prazo para {2}: {1}".format(result.erro,
                                                                     result.msg_erro,
                                                                     source))
                return None

        return DurationRange.from_days(min_days + self.additional_delivery_time,
                                       max_days + self.additional_delivery_time)

    def _pack_source(self, source):
        """
        Empacota itens do pedido
        :rtype: Iterable[shuup_order_packager.package.AbstractPackage|None]
        :return: Lista de pacotes ou None se for impossível empacotar pedido
        """
        packager = cached_load("CORREIOS_PRODUCTS_PACKAGER_CLASS")()
        packager.add_constraint(SimplePackageDimensionConstraint(self.max_width,
                                                                 self.max_length,
                                                                 self.max_height,
                                                                 self.max_edges_sum))

        packager.add_constraint(WeightPackageConstraint(self.max_weight * KG_TO_G))
        return packager.pack_source(source)

    def _get_correios_results(self, source, packages):
        """
        Obtém uma lista dos resultados obtidos dos correios para determinado pedido
        :type source: shuup.core.order_creator.OrderSource
        :rtype: list of shuup_correios.correios.CorreiosWS.CorreiosWSServiceResult
        """
        results = []

        cep_origem = "".join([d for d in self.cep_origem if d.isdigit()])
        pedido_total = source.total_price_of_products.value
        shipping_address = source.shipping_address

        if not shipping_address:
            shipping_address = source.billing_address

        if not shipping_address:
            return []

        cep_destino = "".join([d for d in shipping_address.postal_code if d.isdigit()])

        for package in packages:
            results.append(CorreiosWS.get_preco_prazo(cep_destino,
                                                      cep_origem,
                                                      self.cod_servico_contrato if self.cod_servico_contrato else self.cod_servico,
                                                      package,
                                                      self.cod_empresa,
                                                      self.senha,
                                                      self.mao_propria,
                                                      pedido_total if self.valor_declarado else 0.0,
                                                      self.aviso_recebimento,
                                                      self.min_width,
                                                      self.min_length,
                                                      self.min_height))

        return results
