# Copyright 2019 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import unittest
import datetime as dt
import utilities


class TestInterpretStrAsDatetime(unittest.TestCase):
    NOW_OVERRIDE = dt.datetime(2013, 12, 24, 12, 0)

    def test_format_1(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = utilities.interpret_str_as_datetime('24.12.2013T18:00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_1_hour_separator_period(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = utilities.interpret_str_as_datetime('24.12.2013T18.00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_1_date_separator_hyphen(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = utilities.interpret_str_as_datetime('24-12-2013T18:00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_1_date_separator_slash(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = utilities.interpret_str_as_datetime('24/12/2013T18:00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_2(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = utilities.interpret_str_as_datetime('24.12T18:00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_2_rollover(self):
        expected_datetime = dt.datetime(2014, 11, 24, 18, 0).astimezone()
        intepreted_datetime = utilities.interpret_str_as_datetime('24.11T18:00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_3(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = utilities.interpret_str_as_datetime('24T18:00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_3_rollover(self):
        expected_datetime = dt.datetime(2014, 1, 23, 18, 0).astimezone()
        intepreted_datetime = utilities.interpret_str_as_datetime('23T18:00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_4(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = utilities.interpret_str_as_datetime('18:00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_4_rollover(self):
        expected_datetime = dt.datetime(2013, 12, 25, 10, 0).astimezone()
        intepreted_datetime = utilities.interpret_str_as_datetime('10:00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)


if __name__ == '__main__':
    unittest.main()
