Changelog of TRS
===================================================


3.0 (2026-01-26)
----------------

- Removed "minimum hourly tariff" as it wasn't used.

- Added htmx for better interaction (infinite scroll for the project list, nicer
  filtering on person/project lists, quicker interaction on booking page).

- "Hours" and "hourly tariff" and so are integer fields now instead of decimal fields:
  after 10 years, there's no risk of them becoming non-integers now.

- No more change history for bookings and work assignments, simplifying the code and
  some views.

- Improved the project team edit form.

- Got booking-per-day to work. Everything works as before with bookings attached to
  year/weeks, but bookings *also* have a date. So everything that looks up bookings per
  year/week works and everything that would rather query per month works.

- Switched on booking-per-day on 2026-01-26.


2.2 (2025-05-27)
----------------

- Switched from csv to excel export. xlsxwriter wasn't available when the
  project started and it is now. So hopefully all the csv-related small
  mishaps are gone now :-)

- Fixed person creation. Name wasn't getting set. All name updates to User are
  handled now, fixing the problem.

- Fixed 'projectbegroting' form, which didn't display errors (and the form itself)
  properly when there was a validation error.

- Big upgrade from python 3.10 to 3.13, django 3.2 to 5.2. And updated the setup to use
  ``uv`` instead of pip-tools. Locally, docker isn't used anymore.


2.1 (2022-08-08)
----------------

- Sped up the WBSO csv export considerably.

- Using Cognito instead of the old SSO now. N&S users are automatically
  accepted, so no manual user adding is necessary anymore.


2.0 (2022-08-05)
----------------

- Upgraded django from 1.8 to 1.11. And to 2.2. And to 3.2.

- Upgraded ubuntu from 16.04 to 18.04. And to 20.04. And to 22.04

- Upgraded python in lockstep with ubuntu, so we went from 3.5 to 3.10.

- Moved from buildout to pip-tools.

- Switched server setup to docker-compose.

- There's only one settings file now. ``DEBUG`` and ``SECRET_KEY`` and others
  are handled through env variables.

- The accompanying private ``trs-site`` github project now only contains the
  ansible scripts and a ``.env`` file with the necessary settings.

- Staticfiles are stored inside the docker image.

- Removed django-haystack (=the old full-text search method, it was only used
  once per month or so).

- Using pytest instead of django-nose.


1.17 (2020/2021)
-----------------

- Showing decimals for 'opdrachtsom', also showing decimals in the last two
  columns of the main project financial table.

- Management can now also see team details on the project page.

- Added new simpler search page.


1.16 (2019-01-22)
-----------------

- Added newest version of lizard-auth-client in preparation for switching to
  the new style of connecting to the SSO (and especially the staging SSO).

- .0 projects have mandatory tariffs of 0 now.

- Added 'software development' field (mimicking the 'profit' field) on
  projects.


1.15 (2016-06-10)
-----------------

- Made it impossible for projects to fabricate money out of thin air by giving
  team members hours+tariff when there's no budget for it.

- You can now set hours/tariff to zero without the code falling back to the
  previous value...

- Project budgets are now OK if they fall within one Euro of zero, instead of
  requiring it to be exactly zero. This compensates for contract amounts not
  always being fully rounded.

- Added the fields of the "project loss view" to the main projects csv export.


1.14 (2016-03-02)
-----------------

- Various version updates and test setup fixes to get the tests running on
  travis-ci.org again.

- Added ratings for both customers and projectteam. Including an accompagnying
  reason/comment field. And including an overview page.

- We require python 3.4 now as we use the new "statistics" module.

- Fixed bug that members of a hidden project (like sickness projects) *could*
  download the full ``.csv`` file with all other peoples' info...

- Fixed bug that the project-is-ended state would be cached. This state
  changes without the project itself changing, so the cached value would stay
  the same. Now we just calculate it every time.

- Added opbeat.com configuration for the nice performance metrics it
  provides.

- Added two columns to project csv export.

- Added overview page which makes "booking into the red" more visible, both
  for hours and for money.

- Made other persons' bookings editable for those that can edit everything.

- Added financial overviews with csv downloads.


1.13 (2015-06-18)
-----------------

