from django.test import TestCase
import mock

from trs.templatetags.trs_formatting import money
from trs.templatetags.trs_formatting import hours
from trs.templatetags.trs_formatting import tabindex


class MoneyTestCase(TestCase):

    def test_wrong_type(self):
        value = 'some string, could be <script>dangerous</script>'
        self.assertEqual(money(value), value)

    def test_formatting(self):
        value = 12.34
        self.assertEqual(money(value), '<tt>12</tt>')


class HoursTestCase(TestCase):

    def test_wrong_type(self):
        value = 'some string, could be <script>dangerous</script>'
        self.assertEqual(hours(value), value)

    def test_formatting(self):
        value = 12.34
        self.assertEqual(hours(value), '12')


class TabindexTestCase(TestCase):

    def test_wrong_type(self):
        value = mock.Mock()
        value.field.widget.attrs = {}
        result = tabindex(value, 42)
        self.assertEqual(result.field.widget.attrs['tabindex'], 42)
