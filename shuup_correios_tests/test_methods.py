# -*- coding: utf-8 -*-
# This file is part of Shuup Correios.
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from decimal import Decimal
import pytest

from shuup.core.models import (get_person_contact, OrderLineType)
from shuup.testing.factories import (
    get_address, get_default_product, get_default_shop,
    get_default_supplier, get_default_tax_class,
    get_payment_method, create_product
)
from shuup_tests.utils.basketish_order_source import BasketishOrderSource
from shuup_correios.models import CorreiosCarrier
from shuup_tests.core.test_order_creator import seed_source
from shuup.core.models._service_shipping import ShippingMethod
from mock import patch
from shuup_correios.correios import CorreiosWS
from shuup_correios_tests import create_mock_ws_result

MOCKED_SUCCESS_RESULT = create_mock_ws_result()

@pytest.mark.django_db
def test_create_services():
    carrier = CorreiosCarrier.objects.create(name="Correios")

    pac_service = carrier.create_service(
        'PAC',
        shop=get_default_shop(),
        enabled=True,
        tax_class=get_default_tax_class(),
        name="Correios PAC"
    )
    assert pac_service.behavior_components.count() == 1


    sedex_service = carrier.create_service(
        'SEDEX',
        shop=get_default_shop(),
        enabled=True,
        tax_class=get_default_tax_class(),
        name="Correios SEDEX"
    )
    assert sedex_service.behavior_components.count() == 1


    strange_service = carrier.create_service(
        'STRANGE',
        shop=get_default_shop(),
        enabled=True,
        tax_class=get_default_tax_class(),
        name="unknown"
    )
    assert strange_service.behavior_components.count() == 0


@pytest.mark.django_db
def get_correios_carrier_1():
    carrier = CorreiosCarrier.objects.create(name="Correios C1")

    pac_service1 = carrier.create_service(
        'PAC',
        shop=get_default_shop(),
        enabled=True,
        tax_class=get_default_tax_class(),
        name="Correios - PAC #1",
    )
    pac_service_bc1 = pac_service1.behavior_components.first()
    pac_service_bc1.cep_origem = '82015780'
    pac_service_bc1.max_weight = Decimal(30000.0)
    pac_service_bc1.max_width = Decimal(800.0)
    pac_service_bc1.max_length = Decimal(600.0)
    pac_service_bc1.max_height = Decimal(400.0)
    pac_service_bc1.min_width = Decimal(90.0)
    pac_service_bc1.min_length = Decimal(60.0)
    pac_service_bc1.min_height = Decimal(50.0)
    pac_service_bc1.max_edges_sum = Decimal(2000.0)
    pac_service_bc1.save()

    return carrier

@pytest.mark.django_db
def get_correios_carrier_2():
    carrier = CorreiosCarrier.objects.create(name="Correios C2")

    pac_service2 = carrier.create_service(
        'PAC',
        shop=get_default_shop(),
        enabled=True,
        tax_class=get_default_tax_class(),
        name="Correios - PAC #2",
    )
    pac_service_bc2 = pac_service2.behavior_components.first()
    pac_service_bc2.cep_origem = '88220000'
    pac_service_bc2.max_weight = Decimal(40000.0)
    pac_service_bc2.max_width = Decimal(800.0)
    pac_service_bc2.max_length = Decimal(600.0)
    pac_service_bc2.max_height = Decimal(400.0)
    pac_service_bc2.min_width = Decimal(90.0)
    pac_service_bc2.min_length = Decimal(60.0)
    pac_service_bc2.min_height = Decimal(50.0)
    pac_service_bc2.max_edges_sum = Decimal(2000.0)
    pac_service_bc2.mao_propria = True
    pac_service_bc2.valor_declarado = True
    pac_service_bc2.aviso_recebimento = True
    pac_service_bc2.additional_delivery_time = 2
    pac_service_bc2.additional_price = Decimal(13.3)
    pac_service_bc2.save()

    return carrier

@pytest.mark.django_db
def test_methods_possible(admin_user):
    with patch.object(CorreiosWS, 'get_preco_prazo', return_value=MOCKED_SUCCESS_RESULT):

        contact = get_person_contact(admin_user)
        source = BasketishOrderSource(get_default_shop())

        default_product = get_default_product()
        default_product.width = 500
        default_product.depth = 400
        default_product.heith = 130
        default_product.save()

        source.add_line(
            type=OrderLineType.PRODUCT,
            product=default_product,
            supplier=get_default_supplier(),
            quantity=1,
            base_unit_price=source.create_price(10),
            weight=Decimal("0.2")
        )
        billing_address = get_address()
        shipping_address = get_address(name="My House", country='BR')

        shipping_address.postal_code = "89070210"

        source.billing_address = billing_address
        source.shipping_address = shipping_address
        source.customer = contact

        source.shipping_method = get_correios_carrier_1()
        source.payment_method = get_payment_method(name="neat", price=4)
        assert source.shipping_method_id
        assert source.payment_method_id

        errors = list(source.get_validation_errors())
        # no errors
        assert len(errors) == 0

        final_lines = list(source.get_final_lines())

        assert any(line.type == OrderLineType.SHIPPING for line in final_lines)

        for line in final_lines:
            if line.type == OrderLineType.SHIPPING:
                assert line.text == "Correios - PAC #1"