- Added 'Payable' class: money we have to pay other parties (NL: "kosten
  derden").


1.12 (2015-05-29)
-----------------

- Removed 'nog te verdelen' row from the project template.

- Added quick editing of the two remark fields on projects with a popup.

- You can now enable a project/person filter as a "sidebar" on the right hand
  side of the screen if you're viewing a person/project/person list. Including
  easy browsing through that list.

- Added sum of all reservations to the reservations overview.


1.11 (2015-02-18)
-----------------

- If a budget item transfers money to another project, that project's cache
  key is now also updated.

- Project members can see all financial data on the project.

- Added an extra csv download for subsidized project: a list of all project
  members plus their bookings on other projects during the subsidized
  project's duration.

- Added a filter for the persons overview page to show a specific year's data
  instead of that of the current year.


1.10 (2015-01-02)
-----------------

- Showing bid and confirmation dates in the interface. Added a bit of
  filtering, though, so that the dates don't show up unecessarily as
  not-filled-in. I filter out archived projects and pre-2015 projects
  that already have a contract amount set, for instance.

- Changed cost-related columns in project overview, incuding a new column 'is
  the budget OK?'.

- Added check whether the budget of a project is OK (the amount of money left
  to dish out should be zero). In consequence, removed the check whether there
  is a correct contract amount.

- New team members start out with a tariff of 0 instead of having their normal
  tariff pre-filled-in.

- Speed improvement by caching the person and project widgets.

- Project page is wider now: more room for the budget table.

- Budget transfers between projects are now done explicitly by linking to the
  the project you transfer budget to. No more mismatched amounts. Note: there
  is a data migration that automatically fixes 70% of the current budget
  transfers).

- Budget items are now treated as costs. So a positive number counts as a cost
  to the project. This should remove lots of confusion. (Note: there is a data
  migration that automatically fixes the current numbers).

- The project budget table now has a separate colum for costs and one for
  income. Clearer that way, previously a budget transfer from another project
  would show up as a "negative cost"...

- Costs can be tagged as "third party costs".

- Reservation for future work is done with a specific attribute on the project
  instead of with a generic budget item.

- Added overview pages for 3th party costs and for budget reservations.

- Staticfiles cronjob runs every night, now. Somehow it is needed.

- Added some columns to the csv export of persons.


1.9 (2014-07-15)
----------------

