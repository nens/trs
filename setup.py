from __future__ import unicode_literals
import monkeypatch_setuptools
from setuptools import setup

version = "2.0.dev0"

long_description = "\n\n".join(
    [open("README.rst").read(), open("CREDITS.rst").read(), open("CHANGES.rst").read()]
)

install_requires = (
    [
        "Django >= 3.2",
        "Werkzeug",
        "beautifulsoup4",
        "django-extensions > 3.0.0",
        "django-tls_rvanlaar == 0.0.3",
        "gunicorn",
        "lizard-auth-client >= 3.0",
        "python3-memcached",
        "requests",
        "setuptools",
    ],
)

tests_require = [
    "coverage",
    "factory_boy",
    "mock",
    "pytest",
    "pytest-cov",
    "pytest-django",
]

setup(
    name="trs",
    version=version,
    description="Time Registration System (company-internal)",
    long_description=long_description,
    # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[],
    keywords=[],
    author="Reinout van Rees",
    author_email="reinout.vanrees@nelen-schuurmans.nl",
    url="https://github.com/nens/trs",
    license="GPL",
    packages=["trs"],
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={"test": tests_require},
    entry_points={"console_scripts": []},
)
