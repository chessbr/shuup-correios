# -*- coding: utf-8 -*-
# This file is part of Shuup Correios.
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.


from shuup_correios.packing import BasePackage
from shuup_correios.packing.correios import CorreiosPackage,\
    _get_product_dimensions, CorreiosPackageConstraint, CorreiosSimplePackager

from shuup.testing.factories import create_product, get_default_supplier
from shuup_tests.core.test_order_creator import seed_source
from shuup.core.models._order_lines import OrderLineType
import pytest
from decimal import Decimal

def test_base_package():
    base_pkge = BasePackage()
    assert base_pkge.width == 0
    assert base_pkge.height == 0
    assert base_pkge.length == 0
    assert base_pkge.weight == 0

    repr(base_pkge)

@pytest.mark.django_db
def test_correios_package_no_constraint():
    product1 = create_product(sku='p1', width=100, depth=200, height=50, gross_weight=2340)

    p1_width, p1_length, p1_height = _get_product_dimensions(product1)

    pkge = CorreiosPackage()
    repr(pkge)
    assert pkge.count == 0
    assert pkge.volume == 0

    # adiciona o produto uma vez
    pkge.add_product(product1)
    assert pkge.width == p1_width
    assert pkge.height == p1_height
    assert pkge.length == p1_length
    assert pkge.weight == product1.gross_weight
    assert pkge.count == 1
    assert pkge.volume == (p1_width * p1_length * p1_height)

    # adiciona o produto outra vez
    pkge.add_product(product1)
    assert pkge.width == p1_width
    assert pkge.length == p1_length
    assert pkge.height == p1_height * 2
    assert pkge.weight == product1.gross_weight * 2
    assert pkge.count == 2
    assert pkge.volume == (p1_width * p1_length * (p1_height * 2))

    repr(pkge)

    # cria um produto novo
    product2 = create_product(sku='p2', width=168, depth=365, height=50, gross_weight=1204)
    p2_width, p2_length, p2_height = _get_product_dimensions(product2)

    # adiciona o novo
    pkge.add_product(product2)
    assert pkge.width == max(p1_width, p2_width)
    assert pkge.length == max(p1_length, p2_length)
    assert pkge.height == p1_height * 2 + p2_height
    assert pkge.weight == product1.gross_weight * 2 + product2.gross_weight
    assert pkge.count == 3
    assert pkge.volume == max(p1_width, p2_width) * max(p1_length, p2_length) * (p1_height * 2 + p2_height)


@pytest.mark.django_db
def test_correios_package_with_constraint_max_size_1():
    MAX_WIDTH = 450
    MAX_LENGTH = 200
    MAX_HEIGHT = 100
    MAX_WEIGHT = 32000
    MAX_EDGES_SUM = 2100
    MIN_WIDTH = 120
    MIN_LENGTH = 150
    MIN_HEIGHT = 80

    constraint = CorreiosPackageConstraint(MAX_WIDTH,
                                           MAX_LENGTH,
                                           MAX_HEIGHT,
                                           MAX_WEIGHT,
                                           MAX_EDGES_SUM,
                                           MIN_WIDTH,
                                           MIN_LENGTH,
                                           MIN_HEIGHT)
    assert constraint.max_width == MAX_WIDTH
    assert constraint.max_length == MAX_LENGTH
    assert constraint.max_height == MAX_HEIGHT
    assert constraint.max_weight == MAX_WEIGHT
    assert constraint.max_edges_sum == MAX_EDGES_SUM
    assert constraint.min_width == MIN_WIDTH
    assert constraint.min_length == MIN_LENGTH
    assert constraint.min_height == MIN_HEIGHT

    pkge = CorreiosPackage(constraint)

    # testa o tamanho minimo - mesmo que não exista nada na caixa
    assert pkge.width == MIN_WIDTH
    assert pkge.length == MIN_LENGTH
    assert pkge.height == MIN_HEIGHT

    # @test: produto com largura maior
    product = create_product(sku='p1', width=500, depth=200, height=100, gross_weight=MAX_WEIGHT)
    assert pkge.product_fits(product) == False

    # @test: produto com largura maior
    product = create_product(sku='p2', width=100, depth=300, height=460, gross_weight=MAX_WEIGHT)
    assert pkge.product_fits(product) == False

    # @test: produto com largura igual, comprimento maior
    product = create_product(sku='p3', width=450, depth=210, height=100, gross_weight=MAX_WEIGHT)
    assert pkge.product_fits(product) == False

    # @test: produto com largura igual, comprimento igual, altura maior
    product = create_product(sku='p4', width=450, depth=200, height=110, gross_weight=MAX_WEIGHT)
    assert pkge.product_fits(product) == False

    # @test: produto com largura perfeita
    product = create_product(sku='p5', width=450, depth=200, height=100, gross_weight=MAX_WEIGHT)
    assert pkge.product_fits(product) == True

    # @test: produto com largura menor
    product = create_product(sku='p6', width=300, depth=200, height=100, gross_weight=MAX_WEIGHT)
    assert pkge.product_fits(product) == True

    # @test: produto com largura menor
    product = create_product(sku='p7', width=100, depth=200, height=400, gross_weight=MAX_WEIGHT)
    assert pkge.product_fits(product) == True

    # @test: produto com tamanho maior
    product = create_product(sku='p8', width=500, depth=500, height=500, gross_weight=MAX_WEIGHT)
    assert pkge.product_fits(product) == False

    # testa __repr__
    repr(pkge)