- Added new filter mechanism: easier to combine filters ("archived projects
  belonging to group 'software development'"). Including clearer UI.

- Added option to show all projects (including archived ones) on a person's
  page.

- PL/PM can edit start/end date of projects again.


1.8 (2014-07-08)
----------------

- Running 'collectstatic' from within the buildout. Now I've finally found the
  source of my missing js/css problem...

- Added search with 'whoosh' and 'haystack'. Including cronjob to refresh the
  search index every hour.


1.7 (2014-07-07)
----------------

- Added pagination for project page.

- Fixed caching: project changes increment the assigned persons' cache key
  now.

- Added fill_cache cronjob that runs every five minutes.

- Longer description form field for projects.

- Added 'nowrap' for project widget, preventing it from wrapping lines.

- Showing all unarchived projects in person view. Previous version also
  excluded the projects whose end date had passed.

- Fixed sorting of 'p1233.10' versus 'p1233.2'

- Bookings now visible (for those with the right permissions) per user instead
  of only for yourself.

- Emptied out the navbar a bit in preparation for a search box.

- Unified the date formatting.

- Got the tests working again.

- Made the behaviour of "project is accepted" less restrictive: most of the
  editing is still possible.


1.6 (2014-02-06)
----------------

- Added csv export of persons and projects overviews.

- Added separate 'contract amount ok' checkbox on projects to allow contract
  amounts of zero to be accepted.

- Permission fixes (the system was a bit too strict for project leaders).

- Added csv export of project data.

- Added permission checks for the csv exports.


1.5 (2014-01-27)
----------------

- A project leader or manager can see the elaborate manager version of the
  projects page if he's only looking at his own projects.

- Added management command to automatically book hours for one year for 3
  specific users (=management).

- Nicer relative target bar. And for the current year you only see the
  relative one anyway.

- A contract amount of zero? Then nothing on that project gets counted as
  turnover or towards someone's target. Reason: we don't want to fabricate
  money somewhere in the system.

- Added totals on project page.

- Showing 'costs' and 'reservations' separately on projects page.

- Project leaders can now also edit the project's budget.

- Various smaller UI fixes. Like showing new projects at the top.

- Showing list of latest project codes on project create page.


1.4 (2014-01-22)
----------------

- Added extra column 'booked this year' in PersonView. Handy.

- Added overview of project leaders and managers.

- Nicer feedback in title on selected filters (for persons and projects page).

- Added groups. Including using filters on groups in person and projects views

- Added extra column 'booked this year' in PersonView. Handy.

- Better change overview page, including option to see all projects' changes
  when you're a manager.


1.3 (2014-01-21)
----------------

- Booking overview shows the correct booking feedback in the sidebar now.

- Showing target percentage also relative to the size of the elapsed year.
  More useful.

- project costs on the team edit page.

- Unified team table and budgetitem table on the project page.

- Added financial remark field on project; the other remark field is now also
  editable by PL/PM. The financial one only by office management.

- Allowing PM/PL to edit a project (but with fewer fields available for them
  to edit). This way they can edit the project's end date and the "startup
  meeting" and "accepted" checkboxes.

- Added 'startup meeting done' boolean on project.

- Calculating the money amount that is bookable per person, in addition to the
  already-calculated amount of available external hours per person.

- PM/PL get their hourly tariff automatically set upon project creation.

- Better 'werkvoorraad' calculation: only counting external projects again.

- Project leader can edit the tariffs for the team members too, now.


1.2 (2014-01-10)
----------------

- Invoice amounts are shown including their decimal part.

- Fixed target calculation on per-year percentages overview page.

- Logout works now.

- Added totals in/exclusive on invoice overview page.

- Fixed invoice amount calculation on projects page.

- Improved project budget display.

- Added deletion of invoices and budget items.

- Import fixes: invoices amounts aren't rounded anymore and the principal
  ("opdrachtgever") is imported, too.

- A project code must be unique now.


1.1 (2014-01-09)
----------------

- YearWeeks now store the amount of days they're missing. This is only
  relevant for the start and end week of a year. Storing it in there cuts down
  on complexity in quite a few places.

- Fixed YearWeek representation in forms: the personchange form works again.

- You can now remove team members, provided they haven't booked anything yet.

- Teams are updated right away, again, after adding a new team member.

- Added explanation page for the main percentages.

- Added error 500 logging.

- Invoices edited go back to the invoice overview page when clicked on from
  there.

- Added hint that the 'left to book' number excludes the current week.

- Auto-assigning projectleader/manager to projects. Including message.

- Added filtering to projects, persons and invoices pages.

- Forcing IE8 to use the newest rendering mode (fix for IE8).

- Disabled full import: the last import of 2013 is done, now the new TRS takes
  over.

- Added view to automatically add Pl/PM to a project. Same for persons on an
  internal project.

- Using the current week as default for start/end week for projects.

- Nicer formatting of YearWeek for the project edit view.

- Showing active persons before archived ones (handy for project edit page).

- Fixed team display on project page.


1.0 (2013-12-31)
----------------

- Cache tweak to get correct number-of-hours-to-work.


0.5 (2013-12-31)
----------------

- Added gaug.es tracking.

- Added booking overview page.

- Booking form fixes.

- UI improvements.

- Handling incomplete first/last weeks of the year the right way.

- Javascript to auto-sum the hours for the week you're booking.


0.4 (2013-12-30)
----------------

- Showing number of vacation hours left on homepage. Handy!

- Added totals to booking page (not dynamic yet, though).

- Got booking filtering to work:

  - Archived projects aren't bookable.

  - Not-yet-active or not-active-anymore projects aren't bookable.

  - You can only book in the current year.

- Prevented a lot of editing on archived items. Editing archived persons on a
  team, adding/editing invoices on archived projects, etc.


0.3 (2013-12-28)
----------------

- Removed unused login_name field from Person.

- Still-to-book info is now in absolute numbers for the whole year instead of
  a percentage of the last four weeks.

- A project leader can always add someone to the project, even if the project
  is accepted (="locked down for changes"). In the latter case, the person is
  added for a zero hourly tariff. At least the person can book on the project!

- Added overview page for all invoices (full-width).

- Added overview page listing all overviews.

- Added detailed turnover/booking/overbooked calculation for projects,
  including percentage "invoiced versus turnover+costs".


0.2 (2013-12-24)
----------------

- UI improvements.

- Allowing projects not to be counted towards internal/external hours (for
  holidays, for instance).

- Showing a person's KPI if you're admin.

- Importing extra project costs and invoices.

- Importing more project and person information from the csv files: project
  manager, project comments, target, hourly tariff.

- Only importing bookings from 2013, that fits better with the rest of the
  import.


0.1 (2013-12-18)
----------------

- Using memcache. Waaay faster.

- Optimized caching for PersonChange changes. They happen less frequently.

- Better management projects overview: showing the invoiced/projectamount
  percentage now.

- Way quicker site due to optimized queries. It is still a bit slow in places,
  but bearable now.

- Visual feedback on your key metrics.

- Simpler projects/persons view.

- More elaborate persons/projects view for management including key metrics.

- Added server setup. Config is through ``trs-site``, which you can include
  via mr.developer. The real readme for the server install is in there, too.

- Added lizard-auth-client for sso.lizard.net support. You can prepare persons
  in TRS beforehand and they'll be coupled automatically (based on login name)
  the moment they actually log in.

- More information on the overviews.

- Added progress bars for project overview.

- Made labels less obtrusive.

- Added permission checks all over the place.

- Added all directly necessary forms.

- Fixed formatting of hours and money. Note: money is in a fixed width font
  now.

- Filled in most of the project page, including the financial data.

- Added login/logout views.

- Added booking page including actual booking.

- Added the initial set of models and base overview pages for
  persons/projects.

- Initial project structure created with nensskel 1.34.dev0.
