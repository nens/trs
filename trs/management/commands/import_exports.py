import csv
import datetime
import glob
import itertools
import logging
import os
import tempfile

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
import requests

from trs import models

logger = logging.getLogger(__name__)

NAME_LINE = 1
YEAR_LINE = 6
WEEKS_LINE = 7
START_COLUMN = 10


def date_string_to_date(date_string):
    # dd-mm-yyyy
    day = int(date_string[0:2])
    month = int(date_string[3:5])
    year = int(date_string[6:])
    return datetime.date(year, month, day)


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
    s.get('https://www.trsnens.nl/?page=export',
          verify=False)
    hardcoded_userids = [101,
                         104,
                         105,
                         122,
                         123,
                         124,
                         125,
                         139,
                         143,
                         147,
                         148,
                         149,
                         152,
                         153,
                         155,
                         158,
                         165,
                         169,
                         180,
                         184,
                         186,
                         187,
                         188,
                         189,
                         192,
                         193,
                         196,
                         198,
                         204,
                         206,
                         211,
                         215,
                         217,
                         220,
                         223,
                         225,
                         226,
                         227,
                         231,
                         232,
                         233,
                         234,
                         235,
                         236,
                         237,
                         238,
                         239,
                         240,
                         241,
                         242,
                         243,
                         244,
                         245,
                         246,
                         247,
                         248,
                         249,
                         250,
                         251,
                         252,
                         253,
                         254,
                         255,
                         256,
                         257,
                         258,
                         259,
                         260,
                         261,
                         262,
                         263,
                         264,
                         265,
                         266,
                         267,
                         268,
                         269,
                         27,
                         270,
                         271,
                         272,
                         273,
                         31,
                         41,
                         42,
                         43,
                         46,
                         48,
                         49,
                         50,
                         51,
                         52,
                         53,
                         54,
                         55,
                         56,
                         6,
                         61,
                         62,
                         63,
                         68,
                         76,
                         81,
                         99,
                         ]
    tempdir = tempfile.mkdtemp()
    logger.info("Tempdir: %s", tempdir)
    for hardcoded_userid in hardcoded_userids:
        export = s.post('https://www.trsnens.nl/',
                        params={'page': 'export_4'},
                        data={'userId': hardcoded_userid,
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
    return tempdir


class Command(BaseCommand):
    args = ""
    help = "Import the xls exports from the old TRS"

    def handle(self, *args, **options):
        basedir = download_everything()
        # prepare_tls_request()
        pattern = basedir + '/Totalen * per project per week *.csv'
        found = glob.glob(pattern)
        dialect = csv.Sniffer().sniff(open(found[0], encoding='cp1252').read())
        for filename in found:
            import_from_csv(filename, dialect)


def import_from_csv(filename, dialect):
    logger.info("Opening %s", filename)
    lines = list(csv.reader(open(filename, encoding='cp1252'), dialect))
    person_name = lines[NAME_LINE][1]
    person = get_person(person_name)
    logger.debug("Person's name: %s", person_name)
    year_weeks = create_year_week_column_mapping(
        lines[YEAR_LINE], lines[WEEKS_LINE])
    import_user, created = User.objects.get_or_create(
        username='import_user',
        first_name='Automatic',
        last_name='Import')
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
                logger.warn("Year week at index %s doesn't exist", index)
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
    project.save()
    return project


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
            logger.warn("Week %s-%s does not exist", year, week)
            result.append(None)
    return result
