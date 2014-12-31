from django.test import TestCase
import mock

from trs.templatetags.trs_formatting import money
from trs.templatetags.trs_formatting import moneydiff
from trs.templatetags.trs_formatting import money_with_decimal
from trs.templatetags.trs_formatting import hours
from trs.templatetags.trs_formatting import hoursdiff
from trs.templatetags.trs_formatting import tabindex


class MoneyTestCase(TestCase):

    def test_wrong_type(self):
        value = 'some string, could be <script>dangerous</script>'
        self.assertEqual(money(value), value)

    def test_formatting(self):
        value = 12.34
        self.assertEqual(money(value), '<tt>12</tt>')

    def test_negative_formatting(self):
        value = -12.34
        self.assertEqual(money(value), '<tt>-12</tt>')


class MoneyDiffTestCase(TestCase):

    def test_wrong_type(self):
        value = 'some string, could be <script>dangerous</script>'
        self.assertEqual(moneydiff(value), value)

    def test_positive_formatting(self):
        value = 12.34
        self.assertEqual(moneydiff(value), '<tt>+12</tt>')

    def test_negative_formatting(self):
        value = -12.34
        self.assertEqual(moneydiff(value), '<tt>-12</tt>')


class MoneyWithDecimalTestCase(TestCase):

    def test_wrong_type(self):
        value = 'some string, could be <script>dangerous</script>'
        self.assertEqual(money_with_decimal(value), value)

    def test_formatting(self):
        value = 12.35
        self.assertEqual(money_with_decimal(value), '<tt>12,35</tt>')

    def test_negative_formatting(self):
        value = -12.35
        self.assertEqual(money_with_decimal(value), '<tt>-12,35</tt>')

    def test_negative_formatting2(self):
        value = -3309.60
        self.assertEqual(money_with_decimal(value), '<tt>-3.309,60</tt>')


class HoursTestCase(TestCase):

    def test_wrong_type(self):
        value = 'some string, could be <script>dangerous</script>'
        self.assertEqual(hours(value), value)

    def test_formatting(self):
        value = 12.34
        self.assertEqual(hours(value), '12')


class HoursDiffTestCase(TestCase):

    def test_wrong_type(self):
        value = 'some string, could be <script>dangerous</script>'
        self.assertEqual(hoursdiff(value), value)

    def test_positive_formatting(self):
        value = 12
        self.assertEqual(hoursdiff(value), '+12')

    def test_negative_formatting(self):
        value = -12
        self.assertEqual(hoursdiff(value), '-12')


class TabindexTestCase(TestCase):

    def test_wrong_type(self):
        value = mock.Mock()
        value.field.widget.attrs = {}
        result = tabindex(value, 42)
        self.assertEqual(result.field.widget.attrs['tabindex'], 42)
