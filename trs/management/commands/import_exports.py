import csv
import datetime
import glob
import itertools
import logging
import os
import tempfile

from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
import requests

from trs import models

logger = logging.getLogger(__name__)

NAME_LINE = 1
YEAR_LINE = 6
WEEKS_LINE = 7
START_COLUMN = 10
HOURS_TO_WORK_FILENAME = 'hours_to_work.html'


def date_string_to_date(date_string):
    # dd-mm-yyyy
    day = int(date_string[0:2])
    month = int(date_string[3:5])
    year = int(date_string[6:])
    return datetime.date(year, month, day)


def dutch_string_to_float(dutch_string):
    # 1.234,00 to 1234
    dutch_string = dutch_string.replace('.', '')
    dutch_string = dutch_string.replace(',', '.')
    return float(dutch_string)


def import_year_week():
    return models.YearWeek.objects.get(year=2000, week=1)


def download_everything():
    password = input("Type Reinout's password: ")
    s = requests.Session()
    s.post('https://www.trsnens.nl/',
           data={'action': 'login',
                 'login': 'reinout.vanrees',
                 'password': password},
           verify=False)
    export_page = s.get('https://www.trsnens.nl/?page=export',
          verify=False)
    soup = BeautifulSoup(export_page.content)
    user_export_select = soup.find_all(attrs={'name': 'userId'})[0]
    user_ids = [int(tag['value']) for tag in user_export_select.find_all('option')]
    project_export_select = soup.find_all(attrs={'name': 'budgetId'})[0]
    project_ids = [int(tag['value']) for tag in project_export_select.find_all('option')]
    tempdir = tempfile.mkdtemp()
    logger.info("Tempdir: %s", tempdir)
    for user_id in user_ids:
        export = s.post('https://www.trsnens.nl/',
                        params={'page': 'export_4'},
                        data={'userId': user_id,
                              'beginweek': 0,
                              'beginyear': 2000,
                              'endweek': 53,
                              'endyear': 2013},
                        verify=False)
        parts = export.headers['content-disposition'].split('filename="')
        filename = parts[1].rstrip('"')
        output_filename = os.path.join(tempdir, filename)
        open(output_filename, 'wb').write(export.content)
        logger.info("Wrote %s", output_filename)

    for project_id in project_ids:
        export = s.post('https://www.trsnens.nl/',
                        params={'page': 'export_3'},
                        data={'budgetId': project_id,
                              'beginweek': 0,
                              'beginyear': 2000,
                              'endweek': 53,
                              'endyear': 2013},
                        verify=False)
        parts = export.headers['content-disposition'].split('filename="')
        filename = parts[1].rstrip('"')
        output_filename = os.path.join(tempdir, filename)
        open(output_filename, 'wb').write(export.content)
        logger.info("Wrote %s", output_filename)

    # # Person export
    # for form_number in [1, 2]:
    #     export = s.post('https://www.trsnens.nl/',
    #                     params={'page': 'export_%s' % form_number},
    #                     data={'beginweek': 0,
    #                           'beginyear': 2000,
    #                           'endweek': 53,
    #                           'endyear': 2013},
    #                     verify=False)
    #     parts = export.headers['content-disposition'].split('filename="')
    #     filename = parts[1].rstrip('"')
    #     output_filename = os.path.join(tempdir, filename)
    #     open(output_filename, 'wb').write(export.content)
    #     logger.info("Wrote %s", output_filename)

    active_projects_invoices_page = s.get(
        'https://www.trsnens.nl/',
        params={'page': 'invoice_projects'},
        verify=False)
    soup = BeautifulSoup(active_projects_invoices_page.content)
    budget_select = soup.find(id='budgetId')
    active_budget_ids = [int(tag['value']) for tag in budget_select.find_all('option')]

    archived_projects_invoices_page = s.get(
        'https://www.trsnens.nl/',
        params={'page': 'invoice_projects',
                'filter': 'archive'},
        verify=False)
    soup = BeautifulSoup(archived_projects_invoices_page.content)
    budget_select = soup.find(id='budgetId')
    archived_budget_ids = [int(tag['value']) for tag in budget_select.find_all('option')]

    for budget_id in active_budget_ids:
        page = s.get(
            'https://www.trsnens.nl/',
            params={'page': 'invoice_projects',
                    'budgetId': budget_id},
            verify=False)
        soup = BeautifulSoup(page.content)
        filename = 'invoices_%s.html' % budget_id
        open(os.path.join(tempdir, filename), 'w').write(str(soup))

    for budget_id in archived_budget_ids:
        page = s.get(
            'https://www.trsnens.nl/',
            params={'page': 'invoice_projects',
                    'filter': 'archive',
                    'budgetId': budget_id},
            verify=False)
        soup = BeautifulSoup(page.content)
        filename = 'invoices_%s.html' % budget_id
        open(os.path.join(tempdir, filename), 'w').write(str(soup))

    # Hours to work per week
    # page = s.get(
    #     'https://www.trsnens.nl/',
    #     params={'page': 'time_view'},
    #     verify=False)
    # soup = BeautifulSoup(page.content)
    # open(os.path.join(tempdir, HOURS_TO_WORK_FILENAME), 'w').write(str(soup))

    return tempdir