@pytest.mark.django_db
def test_correios_package_with_constraint_max_size_2():
    MAX_WIDTH = 450
    MAX_LENGTH = 700
    MAX_HEIGHT = 610
    MAX_WEIGHT = 32000
    MAX_EDGES_SUM = MAX_WIDTH + MAX_LENGTH + MAX_HEIGHT
    MIN_WIDTH = 120
    MIN_LENGTH = 150
    MIN_HEIGHT = 80

    constraint = CorreiosPackageConstraint(MAX_WIDTH,
                                           MAX_LENGTH,
                                           MAX_HEIGHT,
                                           MAX_WEIGHT,
                                           MAX_EDGES_SUM,
                                           MIN_WIDTH,
                                           MIN_LENGTH,
                                           MIN_HEIGHT)

    assert constraint.max_width == MAX_LENGTH
    assert constraint.max_length == MAX_HEIGHT
    assert constraint.max_height == MAX_WIDTH
    assert constraint.max_weight == MAX_WEIGHT
    assert constraint.max_edges_sum == MAX_EDGES_SUM
    assert constraint.min_width == MIN_WIDTH
    assert constraint.min_length == MIN_LENGTH
    assert constraint.min_height == MIN_HEIGHT

    pkge = CorreiosPackage(constraint)

    # testa o tamanho minimo - mesmo que não exista nada na caixa
    assert pkge.width == MIN_WIDTH
    assert pkge.length == MIN_LENGTH
    assert pkge.height == MIN_HEIGHT

    p1 = create_product(sku='p1', width=500, depth=200, height=400, gross_weight=5000)
    assert pkge.product_fits(p1) == True
    pkge.add_product(p1)

    # produto 2 - mesma largura e comprimento, mas mais alto
    p2 = create_product(sku='p2', width=500, depth=250, height=400, gross_weight=5000)
    assert pkge.product_fits(p2) == True
    pkge.add_product(p2)

    # produto 3 - mesma largura e comprimento, mas a altura é um palito e não serve, já fechou a altura maxima
    p3 = create_product(sku='p3', width=500, depth=10, height=400, gross_weight=5000)
    assert pkge.product_fits(p3) == False


    # testa __repr__
    repr(pkge)


