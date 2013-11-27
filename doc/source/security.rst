Security setup
##############

Not everyone is allowed to edit everything. There are a couple of roles:

- Logging in is required, so there are no anonymous users.

- Everyone that's logged in is assumed to be an employee. (So: explicitly no
  customers). Everyone is allowed to see the lists of persons and projects and
  some basic data. Basic data is mostly:

  - Billable project membership.

  - Hours booked on billable (=non-internal) projects.

  - How good you've booked (for some social pressure).

  - How many hours you work per week.

- You yourself are allowed to see all your own data. Target, hours booked
  everywhere, etc.

- Project leaders can see all data (including the financial data) on the
  projects they lead. This includes hourly tariffs of all project members.
  They can add team members and they can give them hours for the project.

- Project managers can see all data on the projects they manage. They can set
  the hourly tariff for the project members (but they cannot add them or
  adjust their hours).

- Office management can see everything and edit basically everything
  everywhere. Not bookings, though (but that's a
  booking-is-only-implemented-for-one-person restriction now).

- Management can see everything, but cannot edit more than otherwise.

- The django admin can adjust everything in the django admin interface, even
  stuff that's normally non-adjustable. Don't abuse it. Note that being the
  django admin doesn't give you extra rights in most of the view, it just
  means you can muck around in the django admin interface.

This is still quite a list... How do you get these roles?

- Only you are yourself, obviously.

- You are a project leader or project manager if office management has set you
  as such on a project's edit form.

- You are office management or management if office management (or the admin)
  set you up as such in your person edit form.

Ok, this is much simpler.

Most of the checks and filters are done in the views with custom methods, not
with Django permissions. The advantage here is that it steers towards keeping
everyone out of the Django admin interface :-)