class Command(BaseCommand):
    args = ""
    help = "Import the xls exports from the old TRS"

    def handle(self, *args, **options):
        # basedir = download_everything()
        basedir = '/var/folders/dl/wpghhqhj2bs9bcnn213f1nqw0000gn/T/tmptxwxhw'
        logger.info("Everything downloaded into %s", basedir)

        # Sniffing the dialect
        pattern = basedir + '/*.csv'
        found = glob.glob(pattern)
        if found:
            dialect = csv.Sniffer().sniff(
                open(found[0], encoding='cp1252').read())

        # Project data
        pattern = basedir + '/Totalen per project *.csv'
        found = glob.glob(pattern)
        if found:
            import_project_csv(found[0], dialect)

        # Person data
        hours_to_work_filename = os.path.join(basedir, HOURS_TO_WORK_FILENAME)
        pattern = basedir + '/Totalen per werknemer *.csv'
        found = glob.glob(pattern)
        if found:
            import_person_csv(found[0], dialect, hours_to_work_filename)

        # The booking data per person per project
        pattern = basedir + '/Totalen * per project per week *.csv'
        found = glob.glob(pattern)
        for filename in found:
            import_from_csv(filename, dialect)

        # The project's budget data
        pattern = basedir + '/Totalen project * per werknemer *.csv'
        found = glob.glob(pattern)
        for filename in found:
            import_budget_csv(filename, dialect)

        # The invoices
        pattern = basedir + '/invoices_*.html'
        found = glob.glob(pattern)
        for filename in found:
            import_invoices(filename)


def get_import_user():
    import_user, created = User.objects.get_or_create(
        username='import_user',
        first_name='Automatic',
        last_name='Import')
    return import_user


def import_person_csv(filename, dialect, hours_to_work_filename):
    # First detect ours to work
    hours_per_week = {}
    if os.path.exists(hours_to_work_filename):
        logger.info("Opening %s", hours_to_work_filename)
        soup = BeautifulSoup(open(hours_to_work_filename))
        table = soup.find('table')
        import_user = get_import_user()
        for row in table.find_all('tr')[1:]:
            cells = row.find_all('td')
            name = cells[0].string
            hours_per_week[name] = cells[1].string
        logger.debug("Detected hours to work: %s", hours_per_week)

    logger.info("Opening %s", filename)
    lines = list(csv.reader(open(filename, encoding='cp1252'), dialect))
    import_user = get_import_user()
    START_LINE = 7
    models.PersonChange.objects.filter(added_by=import_user).delete()
    for line in lines[START_LINE:]:
        if not line:
            break
        person_name = line[0]
        target = int(line[11])
        cost_per_day = int(line[13])
        hourly_tariff = round(cost_per_day / 8)
        person = get_person(person_name)
        person_change = get_person_change(person, import_user)
        person_change.standard_hourly_tariff = hourly_tariff
        person_change.target = target
        person_change.hours_per_week = hours_per_week.get(person_name, 0)
        # person.archived = False  # If you're in this list...
        # ^^^ disabled start of 2014
        person_change.save()


