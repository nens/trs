from django.test import TestCase

from trs.templatetags.trs_formatting import money
from trs.templatetags.trs_formatting import hours


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