@pytest.mark.django_db
def test_correios_package_with_constraint_min_size():
    MAX_WIDTH = 450
    MAX_LENGTH = 700
    MAX_HEIGHT = 610
    MAX_WEIGHT = 32000
    MAX_EDGES_SUM = MAX_WIDTH + MAX_LENGTH + MAX_HEIGHT
    MIN_WIDTH = 120
    MIN_LENGTH = 150
    MIN_HEIGHT = 80

    constraint = CorreiosPackageConstraint(MAX_WIDTH,
                                           MAX_LENGTH,
                                           MAX_HEIGHT,
                                           MAX_WEIGHT,
                                           MAX_EDGES_SUM,
                                           MIN_WIDTH,
                                           MIN_LENGTH,
                                           MIN_HEIGHT)

    assert constraint.max_width == MAX_LENGTH
    assert constraint.max_length == MAX_HEIGHT
    assert constraint.max_height == MAX_WIDTH
    assert constraint.max_weight == MAX_WEIGHT
    assert constraint.max_edges_sum == MAX_EDGES_SUM
    assert constraint.min_width == MIN_WIDTH
    assert constraint.min_length == MIN_LENGTH
    assert constraint.min_height == MIN_HEIGHT

    pkge = CorreiosPackage(constraint)

    # testa o tamanho minimo - mesmo que não exista nada na caixa
    assert pkge.width == MIN_WIDTH
    assert pkge.length == MIN_LENGTH
    assert pkge.height == MIN_HEIGHT

    # insere produto muito pequeno - abaixo do tamanho minimo
    p1 = create_product(sku='p1', width=10, depth=10, height=10, gross_weight=1000.0)
    assert pkge.product_fits(p1) == True
    pkge.add_product(p1)


    # testa __repr__
    repr(pkge)


@pytest.mark.django_db
def test_correios_package_with_constraint_max_weight():
    MAX_WIDTH = 450
    MAX_LENGTH = 700
    MAX_HEIGHT = 610
    MAX_WEIGHT = 32000
    MAX_EDGES_SUM = MAX_WIDTH + MAX_LENGTH + MAX_HEIGHT
    MIN_WIDTH = 120
    MIN_LENGTH = 150
    MIN_HEIGHT = 80

    constraint = CorreiosPackageConstraint(MAX_WIDTH,
                                           MAX_LENGTH,
                                           MAX_HEIGHT,
                                           MAX_WEIGHT,
                                           MAX_EDGES_SUM,
                                           MIN_WIDTH,
                                           MIN_LENGTH,
                                           MIN_HEIGHT)

    assert constraint.max_width == MAX_LENGTH
    assert constraint.max_length == MAX_HEIGHT
    assert constraint.max_height == MAX_WIDTH
    assert constraint.max_weight == MAX_WEIGHT
    assert constraint.max_edges_sum == MAX_EDGES_SUM
    assert constraint.min_width == MIN_WIDTH
    assert constraint.min_length == MIN_LENGTH
    assert constraint.min_height == MIN_HEIGHT

    pkge = CorreiosPackage(constraint)
    repr(pkge)

    # testa o tamanho minimo - mesmo que não exista nada na caixa
    assert pkge.width == MIN_WIDTH
    assert pkge.length == MIN_LENGTH
    assert pkge.height == MIN_HEIGHT

    p1 = create_product(sku='p1', width=500, depth=200, height=400, gross_weight=5000.0)
    assert pkge.product_fits(p1) == True
    pkge.add_product(p1)

    # produto 2
    p2 = create_product(sku='p2', width=10, depth=10, height=10, gross_weight=5000.0)
    assert pkge.product_fits(p2) == True
    pkge.add_product(p2)

    # produto 3 - mesma largura e comprimento, mas o peso estoura o maximo
    p3 = create_product(sku='p3', width=10, depth=10, height=10, gross_weight=50000.0)
    assert pkge.product_fits(p3) == False


    # testa __repr__
    repr(pkge)


