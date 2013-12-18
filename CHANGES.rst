Changelog of trs
===================================================


0.2 (unreleased)
----------------

- Nothing changed yet.


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
