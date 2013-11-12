from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.auth.models import AnonymousUser

from trs.views import BaseMixin


class BaseMixinTestCase(TestCase):

    def setUp(self):
        self.view = BaseMixin()

    def test_today(self):
        self.assertTrue(self.view.today)

    def test_active_project_is_iterable(self):
        # if no one is logged in, we should be iterable, too.
        self.view.request = RequestFactory().get('/')
        self.view.request.user = AnonymousUser()
        self.assertEqual(self.view.active_projects, [])