@pytest.mark.django_db
def test_correios_package_with_constraint_max_edges_size():
    MAX_WIDTH = 500
    MAX_LENGTH = 600
    MAX_HEIGHT = 600
    MAX_WEIGHT = 32000
    MIN_WIDTH = 120
    MIN_LENGTH = 150
    MIN_HEIGHT = 80

    MAX_EDGES_SUM = MIN_WIDTH + MIN_LENGTH + MIN_HEIGHT - 1

    constraint = CorreiosPackageConstraint(MAX_WIDTH,
                                           MAX_LENGTH,
                                           MAX_HEIGHT,
                                           MAX_WEIGHT,
                                           MAX_EDGES_SUM,
                                           MIN_WIDTH,
                                           MIN_LENGTH,
                                           MIN_HEIGHT)

    assert constraint.max_width == MAX_LENGTH
    assert constraint.max_length == MAX_HEIGHT
    assert constraint.max_height == MAX_WIDTH
    assert constraint.max_weight == MAX_WEIGHT
    assert constraint.max_edges_sum == (MIN_WIDTH + MIN_LENGTH + MIN_HEIGHT)
    assert constraint.min_width == MIN_WIDTH
    assert constraint.min_length == MIN_LENGTH
    assert constraint.min_height == MIN_HEIGHT

    pkge = CorreiosPackage(constraint)


    # insere produto pequeno
    p1 = create_product(sku='p1', width=80, depth=90, height=100, gross_weight=1000.0)
    assert pkge.product_fits(p1) == True
    pkge.add_product(p1)


    # insere outro produto que serve na caixa, mas completa a constraint de
    # soma de arestas
    p2 = create_product(sku='p2', width=180, depth=90, height=80, gross_weight=1000.0)
    assert pkge.product_fits(p2) == True
    pkge.add_product(p2)


    # essa caixinha não cabe
    p3 = create_product(sku='p3', width=10, depth=10, height=10, gross_weight=1000.0)
    assert pkge.product_fits(p3) == False


    # testa __repr__
    repr(pkge)


@pytest.mark.django_db
def test_correios_package_dimensions():
    MAX_WIDTH = 450
    MAX_LENGTH = 200
    MAX_HEIGHT = 100
    MAX_WEIGHT = 32000
    MAX_EDGES_SUM = 2100
    MIN_WIDTH = 120
    MIN_LENGTH = 150
    MIN_HEIGHT = 80

    constraint = CorreiosPackageConstraint(MAX_WIDTH,
                                           MAX_LENGTH,
                                           MAX_HEIGHT,
                                           MAX_WEIGHT,
                                           MAX_EDGES_SUM,
                                           MIN_WIDTH,
                                           MIN_LENGTH,
                                           MIN_HEIGHT)

    assert constraint.max_width == MAX_WIDTH
    assert constraint.max_length == MAX_LENGTH
    assert constraint.max_height == MAX_HEIGHT
    assert constraint.max_weight == MAX_WEIGHT
    assert constraint.max_edges_sum == MAX_EDGES_SUM
    assert constraint.min_width == MIN_WIDTH
    assert constraint.min_length == MIN_LENGTH
    assert constraint.min_height == MIN_HEIGHT

    pkge = CorreiosPackage(constraint)

    p1 = create_product(sku='p1', width=10, depth=20, height=30, gross_weight=1000.0)
    assert pkge.product_fits(p1) == True
    assert pkge.width == MIN_WIDTH
    assert pkge.length == MIN_LENGTH
    assert pkge.height == MIN_HEIGHT
    pkge.add_product(p1)
    assert pkge.width == MIN_WIDTH
    assert pkge.length == MIN_LENGTH
    assert pkge.height == MIN_HEIGHT

    assert pkge.volume - Decimal(MIN_WIDTH * MIN_LENGTH * MIN_HEIGHT) < Decimal(0.0001)
    assert pkge.cubic_weight - Decimal((MIN_WIDTH * MIN_LENGTH * MIN_HEIGHT) / 600.0) < Decimal(0.00001)


    pkge = CorreiosPackage()
    assert pkge.product_fits(p1) == True
    pkge.add_product(p1)
    assert pkge.width == 30
    assert pkge.length == 20
    assert pkge.height == 10
    assert pkge.volume == 10 * 20 * 30
    assert pkge.cubic_weight - Decimal((10 * 20 * 30) / 600.0) < Decimal(0.00001)


