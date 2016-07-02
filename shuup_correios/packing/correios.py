# -*- coding: utf-8 -*-
# This file is part of Shuup Correios.
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals
from shuup.core.models._order_lines import OrderLineType
from shuup_correios.packing.base import AbstractPackageConstraint, BasePackage,\
    AbstractPackager
from decimal import Decimal
from django.utils.log import getLogger

logger = getLogger(__name__)

class CorreiosPackageConstraint(AbstractPackageConstraint):
    """
    Constraint de pacotes dos Correios. Possui dimensões máximas e mínimas.
    Dimensões em milímetros. Peso em gramas.
    """
    max_width = Decimal()
    max_length = Decimal()
    max_height = Decimal()
    max_weight = Decimal()
    max_edges_sum = Decimal()

    min_width = Decimal()
    min_length = Decimal()
    min_height = Decimal()

    def __init__(self,
                 max_width,
                 max_length,
                 max_height,
                 max_weight,
                 max_edges_sum,
                 min_width,
                 min_length,
                 min_height):

        # ordena as dimensões da constraint
        constraint_sizes = [max_width, max_length, max_height]
        constraint_sizes.sort(reverse=True)
        max_width, max_length, max_height = constraint_sizes

        self.max_width = Decimal(max_width)
        self.max_length = Decimal(max_length)
        self.max_height = Decimal(max_height)
        self.max_weight = Decimal(max_weight)
        self.min_width = Decimal(min_width)
        self.min_length = Decimal(min_length)
        self.min_height = Decimal(min_height)

        # soma das arestas não pode ser menor que o tamanho mínimo
        if max_edges_sum < (min_width + min_length + min_height):
            self.max_edges_sum = (min_width + min_length + min_height)
        else:
            self.max_edges_sum = Decimal(max_edges_sum)


class CorreiosPackage(BasePackage):
    """
    Implementação do pacote simples do Correio.

    O pacote sempre terá as dimensões ordenadas em: largura, comprimento e altura
    Todo e qualquer item será colocado na caixa nessa ordem:
        * itens mais largos
        * itens mais compridos
        * items mais altos

    O tamanho do pacote terá a largura e comprimento do maior
    produto que está dentro da caixa.
    A altura será a soma da altura de todos os itens.
    """

    def add_product(self, product):
        if not self._product_has_valid_attrs(product):
            return

        width, length, height = _get_product_dimensions(product)

        # soma o peso e a altura
        self._weight = self._weight + product.gross_weight
        self._height = self._height + height

        # faz a bounding box atribuindo sempre a largura e comprimento do pacote
        # com as dimensões do maior item
        self._width = max(self._width, width)
        self._length = max(self._length, length)

        super(CorreiosPackage, self).add_product(product)

    def product_fits(self, product):

        if not self._product_has_valid_attrs(product):
            return False

        # se a constraint for da classe CorreiosPackageConstraint valida o tamanho máx/min
        if self._constraint and isinstance(self._constraint, CorreiosPackageConstraint):

            width, length, height = _get_product_dimensions(product)

            # não pode ultrapassar a largura máxima
            if max(self._width, width) > self._constraint.max_width:
                return False

            # não pode ultrapassar a profundidade máxima
            elif max(self._length, length) > self._constraint.max_length:
                return False

            # não pode ultrapassar a altura máxima
            elif self._height + height > self._constraint.max_height:
                return False

            # não pode ultrapassar o peso máximo
            elif self._constraint.max_weight and self._weight + product.gross_weight > self._constraint.max_weight:
                return False

            # soma das arestas da caixa contendo o produto não pode ultrapassar a constraint
            elif self._constraint.max_edges_sum and (self._width + self._length + self._height + height) > self._constraint.max_edges_sum:
                return False

            return True

        else:
            return super(CorreiosPackage, self).product_fits(product)

    def _product_has_valid_attrs(self, product):
        """
        Valida se o produto possui atributos válidos.
        :rtype: bool
        :return: se o produto está apto a ser adicionado em alguma caixa
        """

        # valida se o produto está bem configurado
        if not product.width or not product.depth or not product.height or not product.gross_weight:
            logger.warn("CorreiosPackage: Produto {0} (id={1}) mal configurado. "
                        "Configure corretamente as dimensoes e peso do produto.", product, product.id)
            return False
        return True

    @property
    def volume(self):
        return self.width * self.length * self.height

    @property
    def cubic_weight(self):
        """
        Os Correios utilizam o coeficiente de 6.000 cm3/kg
        http://www.correios.com.br/para-sua-empresa/comercio-eletronico/como-calcular-precos-e-prazos-de-entrega-em-sua-loja-on-line
        """
        # divide por 600 pois volume está em milímetros
        return self.volume / Decimal(600.0)

    @property
    def width(self):
        # se há configurado uma constraint, vamos retornar sempre
        # o tamanho mínimo da constraint se o tamanho da caixa for menor
        if self._constraint and isinstance(self._constraint, CorreiosPackageConstraint):
            return max(self._width, self._constraint.min_width)

        return self._width

    @property
    def height(self):
        # se há configurado uma constraint, vamos retornar sempre
        # o tamanho mínimo da constraint se o tamanho da caixa for menor
        if self._constraint and isinstance(self._constraint, CorreiosPackageConstraint):
            return max(self._height, self._constraint.min_height)

        return self._height

    @property
    def length(self):
        # se há configurado uma constraint, vamos retornar sempre
        # o tamanho mínimo da constraint se o tamanho da caixa for menor
        if self._constraint and isinstance(self._constraint, CorreiosPackageConstraint):
            return max(self._length, self._constraint.min_length)

        return self._length


