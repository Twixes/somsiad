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
from utilities import TextFormatter, interpret_str_as_datetime


class TestTextFormatterFindURL(unittest.TestCase):
    def test_proper_http(self):
        search_result = TextFormatter.find_url('This sentence contains an exemplary URL: http://www.example.com.')
        self.assertEqual(search_result, 'http://www.example.com')

    def test_proper_https(self):
        search_result = TextFormatter.find_url('This sentence contains an exemplary URL: https://www.example.com.')
        self.assertEqual(search_result, 'https://www.example.com')

    def test_proper_no_subdomain(self):
        search_result = TextFormatter.find_url('This sentence contains an exemplary URL: https://example.com.')
        self.assertEqual(search_result, 'https://example.com')

    def test_proper_trailing_slash(self):
        search_result = TextFormatter.find_url('This sentence contains an exemplary URL: https://www.example.com/.')
        self.assertEqual(search_result, 'https://www.example.com/')

    def test_proper_path(self):
        search_result = TextFormatter.find_url(
            'This sentence contains an exemplary URL: https://www.example.com/resource/id.'
        )
        self.assertEqual(search_result, 'https://www.example.com/resource/id')

    def test_proper_comma_after(self):
        search_result = TextFormatter.find_url(
            'This sentence contains an exemplary URL: https://www.example.com, and some rambling.'
        )
        self.assertEqual(search_result, 'https://www.example.com')

    def test_proper_markdown(self):
        search_result = TextFormatter.find_url('This sentence contains an exemplary URL: <https://www.example.com>.')
        self.assertEqual(search_result, 'https://www.example.com')

    def test_proper_markdown_formatted(self):
        search_result = TextFormatter.find_url('This sentence contains [an exemplary URL](https://www.example.com).')
        self.assertEqual(search_result, 'https://www.example.com')

    def test_proper_comma_continuation(self):
        search_result = TextFormatter.find_url(
            'This sentence contains an exemplary URL: https://www.example.com, and some rambling.'
        )
        self.assertEqual(search_result, 'https://www.example.com')

    def test_proper_semicolon_continuation(self):
        search_result = TextFormatter.find_url(
            'This sentence contains an exemplary URL: https://www.example.com; and some rambling.'
        )
        self.assertEqual(search_result, 'https://www.example.com')

    def test_proper_colon_after(self):
        search_result = TextFormatter.find_url('https://www.example.com: An Exemplary URL')
        self.assertEqual(search_result, 'https://www.example.com')

    def test_proper_two_urls(self):
        search_result = TextFormatter.find_url(
            'This sentence contains exemplary URLs: https://one.example.com and https://two.example.com.'
        )
        self.assertEqual(search_result, 'https://one.example.com')

    def test_proper_sentence_after(self):
        search_result = TextFormatter.find_url(
            'This sentence contains an exemplary URL: https://www.example.com. '
            'And this sentence contains no exemplary URL.'
        )
        self.assertEqual(search_result, 'https://www.example.com')

    def test_improper_unspaced_sentence_after(self):
        search_result = TextFormatter.find_url(
            'ThissentencecontainsanexemplaryURL:https://www.example.com.AndthissentencecontainsnoexemplaryURL.'
        )
        self.assertEqual(search_result, 'https://www.example.com.AndthissentencecontainsnoexemplaryURL')

    def test_improper_ftp(self):
        search_result = TextFormatter.find_url('This sentence contains an exemplary URL: ftp://www.example.com.')
        self.assertIsNone(search_result)

    def tesy_improper_no_protocol(self):
        search_result = TextFormatter.find_url('This sentence contains an exemplary URL: www.example.com.')
        self.assertIsNone(search_result)

    def test_improper_no_tld(self):
        search_result = TextFormatter.find_url('This sentence contains an exemplary URL: https://example.')
        self.assertIsNone(search_result)

    def test_improper_no_url(self):
        search_result = TextFormatter.find_url('This sentence contains no exemplary URL.')
        self.assertIsNone(search_result)


class TestInterpretStrAsDatetime(unittest.TestCase):
    NOW_OVERRIDE = dt.datetime(2013, 12, 24, 12, 0)

    def test_format_1(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('24.12.2013T18:00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_1_hour_separator_period(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('24.12.2013T18.00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_1_date_separator_hyphen(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('24-12-2013T18:00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_1_date_separator_slash(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('24/12/2013T18:00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_2(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('24.12T18:00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_2_rollover(self):
        expected_datetime = dt.datetime(2014, 11, 24, 18, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('24.11T18:00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_3(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('24T18:00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_3_rollover(self):
        expected_datetime = dt.datetime(2014, 1, 23, 18, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('23T18:00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_4(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('18:00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_4_rollover(self):
        expected_datetime = dt.datetime(2013, 12, 25, 10, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('10:00', now_override=self.NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)


if __name__ == '__main__':
    unittest.main()
