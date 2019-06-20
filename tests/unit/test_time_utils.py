import datetime
import unittest

# Testing targets
from training_noodles.time_utils import convert_unix_time_to_iso


class TestConvertUnixTimeToIso(unittest.TestCase):
    def test_unix_time_zero(self):
        self.unix_time = 0
        self.expected_iso = '1970-01-01T00:00:00+00:00'

    def test_unix_time_year_2000(self):
        self.unix_time = 946684800
        self.expected_iso = '2000-01-01T00:00:00+00:00'

    def test_unix_time_1G(self):
        self.unix_time = 1000000000
        self.expected_iso = '2001-09-09T01:46:40+00:00'

    def tearDown(self):
        # Convert Unix time to ISO time
        iso_time = convert_unix_time_to_iso(
            self.unix_time, tz=datetime.timezone.utc)

        # Check the expected ISO time
        self.assertEqual(iso_time, self.expected_iso)
