Time registration system ("TRS")
==========================================


.. image:: https://travis-ci.org/nens/trs.png?branch=master
   :target: https://travis-ci.org/nens/trs

.. image:: https://coveralls.io/repos/nens/trs/badge.png?branch=master
  :target: https://coveralls.io/r/nens/trs?branch=master


`Nelen & Schuurmans <http://www.nelen-schuurmans.nl>`_-internal tool for,
basically, booking our hours and managing projects.


Local development installation
------------------------------

Make a copy of the database on the server::

  $ sqlite3 var/db/trs.db ".backup trs_`date +%Y-%m-%d`.db"

Grab the sqlite db from the server::

  $ scp the.server.name:/srv/trs.nelen-schuurmans.nl/trs_YYYY-MM-DD.db var/db/trs.db

Add a ``.env`` with the nens-auth-client cognito settings for localhost.

Some commands::

  $ make install
  $ make test
  $ pre-commit run --all

Keep the python version in sync between the ``Dockerfile`` and the ``pyproject.toml``
(``requires-python`` and ``target-version``).


To test the docker setup::

  $ docker compose build
  $ docker compose up

For local development, you need some additional environment variables. Set them in a
`.env` or use "direnv":

    export DEBUG=True
    export SECRET_KEY="xxx"
    export NENS_AUTH_ISSUER="xxx
    export NENS_AUTH_CLIENT_ID="xxx"
    export NENS_AUTH_CLIENT_SECRET="xxx"


Server installation
-------------------

For a production installation, see the private
https://github.com/nens/trs-site repo.


Weeks
-----

A ``YearWeek`` is the core time object in the site: every year+week
combination has its own database object for easy filtering. They must be
created with a management command::

    $ bin/python manage.py update_weeks

It is safe to run this command more than once. In case this site is still used
after 2028: adjust the ``TRS_END_YEAR`` setting and run the command again :-)
