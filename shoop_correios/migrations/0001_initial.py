# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from decimal import Decimal
import shoop.core.fields
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0021_weight_based_pricing'),
    ]

    operations = [
        migrations.CreateModel(
            name='CorreiosBehaviorComponent',
            fields=[
                ('servicebehaviorcomponent_ptr', models.OneToOneField(parent_link=True, serialize=False, primary_key=True, to='shoop.ServiceBehaviorComponent', auto_created=True)),
                ('cod_servico', models.CharField(help_text='Código atribuído automaticamente ao criar o serviço.', choices=[('41106', '(41106) PAC'), ('40010', '(40010) Sedex'), ('40215', '(40215) Sedex 10'), ('40045', '(40045) Sedex a cobrar'), ('40290', '(40290) Sedex Hoje'), ('99999', '(99999) eSedex')], max_length=10, verbose_name='Código do serviço')),
                ('cod_servico_contrato', models.CharField(help_text='Informe o código do serviço em contrato, se existir. Quando há um contrato com os Correios, é necessário informar este código para que ele seja utilizado no cálculo dos preços e prazos.', null=True, blank=True, max_length=10, verbose_name='Código do serviço em contrato')),
                ('cep_origem', models.CharField(help_text='CEP de origem da encomenda. Apenas números, sem hífen.', default='99999999', max_length=8, verbose_name='CEP de origem')),
                ('cod_empresa', models.CharField(help_text='Seu código administrativo junto à ECT, se existir. O código está disponível no corpo do contrato firmado com os Correios.', null=True, blank=True, max_length=30, verbose_name='Código da empresa')),
                ('senha', models.CharField(help_text='Senha para acesso ao serviço, associada ao seu código administrativo, se existir. A senha inicial corresponde aos 8 primeiros dígitos do CNPJ informado no contrato.', null=True, blank=True, max_length=30, verbose_name='Senha')),
                ('mao_propria', models.BooleanField(help_text='Indica se a encomenda será entregue com o serviço adicional mão própria.', default=False, verbose_name='Mão própria?')),
                ('valor_declarado', models.BooleanField(help_text='Indica se a encomenda será entregue com o serviço adicional valor declarado.', default=False, verbose_name='Valor declarado?')),
                ('aviso_recebimento', models.BooleanField(help_text='Indica se a encomenda será entregue com o serviço adicional aviso de recebimento.', default=False, verbose_name='Aviso de recebimento?')),
                ('additional_delivery_time', models.PositiveIntegerField(help_text='Indica quantos dias devem ser somados ao prazo original retornado pelo serviço dos Correios. O prazo será somado no prazo de cada encomenda diferente.', default=0, validators=[django.core.validators.MinValueValidator(0)], blank=True, verbose_name='Prazo adicional')),
                ('additional_price', models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Preço adicional', help_text='Indica o valor, em reais, a ser somado ao preço original retornado pelo serviço dos Correios. O preço será somado no valor de cada encomenda diferente.', default=Decimal('0'), validators=[django.core.validators.MinValueValidator(Decimal('0'))], blank=True)),
                ('max_weight', shoop.core.fields.MeasurementField(max_digits=36, decimal_places=9, verbose_name='Peso máximo', help_text='Indica o peso máximo admitido para esta modalidade.', default=Decimal('0'), unit='g', validators=[django.core.validators.MinValueValidator(Decimal('0'))], blank=True)),
                ('min_length', shoop.core.fields.MeasurementField(decimal_places=9, max_digits=36, help_text='Indica o comprimento mínimo para caixas e pacotes.', default=160, unit='mm', verbose_name='Comprimento mínimo', validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('max_length', shoop.core.fields.MeasurementField(decimal_places=9, max_digits=36, help_text='Indica o comprimento máximo para caixas e pacotes.', default=1050, unit='mm', verbose_name='Comprimento máximo', validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('min_width', shoop.core.fields.MeasurementField(decimal_places=9, max_digits=36, help_text='Indica a largura mínima para caixas e pacotes.', default=110, unit='mm', verbose_name='Largura mínima', validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('max_width', shoop.core.fields.MeasurementField(decimal_places=9, max_digits=36, help_text='Indica a largura máxima para caixas e pacotes.', default=1050, unit='mm', verbose_name='Largura máxima', validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('min_height', shoop.core.fields.MeasurementField(decimal_places=9, max_digits=36, help_text='Indica a altura mínima para caixas e pacotes.', default=200, unit='mm', verbose_name='Altura mínima', validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('max_height', shoop.core.fields.MeasurementField(decimal_places=9, max_digits=36, help_text='Indica a altura máxima para caixas e pacotes.', default=1050, unit='mm', verbose_name='Altura máxima', validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('max_edges_sum', shoop.core.fields.MeasurementField(decimal_places=9, max_digits=36, help_text='Indica a soma máxima das dimensões de altura + largura + comprimento para caixas e pacotes.', default=2000, unit='mm', verbose_name='Soma máxima das dimensões (L + A + C)', validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
            ],
            options={
                'abstract': False,
            },
            bases=('shoop.servicebehaviorcomponent',),
        ),
        migrations.CreateModel(
            name='CorreiosCarrier',
            fields=[
                ('carrier_ptr', models.OneToOneField(parent_link=True, serialize=False, primary_key=True, to='shoop.Carrier', auto_created=True)),
            ],
            options={
                'verbose_name_plural': 'Correios',
                'verbose_name': 'Correios',
            },
            bases=('shoop.carrier',),
        ),
    ]
