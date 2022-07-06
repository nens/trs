from __future__ import unicode_literals
import monkeypatch_setuptools
from setuptools import setup

version = "2.0.dev0"

long_description = "\n\n".join(
    [open("README.rst").read(), open("CREDITS.rst").read(), open("CHANGES.rst").read()]
)

install_requires = (
    [
        "Django >= 1.11",
        "Werkzeug",
        "beautifulsoup4",
        "django-extensions",
        "django-tls",
        "gunicorn",
        "lizard-auth-client >= 2.13",
        "python3-memcached",
        "raven",
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
    "pytest-django < 4",  # Remove restriction when django is new enough.
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
