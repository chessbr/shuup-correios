import setuptools

EXCLUDED_PACKAGES = [
    'shoop_correios_tests', 'shoop_correios_tests.*',
]

REQUIRES = [
    "lxml<=3.6",
    "beautifulsoup4<=4.4"
]

if __name__ == '__main__':
    setuptools.setup(
        name="shoop-correios",
        version="0.1.0",
        description="Correios shipping method add-on for Shoop",
        packages=["shoop_correios"],
        include_package_data=True,
        install_requires=REQUIRES,
        entry_points={"shoop.addon": "shoop_correios=shoop_correios"}
    )