class CorreiosSimplePackager(AbstractPackager):
    _pkge_constraint = None

    def set_package_constraint(self, package_constraint):
        self._pkge_constraint = package_constraint

    def new_package(self):
        """ Cria e retorna um pacote do Correio """
        return CorreiosPackage(self._pkge_constraint)

    def pack_products(self, source):
        """
        Calcula os atributos dos produtos e cria pacotes
        contendo o peso e tamanho das embalagens finais.

        Se o tamanho ou peso ultrapassar os limites
        estabelecidos pelos Correios, uma nova
        encomenda será criada.

        Atualmente o algoritmo vai somando a altura dos produtos
        até chegar a uma altura limite. Quando chegar na altura limite
        o pacote é fechado e outro é criado.

        :param: source: cesta de itens a ser utilizada para empacotar os itens
        :type source: shuup.core.order_creator.OrderSource
        :rtype: Iterable[shuup_correios.packing.CorreiosPackage|None]
        :return: Lista de pacotes ou None se for impossível
        """

        packages = []
        expanded_products = []

        # expande os itens do pedido, para que cada produto
        # seja colocado separadamente na caixa

        # TODO: verificar se quantidades são fracionadas?

        for line in source.get_lines():
            if line.type == OrderLineType.PRODUCT:
                expanded_products.extend([line.product] * line.quantity)

        # GAMBI: coloca num dicionário para poder acessar
        # no escopo da função interna close_package
        current_package = {'default': self.new_package()}

        def close_package():
            """ Se o pacote possui itens, fecha e cria um novo """
            if current_package['default'].count > 0:
                packages.append(current_package['default'])
            current_package['default'] = self.new_package()

        for product in expanded_products:
            # opa, produto não serviu! vamos testar com um pacote vazio
            if not current_package['default'].product_fits(product):

                # cria um pacote temporario e testa se ele serve em um vazio
                if self.new_package().product_fits(product):
                    # ok, então fecha esse e cria um novo
                    close_package()

                else:
                    # Impossível acondicionar o produto em um pacote vazio
                    # não podemos efetuar a entrega com o um todo
                    return None

            current_package['default'].add_product(product)

        close_package()
        return packages


def _get_product_dimensions(product):
    """
    :type: product: shuup.core.models.Product
    """

    height = product.height
    width = product.width
    length = product.depth

    # obtém as dimensões e ordena
    # assim teremos a largura como a maior dimensão
    # precedida do comprimento..
    # a altura será a menor dimensão
    sizes = [width, length, height]
    sizes.sort(reverse=True)
    width, length, height = sizes

    return width, length, height
