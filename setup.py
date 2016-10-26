# -*- coding: utf-8 -*-
# This file is part of Shuup Correios.
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import setuptools

NAME = 'shuup-correios'
VERSION = '1.0.0'
DESCRIPTION = 'A Correios shipping method add-on for Shuup'
AUTHOR = 'Rockho Team'
AUTHOR_EMAIL = 'rockho@rockho.com.br'
URL = 'http://www.rockho.com.br/'
LICENSE = 'AGPL-3.0'  # https://spdx.org/licenses/

EXCLUDED_PACKAGES = [
    'shuup_correios_tests', 'shuup_correios_tests.*',
]

REQUIRES = [
    "xmltodict"
]

if __name__ == '__main__':
    setuptools.setup(
        name=NAME,
        version=VERSION,
        description=DESCRIPTION,
        url=URL,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        license=LICENSE,
        packages=["shuup_correios"],
        include_package_data=True,
        install_requires=REQUIRES,
        entry_points={"shuup.addon": "shuup_correios=shuup_correios"}
    )
