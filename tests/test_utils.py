import unittest

from frost_sta_client.utils import process_datetime


class TestUtils(unittest.TestCase):

    def test_parse_iso_time_with_timezone(self):
        parsedtime = process_datetime('2022-04-07T14:00:00+02:00')
        self.assertEqual('2022-04-07T14:00:00+02:00', parsedtime)

    def test_parse_iso_time(self):
        parsedtime = process_datetime('2022-04-07T14:00:00Z')
        self.assertEqual('2022-04-07T14:00:00Z', parsedtime)

    def test_parse_interval(self):
        parsedtime = process_datetime('2022-04-07T14:00:00Z/2022-04-07T15:00:00Z')
        self.assertEqual('2022-04-07T14:00:00Z/2022-04-07T15:00:00Z', parsedtime)

    def test_parse_interval_with_timezone_offset(self):
        parsedtime = process_datetime('2022-04-07T14:00:00+02:00/2022-04-07T15:00:00+02:00')
        self.assertEqual('2022-04-07T14:00:00+02:00/2022-04-07T15:00:00+02:00', parsedtime)

if __name__ == '__main__':
    unittest.main()