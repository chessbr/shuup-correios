# -*- coding: utf-8 -*-
# This file is part of Shuup Correios.
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

#
# Classe utilizada para empacotar os pedidos
#
CORREIOS_PRODUCTS_PACKAGER_CLASS = ("shuup_order_packager.algorithms.simple:SimplePackager")

#
# Nome do cache a ser utilizado para armazenar os resultados do webservice do Correio
#
CORREIOS_CACHE_NAME = 'default'

#
# Quantidade de tempo, em segundos, para estourar timetout na requisição com o webservice
#
CORREIOS_WEBSERVICE_TIMEOUT = 5.0
