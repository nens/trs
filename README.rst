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

Grab the sqlite db from the server::

  $ scp the.server.name:/srv/trs.nelen-schuurmans.nl/var/db/trs.db var/db/

Add a ``.env`` with the SSO settings for localhost.

Symlink the development compose file and build it::

  $ ln -s docker-compose.development.yml docker-compose.override.yml
  $ docker compose build

You can run it with one of the following::

  $ docker compose up
  $ docker compose run --rm --service-ports web bin/python manage.py runserver 0.0.0.0:5000

Run the tests::

  $ docker compose run --rm web make test

And sometimes::

  $ docker compose run --rm web make beautiful

For upgrading versions: ``requirements/requirements.in`` (and ``.txt``) are in
a mounted subfolder, so running "make install" inside the docker will update
.txt if you change the .in. But changes to the makefile or the setup.py are
only copied when you re-build the docker.... So what I did during the upgrades
of the django versions was to change the version in ``requirements.in``, run
``make install`` and then rebuild the docker::

  $ docker compose run --rm web make install
  $ docker compose build

And sometimes, to upgrade all versions to the latest ones::

  $ docker compose run --rm web make upgrade
  $ docker compose run --rm web make install


Server installation
-------------------

See the ``src/trs-site/README.rst`` (from the protected github trs-site repo).

The site doesn't run with docker-compose there, yet, though.


Weeks
-----

A ``YearWeek`` is the core time object in the site: every year+week
combination has its own database object for easy filtering. They must be
created with a management command::

    $ bin/python manage.py update_weeks

It is safe to run this command more than once. In case this site is still used
after 2025: adjust the ``TRS_END_YEAR`` setting and run the command again :-)


Upgrade notes
-------------

Als ik van buildout naar pip overga mis ik o.a. de volgende zaken:

- mr.developer checkout van trs-site

- DONE mkdir van var/static, db, log, cache, media

- DONE gunicorn/supervisord config (supervisor kan weg)

- DONE settings selectie (één setting, DEBUG enzo via env var)

- DONE (grunt nog niet, is dat nodig?) npm setup met bower en grunt

- DONE Auto-run van ``bin/bower --allow-root install``

- DONE nginx template (vervangen door gunicorn)

- DONE collectstatic

En in productie:

- cronjob ``bin/python manage.py fill_cache``, elke 5 minuten

memcache met z'n 64MB: zat. Beetje lopen testen en er lijkt 10% gebruikt te
worden :-)