def import_project_csv(filename, dialect):
    logger.info("Opening %s", filename)
    lines = list(csv.reader(open(filename, encoding='cp1252'), dialect))
    START_LINE = 6
    for line in lines[START_LINE:]:
        if not line:
            break
        project_code = line[0]
        project = get_project2(project_code)
        project_manager_name = line[2]
        project_manager = get_person(project_manager_name)
        project.contract_amount = line[7]
        project.project_manager = project_manager
        REMARK_COLUMN = 12  # Weird, should be 14?
        remarks = [remark for remark in line[REMARK_COLUMN:]
                   if remark != '' and not
                   (len(remark) == 3 and remark.endswith(',0'))]
        project.remark = '\n'.join(remarks)
        project.save()


def import_budget_csv(filename, dialect):
    logger.info("Opening %s", filename)
    lines = list(csv.reader(open(filename, encoding='cp1252'), dialect))
    import_user = get_import_user()
    project_and_description_string = lines[1][1]
    project_id = project_and_description_string.split(' ')[0]
    project = get_project2(project_id)
    models.BudgetItem.objects.filter(added_by=import_user,
                                     project=project).delete()
    on_budget_line = False
    import_added_date = datetime.date(2000, 1, 1)
    for line in lines:
        if line[0].startswith('Overige kosten'):
            on_budget_line = True
            continue
        if not on_budget_line:
            continue
        if not line[0]:
            break
        description = line[0]
        amount = -1 * int(line[1])
        budget_item = models.BudgetItem(
            project=project,
            description=description,
            amount=amount,
            added_by=import_user,
            added=import_added_date)
        logger.debug("Added on %s: %s = %s",
                     project, description, amount)
        budget_item.save()


def import_invoices(filename):
    logger.info("Importing invoices from %s", filename)
    soup = BeautifulSoup(open(filename))
    budget_select = soup.find(id='budgetId')
    budget_id = filename.split('invoices_')[1].split('.')[0]
    selected_option = budget_select.find('option', attrs={'value': budget_id})
    project_code = selected_option.string
    project = get_project2(project_code)
    import_user = get_import_user()
    models.Invoice.objects.filter(added_by=import_user,
                                  project=project).delete()
    invoices_table = soup.find('table', attrs={'style': 'font-size:7pt;'})
    import_added_date = datetime.date(2000, 1, 1)
    for row in invoices_table.find_all('tr')[1:]:
        cells = row.find_all('td')
        if 'colspan' in cells[0].attrs:
            break
        invoice_date_string = cells[0].string
        dd, mm, yy = invoice_date_string.split('-')
        invoice_date = datetime.date(2000 + int(yy), int(mm), int(dd))
        number = cells[1].string
        if not number:
            logger.error("Invoice without a number! %s", cells)
            number = "GEEN NUMMER"
        description = cells[2].string or "NIET INGEVULD"
        amount_exclusive = dutch_string_to_float(cells[3].string)
        vat = dutch_string_to_float(cells[4].string)
        payed_date_string = cells[6].string
        if not payed_date_string:
            payed = None
        else:
            dd, mm, yy = payed_date_string.split('-')
            payed = datetime.date(2000 + int(yy), int(mm), int(dd))
        invoice = models.Invoice(
            added_by=import_user,
            added=import_added_date,
            project=project,
            date=invoice_date,
            number=number,  # This isn't always a proper unique number, btw.
            description=description,
            amount_exclusive=amount_exclusive,
            vat=vat,
            payed=payed)
        invoice.save()
        logger.debug("Added invoice %s on %s", invoice, project)


