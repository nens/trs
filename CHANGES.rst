Changelog of trs
===================================================


1.3 (unreleased)
----------------

- Nothing changed yet.


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
