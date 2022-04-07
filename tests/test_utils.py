import unittest

from frost_sta_client.utils import parse_datetime
import datetime


class TestUtils(unittest.TestCase):

    def test_parse_iso_time_with_timezone(self):
        parsedtime = parse_datetime('2022-04-07T14:00:00+02:00')
        self.assertEqual('2022-04-07T14:00:00+02:00', parsedtime)

    def test_parse_iso_time(self):
        parsedtime = parse_datetime('2022-04-07T14:00:00Z')
        self.assertEqual('2022-04-07T14:00:00+00:00', parsedtime)

    def test_parse_interval(self):
        parsedtime = parse_datetime('2022-04-07T14:00:00Z/2022-04-07T15:00:00Z')
        self.assertEqual('2022-04-07T14:00:00+00:00/2022-04-07T15:00:00+00:00', parsedtime)

    def test_parse_interval_with_timezone_offset(self):
        parsedtime = parse_datetime('2022-04-07T14:00:00+02:00/2022-04-07T15:00:00+02:00')
        self.assertEqual('2022-04-07T14:00:00+02:00/2022-04-07T15:00:00+02:00', parsedtime)

