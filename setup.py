from __future__ import unicode_literals
from setuptools import setup

version = '0.5'

long_description = '\n\n'.join([
    open('README.rst').read(),
    open('CREDITS.rst').read(),
    open('CHANGES.rst').read(),
    ])

install_requires = [
    'Django >= 1.6',
    'Werkzeug',
    'beautifulsoup4',
    'django-debug-toolbar',
    'django-extensions',
    'django-tls',
    'gunicorn',
    'lizard-auth-client >= 0.9',
    'python3-memcached',
    'requests',
    'setuptools',
    'south',
    ],

tests_require = [
    'nose',
    'mock',
    'factory_boy',
    'coverage',
    'django-nose',
    'coveralls',
    ]

setup(name='trs',
      version=version,
      description="Time Registration System (company-internal)",
      long_description=long_description,
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[],
      keywords=[],
      author='Reinout van Rees',
      author_email='reinout.vanrees@nelen-schuurmans.nl',
      url='https://github.com/nens/trs',
      license='GPL',
      packages=['trs'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require={'test': tests_require},
      entry_points={
          'console_scripts': [
          ]},
      )