def import_from_csv(filename, dialect):
    logger.info("Opening %s", filename)
    lines = list(csv.reader(open(filename, encoding='cp1252'), dialect))
    person_name = lines[NAME_LINE][1]
    person = get_person(person_name)
    logger.debug("Person's name: %s", person_name)
    year_weeks = create_year_week_column_mapping(
        lines[YEAR_LINE], lines[WEEKS_LINE])
    import_user = get_import_user()
    models.Booking.objects.filter(added_by=import_user,
                                  booked_by=person).delete()
    booked_this_year = False
    for line in lines[WEEKS_LINE + 1:]:
        if not line:
            break
        project_code = line[0]
        project_description = line[1]
        project_leader_name = line[2]
        start_date = date_string_to_date(line[3])
        end_date = date_string_to_date(line[4])
        status = line[5]
        hours_available = line[6]
        hourly_tariff = line[8]
        project = get_project(project_code,
                              project_description,
                              project_leader_name,
                              start_date,
                              end_date,
                              status)

        work_assignment = get_work_assignment(project, person)
        work_assignment.hourly_tariff = hourly_tariff
        work_assignment.hours = hours_available
        work_assignment.save()

        # Bookings. The ones added by the import user have already been
        # removed.
        for index, hours in enumerate(line[START_COLUMN:]):
            if hours == '':
                break
            hours = int(hours)
            if not hours:
                continue
            if not year_weeks[index]:
                # Doesn't matter really.
                continue
            if year_weeks[index].year != 2013:
                # Only book in this year
                continue
            booking = models.Booking(booked_by=person,
                                     booked_on=project,
                                     added_by=import_user,
                                     year_week=year_weeks[index],
                                     hours=hours)
            booking.save()
            booked_this_year = True
    if not booked_this_year:
        person.archived = True
        person.save()


def get_work_assignment(project, person):
    (work_assignment,
     created) = models.WorkAssignment.objects.get_or_create(
         assigned_on=project,
         assigned_to=person,
         year_week=import_year_week())
    if created:
        logger.info("Created work assignment of %s on %s", person, project)
    return work_assignment


def get_person(name):
    person, created = models.Person.objects.get_or_create(name=name)
    if created:
        logger.info("Created new person %s", person)
    return person


def get_project(project_code,
                project_description,
                project_leader_name,
                start_date,
                end_date,
                status):
    project, created = models.Project.objects.get_or_create(code=project_code)
    if created:
        logger.info("Created new project %s", project)
    project.description = project_description
    project.project_leader = get_person(project_leader_name)
    project.start = models.YearWeek.objects.filter(
        first_day__lte=start_date).last()
    project.end = models.YearWeek.objects.filter(
        first_day__lte=end_date).last()
    project.archived = (status == 'Archief')
    project.internal = (project_code.lower().startswith('intern'))
    if project.internal:
        project.hidden = True
    else:
        # Set it because sqlite has a 'None' false value too...
        project.hidden = False
    if ('verlof' in project_description.lower() or
        'feestdag' in project_description.lower()):
        project.hourless = True
    else:
        # Set it because sqlite has a 'None' false value too...
        project.hourless = False
    project.save()
    return project


def get_project2(project_code):
    project, created = models.Project.objects.get_or_create(code=project_code)
    if created:
        logger.info("Created new project %s", project)
    return project


def get_person_change(person, import_user):
    (person_change,
     created) = models.PersonChange.objects.get_or_create(
         person=person,
         added_by=import_user,
         year_week=import_year_week())
    if created:
        logger.info("Created person change for %s", person)
    return person_change


def create_year_week_column_mapping(year_line, weeks_line):
    result = []
    year_line = year_line[START_COLUMN:]
    weeks_line = weeks_line[START_COLUMN:]
    year = None
    for year_from_line, week in itertools.zip_longest(year_line, weeks_line):
        if year_from_line:
            year = year_from_line
        if week == '':
            continue
        try:
            result.append(models.YearWeek.objects.get(
                year=int(year), week=int(week)))
        except models.YearWeek.DoesNotExist:
            # Doesn't really matter.
            result.append(None)
    return result
