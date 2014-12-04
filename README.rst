Time registration system ("TRS")
==========================================


.. image:: https://travis-ci.org/nens/trs.png?branch=master
   :target: https://travis-ci.org/nens/trs

.. image:: https://coveralls.io/repos/nens/trs/badge.png?branch=master
  :target: https://coveralls.io/r/nens/trs?branch=master


`Nelen & Schuurmans <http://www.nelen-schuurmans.nl>`_-internal tool for,
basically, booking our hours and managing projects.


Extra ubuntu packages
---------------------

python3
python3-dev




Local development installation
------------------------------

Grab the sqlite db from the server::

    $ scp 110-ws-d05.external-nens.local:/srv/trs.lizard.net/var/db/trs.db var/db/

Bootstrap with python3::

    $ python3 bootstrap.py && bin/buildout


Server installation
-------------------

Hey, supervisord nor fabric are currently ready for python 3. So our normal
lizard site setup is out of the window. Time to try something new!

The installation is explained in the password-protected trs-site project's
README.


Weeks
-----

A ``YearWeek`` is the core time object in the site: every year+week
combination has its own database object for easy filtering. They must be
created with a management command::

    $ bin/django update_weeks

It is save to run this command more than once. In case this site is still used
after 2020: adjust the ``TRS_END_YEAR`` setting and run the command again :-)