@pytest.mark.django_db
def test_correios_packager_no_constraint(rf, admin_user):
    pkger = CorreiosSimplePackager()

    p1 = create_product(sku='p1', supplier=get_default_supplier(), width=100, depth=400, height=300, gross_weight=2000)
    p2 = create_product(sku='p2', supplier=get_default_supplier(), width=220, depth=350, height=110, gross_weight=1530)

    source = seed_source(admin_user)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=p1,
        supplier=get_default_supplier(),
        quantity=2,
        base_unit_price=source.create_price(10),
    )

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=p2,
        supplier=get_default_supplier(),
        quantity=4,
        base_unit_price=source.create_price(10),
    )

    # como não há constraints, o pacote deve ter as dimensões do maior produto
    # e a soma das alturas dos produtos
    pkges = pkger.pack_products(source)

    # a quantidade de pacotes deve ser única, pois não temos constraints
    assert len(pkges) == 1

    pkge = pkges[0]

    assert pkge.width == Decimal(400)
    assert pkge.length == Decimal(300)
    # soma a altura de todos os produtos.. 2*p1 + 4*p2
    assert pkge.height - Decimal((100 + 100) + (110 + 110 + 110 + 110)) < Decimal(0.00001)
    # soma o peso de todos os produtos.. 2*p1 + 4*p2
    assert pkge.weight - Decimal((2000 + 2000) + (1530 + 1530 + 1530 + 1530))  < Decimal(0.00001)


@pytest.mark.django_db
def test_correios_packager_with_constraint_possible_1(rf, admin_user):
    MAX_WIDTH = 600
    MAX_LENGTH = 400
    MAX_HEIGHT = 350
    MAX_WEIGHT = 12000
    MAX_EDGES_SUM = 2000
    MIN_WIDTH = 120
    MIN_LENGTH = 100
    MIN_HEIGHT = 80

    constraint = CorreiosPackageConstraint(MAX_WIDTH,
                                           MAX_LENGTH,
                                           MAX_HEIGHT,
                                           MAX_WEIGHT,
                                           MAX_EDGES_SUM,
                                           MIN_WIDTH,
                                           MIN_LENGTH,
                                           MIN_HEIGHT)

    pkger = CorreiosSimplePackager()
    pkger.set_package_constraint(constraint)

    p1 = create_product(sku='p1', supplier=get_default_supplier(), width=350, depth=285, height=30, gross_weight=240)
    p2 = create_product(sku='p2', supplier=get_default_supplier(), width=150, depth=135, height=110, gross_weight=350)
    p3 = create_product(sku='p3', supplier=get_default_supplier(), width=40, depth=40, height=40, gross_weight=186)

    source = seed_source(admin_user)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=p1,
        supplier=get_default_supplier(),
        quantity=2,
        base_unit_price=source.create_price(10),
    )

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=p2,
        supplier=get_default_supplier(),
        quantity=4,
        base_unit_price=source.create_price(10),
    )

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=p3,
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
    )

    pkges = pkger.pack_products(source)
    assert len(pkges) == 2

    pkg1 = pkges[0]
    pkg2 = pkges[1]

    # no pacote 1 estão os 2 produtos p1 e 2 produtos p2
    assert pkg1.width == p1.width
    assert pkg1.length == p1.depth
    assert pkg1.height == (p1.height + p1.height + p2.height + p2.height)
    assert pkg1.weight == (p1.gross_weight + p1.gross_weight + p2.gross_weight + p2.gross_weight)
    assert pkg1.count == 4
    assert p1 in pkg1._products
    assert p2 in pkg1._products
    assert not p3 in pkg1._products

    # no pacote 2 estão 2 produtos p2 e 1 produtos p3
    assert pkg2.width == p2.width
    assert pkg2.length == p2.depth
    assert pkg2.height == (p2.height + p2.height + p3.height)
    assert pkg2.weight == (p2.gross_weight + p2.gross_weight + p3.gross_weight)
    assert pkg2.count == 3

    assert not p1 in pkg2._products
    assert p2 in pkg2._products
    assert p3 in pkg2._products


