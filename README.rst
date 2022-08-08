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
