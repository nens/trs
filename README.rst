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

Add ``trs/local_testsettings.py`` with the SSO settings for localhost.

Install django with the makefile::

  $ docker-compose build
  $ docker-compose run web make install

You can run it with::

  $ docker-compose up


Server installation
-------------------

See the ``src/trs-site/README.rst`` (from the protected github trs-site repo).

The site doesn't run with docker-compose there, yet, though.


Weeks
-----

A ``YearWeek`` is the core time object in the site: every year+week
combination has its own database object for easy filtering. They must be
created with a management command::

    $ bin/django update_weeks

It is safe to run this command more than once. In case this site is still used
after 2025: adjust the ``TRS_END_YEAR`` setting and run the command again :-)


Upgrade notes
-------------

Als ik van buildout naar pip overga mis ik o.a. de volgende zaken:

- mr.developer checkout van trs-site

- mkdir van var/static, db, log, cache, media, index

- gunicorn/supervisord config

- settings selectie

- npm setup met bower en grunt

- Auto-run van ``bin/bower --allow-root install``

- nginx template

- collectstatic

En in productie:

- cronjob ``bin/django fill_cache``, elke 5 minuten

- cronjob collectstatic??? Elke nacht?

- cronjob ``bin/django update_index--age 2`` elk uur? Wat doet dat? Oh, search
  index updaten.