@pytest.mark.django_db
def test_correios_packager_with_constraint_possible_2(rf, admin_user):
    MAX_WIDTH = 1050
    MAX_LENGTH = 1050
    MAX_HEIGHT = 1050
    MAX_WEIGHT = 30000
    MAX_EDGES_SUM = 2000
    MIN_WIDTH = 120
    MIN_LENGTH = 100
    MIN_HEIGHT = 80

    constraint = CorreiosPackageConstraint(MAX_WIDTH,
                                           MAX_LENGTH,
                                           MAX_HEIGHT,
                                           MAX_WEIGHT,
                                           MAX_EDGES_SUM,
                                           MIN_WIDTH,
                                           MIN_LENGTH,
                                           MIN_HEIGHT)

    pkger = CorreiosSimplePackager()
    pkger.set_package_constraint(constraint)

    p1 = create_product(sku='p1', supplier=get_default_supplier(), width=MAX_WIDTH, depth=MAX_LENGTH, height=MAX_HEIGHT, gross_weight=MAX_WEIGHT)

    source = seed_source(admin_user)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=p1,
        supplier=get_default_supplier(),
        quantity=20,
        base_unit_price=source.create_price(10),
    )

    # deve empacotar 1 produto por caixa
    pkges = pkger.pack_products(source)
    assert len(pkges) == 20


@pytest.mark.django_db
def test_correios_packager_with_constraint_impossible_1(rf, admin_user):
    MAX_WIDTH = 600
    MAX_LENGTH = 400
    MAX_HEIGHT = 350
    MAX_WEIGHT = 12000
    MAX_EDGES_SUM = 2000
    MIN_WIDTH = 120
    MIN_LENGTH = 100
    MIN_HEIGHT = 80

    constraint = CorreiosPackageConstraint(MAX_WIDTH,
                                           MAX_LENGTH,
                                           MAX_HEIGHT,
                                           MAX_WEIGHT,
                                           MAX_EDGES_SUM,
                                           MIN_WIDTH,
                                           MIN_LENGTH,
                                           MIN_HEIGHT)

    pkger = CorreiosSimplePackager()
    pkger.set_package_constraint(constraint)

    p1 = create_product(sku='p1', supplier=get_default_supplier(), width=350, depth=285, height=30, gross_weight=240)
    p2 = create_product(sku='p2', supplier=get_default_supplier(), width=650, depth=135, height=110, gross_weight=350)

    source = seed_source(admin_user)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=p1,
        supplier=get_default_supplier(),
        quantity=2,
        base_unit_price=source.create_price(10),
    )

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=p2,
        supplier=get_default_supplier(),
        quantity=4,
        base_unit_price=source.create_price(10),
    )

    # impossível empacotar - produto p2 é maior que o tamanho maximo do pacote
    pkges = pkger.pack_products(source)
    assert pkges is None


def test_correios_packager_with_constraint_impossible_2(rf, admin_user):
    MAX_WIDTH = 600
    MAX_LENGTH = 400
    MAX_HEIGHT = 350
    MAX_WEIGHT = 12000
    MAX_EDGES_SUM = 2000
    MIN_WIDTH = 120
    MIN_LENGTH = 100
    MIN_HEIGHT = 80

    constraint = CorreiosPackageConstraint(MAX_WIDTH,
                                           MAX_LENGTH,
                                           MAX_HEIGHT,
                                           MAX_WEIGHT,
                                           MAX_EDGES_SUM,
                                           MIN_WIDTH,
                                           MIN_LENGTH,
                                           MIN_HEIGHT)

    pkger = CorreiosSimplePackager()
    pkger.set_package_constraint(constraint)

    p1 = create_product(sku='p1', supplier=get_default_supplier(), width=350, depth=285, height=30, gross_weight=240)
    p2 = create_product(sku='p2', supplier=get_default_supplier(), width=40, depth=135, height=110, gross_weight=12500)

    source = seed_source(admin_user)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=p1,
        supplier=get_default_supplier(),
        quantity=2,
        base_unit_price=source.create_price(10),
    )

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=p2,
        supplier=get_default_supplier(),
        quantity=4,
        base_unit_price=source.create_price(10),
    )

    # impossível empacotar - produto p2 tem peso maior que o tamanho maximo do pacote
    pkges = pkger.pack_products(source)
    assert pkges is None



@pytest.mark.django_db
def test_get_product_dimensions():
    p1 = create_product(sku='p1', width=10, depth=20, height=30, gross_weight=5000.0)

    # ordena e converter dimensões e peso
    w, l, h =_get_product_dimensions(p1)

    assert w == 30
    assert l == 20
    assert h == 10