@pytest.mark.django_db
def test_methods_impossible(admin_user):
    contact = get_person_contact(admin_user)
    source = BasketishOrderSource(get_default_shop())

    default_product = get_default_product()
    default_product.width = 5000
    default_product.depth = 4000
    default_product.heith = 1300
    default_product.save()

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=default_product,
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
        weight=Decimal("200")
    )
    billing_address = get_address()
    shipping_address = get_address(name="My House", country='BR')

    shipping_address.postal_code = "89070210"

    source.billing_address = billing_address
    source.shipping_address = shipping_address
    source.customer = contact

    source.shipping_method = get_correios_carrier_1()
    source.payment_method = get_payment_method(name="neat", price=4)
    assert source.shipping_method_id
    assert source.payment_method_id

    errors = list(source.get_validation_errors())
    assert len(errors) == 1



@pytest.mark.django_db
def test_correios_pack_source(rf, admin_user):
    with patch.object(CorreiosWS, 'get_preco_prazo', return_value=MOCKED_SUCCESS_RESULT):
        pac_carrier = get_correios_carrier_2()
        contact = get_person_contact(admin_user)
        p1 = create_product(sku='p1',
                            supplier=get_default_supplier(),
                            width=400,
                            depth=400,
                            height=400,
                            gross_weight=1250)

        source = seed_source(admin_user)
        source.add_line(
            type=OrderLineType.PRODUCT,
            product=p1,
            supplier=get_default_supplier(),
            quantity=2,
            base_unit_price=source.create_price(10),
        )
        billing_address = get_address()
        shipping_address = get_address(name="My House", country='BR')
        shipping_address.postal_code = "89070210"
        source.billing_address = billing_address
        source.shipping_address = shipping_address
        source.customer = contact


        bc = ShippingMethod.objects.filter(carrier=pac_carrier).first().behavior_components.first()
        packages = bc._pack_source(source)
        assert len(packages) == 2

        results = bc._get_correios_results(source, packages)
        assert len(results) == 2
        # todos devem ter dado certo
        assert all(result.erro == 0 for result in results)
        assert all(result.valor > Decimal(0) for result in results)

        delivery_time = bc.get_delivery_time(ShippingMethod.objects.filter(carrier=pac_carrier).first(), source)
        assert not delivery_time is None

        # como os locais de entrega sao iguais, prazo iguais
        assert delivery_time.max_duration == delivery_time.min_duration
        assert delivery_time.max_duration.days > 0


@pytest.mark.django_db
def test_correios_delivery_time_1(rf, admin_user):

    with patch.object(CorreiosWS, 'get_preco_prazo', return_value=MOCKED_SUCCESS_RESULT):
        pac_carrier = get_correios_carrier_2()
        contact = get_person_contact(admin_user)
        p1 = create_product(sku='p1',
                            supplier=get_default_supplier(),
                            width=400,
                            depth=400,
                            height=400,
                            gross_weight=1250)

        source = seed_source(admin_user)
        source.add_line(
            type=OrderLineType.PRODUCT,
            product=p1,
            supplier=get_default_supplier(),
            quantity=1,
            base_unit_price=source.create_price(10),
        )
        billing_address = get_address()
        shipping_address = get_address(name="My House", country='BR')
        shipping_address.postal_code = "89070210"
        source.billing_address = billing_address
        source.shipping_address = shipping_address
        source.customer = contact

        bc = ShippingMethod.objects.filter(carrier=pac_carrier).first().behavior_components.first()
        packages = bc._pack_source(source)
        assert len(packages) == 1

        results = bc._get_correios_results(source, packages)
        assert len(results) == 1
        assert results[0].erro == 0
        assert results[0].valor > Decimal(0)

        delivery_time = bc.get_delivery_time(ShippingMethod.objects.filter(carrier=pac_carrier).first(), source)
        assert not delivery_time is None
        assert delivery_time.max_duration == delivery_time.min_duration
        assert delivery_time.max_duration.days == results[0].prazo_entrega + bc.additional_delivery_time

        costs = list(bc.get_costs(ShippingMethod.objects.filter(carrier=pac_carrier).first(), source))
        assert len(costs) == 1
        assert source.create_price(results[0].valor + bc.additional_price) == costs[0].price


@pytest.mark.django_db
def test_correios_delivery_time_2(rf, admin_user):
    with patch.object(CorreiosWS, 'get_preco_prazo', return_value=MOCKED_SUCCESS_RESULT):
        pac_carrier = get_correios_carrier_2()
        contact = get_person_contact(admin_user)
        p1 = create_product(sku='p1',
                            supplier=get_default_supplier(),
                            width=400,
                            depth=400,
                            height=400,
                            gross_weight=1250)

        # P2 é pesado pacas - é empacotado em uma caixa separada
        # só para dar problema na metade da entrega
        p2 = create_product(sku='p2',
                            supplier=get_default_supplier(),
                            width=400,
                            depth=400,
                            height=400,
                            gross_weight=31250)

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
            quantity=1,
            base_unit_price=source.create_price(20),
        )

        billing_address = get_address()
        shipping_address = get_address(name="My House", country='BR')
        shipping_address.postal_code = "89070210"
        source.billing_address = billing_address
        source.shipping_address = shipping_address
        source.customer = contact

        shipping = ShippingMethod.objects.filter(carrier=pac_carrier).first()

        bc = shipping.behavior_components.first()
        packages = bc._pack_source(source)
        assert len(packages) == 3

        results = bc._get_correios_results(source, packages)
        assert len(results) == 3

