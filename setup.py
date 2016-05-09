# -*- coding: utf-8 -*-
# This file is part of Shoop Correios.
#
# Copyright (c) 2016, Rockho Team. All rights reserved.
# Author: Christian Hess
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import setuptools

NAME = 'shoop-correios'
VERSION = '1.0.0'
DESCRIPTION = 'A Correios shipping method add-on for Shoop'
AUTHOR = 'Rockho Team'
AUTHOR_EMAIL = 'rockho@rockho.com.br'
URL = 'http://www.rockho.com.br/'
LICENSE = 'AGPL-3.0'  # https://spdx.org/licenses/

EXCLUDED_PACKAGES = [
    'shoop_correios_tests', 'shoop_correios_tests.*',
]

REQUIRES = [
    "lxml<=3.6",
    "beautifulsoup4<=4.4"
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
        packages=["shoop_correios"],
        include_package_data=True,
        install_requires=REQUIRES,
        entry_points={"shoop.addon": "shoop_correios=shoop_correios"}
    )
