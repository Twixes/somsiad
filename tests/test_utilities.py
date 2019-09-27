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
import locale
from utilities import TextFormatter, interpret_str_as_datetime
from run import setlocale

NOW_OVERRIDE = dt.datetime(2013, 12, 24, 12, 0)

setlocale()

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


class TestTextFormatterLimitTextLength(unittest.TestCase):
    def test_limit_1_under(self):
        cut_text = TextFormatter.limit_text_length('This string is too long, it needs to be cut.', 18)
        expected_cut_text = 'This string is…'
        self.assertEqual(cut_text, expected_cut_text)

    def test_limit_from_exact_to_5_over(self):
        expected_cut_text = 'This string is too…'
        for limit in (19 + leeway for leeway in range(6)):
            with self.subTest(limit=limit):
                cut_text = TextFormatter.limit_text_length('This string is too long, it needs to be cut.', limit)
                self.assertEqual(cut_text, expected_cut_text)

    def test_end_on_comma(self):
        cut_text = TextFormatter.limit_text_length('This string is too long, it needs to be cut.', 25)
        expected_cut_text = 'This string is too long…'
        self.assertEqual(cut_text, expected_cut_text)

    def test_end_on_semicolon(self):
        cut_text = TextFormatter.limit_text_length('This string is too long; it needs to be cut.', 25)
        expected_cut_text = 'This string is too long;…'
        self.assertEqual(cut_text, expected_cut_text)

    def test_end_on_period(self):
        cut_text = TextFormatter.limit_text_length('This string is too long. It needs to be cut.', 25)
        expected_cut_text = 'This string is too long.…'
        self.assertEqual(cut_text, expected_cut_text)

    def test_first_word_too_long(self):
        cut_text = TextFormatter.limit_text_length('This string is too long, it needs to be cut.', 4)
        expected_cut_text = '…'
        self.assertEqual(cut_text, expected_cut_text)

    def test_no_cutting(self):
        cut_text = TextFormatter.limit_text_length('This string is not too long, it doesn\'t need to be cut.', 420)
        expected_cut_text = 'This string is not too long, it doesn\'t need to be cut.'
        self.assertEqual(cut_text, expected_cut_text)

    def test_no_text(self):
        cut_text = TextFormatter.limit_text_length('', 16)
        expected_cut_text = ''
        self.assertEqual(cut_text, expected_cut_text)


class TestTextFormatterWithPrepositionVariant(unittest.TestCase):
    def test_positive_numbers_starting_with_1_hundred(self):
        for number in [base * 1000**power for power in range(3) for base in (100, 199)]:
            with self.subTest(number=number):
                returned_with_preposition_variant = TextFormatter.with_preposition_variant(number)
                self.assertEqual(returned_with_preposition_variant, 'ze')

    def test_numbers_negative_or_not_starting_with_1_hundred(self):
        for number in [0] + [
            base * 1000**power for power in range(3) for base in (-999, -200, -199, -100, -99, -1, 1, 99, 200, 999)
        ]:
            with self.subTest(number=number):
                returned_with_preposition_variant = TextFormatter.with_preposition_variant(number)
                self.assertEqual(returned_with_preposition_variant, 'z')


class TestTextFormatterWordNumberVariant(unittest.TestCase):
    _SIGNS = (-1, 1)
    _BASES = (0, 100, 200, 1000, 1100, 11000)

    def test_singular_noun(self):
        returned_variant_with_number = TextFormatter.word_number_variant(1, 'klocek', 'klocki', 'klocków')
        expected_variant_with_number = '1 klocek'
        self.assertEqual(returned_variant_with_number, expected_variant_with_number)

    def test_singular_noun_without_number(self):
        returned_variant_without_number = TextFormatter.word_number_variant(
            1, 'klocek', 'klocki', 'klocków', include_number=False
        )
        expected_variant_without_number = 'klocek'
        self.assertEqual(returned_variant_without_number, expected_variant_without_number)

    def test_plural_noun_2_to_4(self):
        for number in (
            sign * (base + addition)
            for base in self._BASES
            for addition in range(2, 5)
            for sign in self._SIGNS
        ):
            with self.subTest(number=number):
                returned_variant_with_number = TextFormatter.word_number_variant(number, 'klocek', 'klocki', 'klocków')
                expected_variant_with_number = f'{number} klocki'
                self.assertEqual(returned_variant_with_number, expected_variant_with_number)

    def test_plural_noun_5_to_1(self):
        for number in (
            sign * (base + addition)
            for base in self._BASES
            for addition in list(range(5, 10)) + ([0, 1] if base != 0 else [0])
            for sign in self._SIGNS
        ):
            with self.subTest(number=number):
                returned_variant_with_number = TextFormatter.word_number_variant(number, 'klocek', 'klocki', 'klocków')
                expected_variant_with_number = f'{number} klocków'
                self.assertEqual(returned_variant_with_number, expected_variant_with_number)

    def test_plural_noun_12_to_14(self):
        for number in (
            sign * (base + addition)
            for base in self._BASES
            for addition in list(range(12, 15))
            for sign in self._SIGNS
        ):
            with self.subTest(number=number):
                returned_variant_with_number = TextFormatter.word_number_variant(number, 'klocek', 'klocki', 'klocków')
                expected_variant_with_number = f'{number} klocków'
                self.assertEqual(returned_variant_with_number, expected_variant_with_number)

    def test_fractional_noun(self):
        for number in (
            sign * (base + addition + 0.5)
            for base in self._BASES
            for addition in range(100)
            for sign in self._SIGNS
        ):
            with self.subTest(number=number):
                returned_variant_with_number = TextFormatter.word_number_variant(
                    number, 'klocek', 'klocki', 'klocków', 'klocka'
                )
                expected_variant_with_number = f'{locale.str(number)} klocka'
                self.assertEqual(returned_variant_with_number, expected_variant_with_number)

    def test_singular_verb(self):
        returned_variant_with_number = TextFormatter.word_number_variant(1, 'skoczył', 'skoczyło')
        expected_variant_with_number = '1 skoczył'
        self.assertEqual(returned_variant_with_number, expected_variant_with_number)

    def test_plural_verb(self):
        for number in (
            sign * (base + addition)
            for base in self._BASES
            for addition in list(range(2, 100)) + [0]
            for sign in self._SIGNS
        ):
            with self.subTest(number=number):
                returned_variant_with_number = TextFormatter.word_number_variant(number, 'skoczył', 'skoczyło')
                expected_variant_with_number = f'{number} skoczyło'
                self.assertEqual(returned_variant_with_number, expected_variant_with_number)


class TestTextFormatterTimeDifference(unittest.TestCase):
    def test_singular_day_n_days_ago(self):
        for n in range(3, 8):
            with self.subTest(n=n):
                returned_time_difference = TextFormatter.time_difference(
                    NOW_OVERRIDE - dt.timedelta(n), naive=False, now_override=NOW_OVERRIDE
                )
                expected_time_difference = f'{24 - n} grudnia 2013 o 12:00, {n} dni temu'
                self.assertEqual(returned_time_difference, expected_time_difference)

    def test_singular_day_before_yesterday(self):
        returned_time_difference = TextFormatter.time_difference(
            NOW_OVERRIDE - dt.timedelta(2), naive=False, now_override=NOW_OVERRIDE
        )
        expected_time_difference = f'22 grudnia 2013 o 12:00, przedwczoraj'
        self.assertEqual(returned_time_difference, expected_time_difference)

    def test_singular_yesterday(self):
        returned_time_difference = TextFormatter.time_difference(
            NOW_OVERRIDE - dt.timedelta(1), naive=False, now_override=NOW_OVERRIDE
        )
        expected_time_difference = f'23 grudnia 2013 o 12:00, wczoraj'
        self.assertEqual(returned_time_difference, expected_time_difference)

    def test_singular_today(self):
        returned_time_difference = TextFormatter.time_difference(
            NOW_OVERRIDE, naive=False, now_override=NOW_OVERRIDE
        )
        expected_time_difference = f'24 grudnia 2013 o 12:00, dzisiaj'
        self.assertEqual(returned_time_difference, expected_time_difference)

    def test_singular_today_no_date(self):
        returned_time_difference = TextFormatter.time_difference(
            NOW_OVERRIDE, naive=False, date=False, now_override=NOW_OVERRIDE
        )
        expected_time_difference = f'12:00, dzisiaj'
        self.assertEqual(returned_time_difference, expected_time_difference)

    def test_singular_today_no_time(self):
        returned_time_difference = TextFormatter.time_difference(
            NOW_OVERRIDE, naive=False, time=False, now_override=NOW_OVERRIDE
        )
        expected_time_difference = f'24 grudnia 2013, dzisiaj'
        self.assertEqual(returned_time_difference, expected_time_difference)

    def test_singular_today_no_name_month(self):
        returned_time_difference = TextFormatter.time_difference(
            NOW_OVERRIDE, naive=False, name_month=False, now_override=NOW_OVERRIDE
        )
        expected_time_difference = f'24.12.2013 o 12:00, dzisiaj'
        self.assertEqual(returned_time_difference, expected_time_difference)

    def test_singular_today_no_days_difference(self):
        returned_time_difference = TextFormatter.time_difference(
            NOW_OVERRIDE, naive=False, days_difference=False, now_override=NOW_OVERRIDE
        )
        expected_time_difference = f'24 grudnia 2013 o 12:00'
        self.assertEqual(returned_time_difference, expected_time_difference)

    def test_singular_tomorrow(self):
        returned_time_difference = TextFormatter.time_difference(
            NOW_OVERRIDE + dt.timedelta(1), naive=False, now_override=NOW_OVERRIDE
        )
        expected_time_difference = f'25 grudnia 2013 o 12:00, jutro'
        self.assertEqual(returned_time_difference, expected_time_difference)

    def test_singular_tomorrow_less_than_24_hours_later(self):
        returned_time_difference = TextFormatter.time_difference(
            NOW_OVERRIDE + dt.timedelta(hours=16), naive=False, now_override=NOW_OVERRIDE
        )
        expected_time_difference = f'25 grudnia 2013 o 4:00, jutro'
        self.assertEqual(returned_time_difference, expected_time_difference)

    def test_singular_day_after_tomorrow(self):
        returned_time_difference = TextFormatter.time_difference(
            NOW_OVERRIDE + dt.timedelta(2), naive=False, now_override=NOW_OVERRIDE
        )
        expected_time_difference = f'26 grudnia 2013 o 12:00, pojutrze'
        self.assertEqual(returned_time_difference, expected_time_difference)

    def test_singular_day_in_n_days(self):
        for n in range(3, 8):
            with self.subTest(n=n):
                returned_time_difference = TextFormatter.time_difference(
                    NOW_OVERRIDE + dt.timedelta(n), naive=False, now_override=NOW_OVERRIDE
                )
                expected_time_difference = f'{24 + n} grudnia 2013 o 12:00, za {n} dni'
                self.assertEqual(returned_time_difference, expected_time_difference)


class TestTextFormatterHumanReadableTime(unittest.TestCase):
    def test_timedelta(self):
        returned_human_readable_time = TextFormatter.human_readable_time(dt.timedelta(days=3, hours=9, minutes=3, seconds=1))
        expected_human_readable_time = '3 d 9 h 3 min 1 s'
        self.assertEqual(returned_human_readable_time, expected_human_readable_time)

    def test_timedelta_with_microseconds(self):
        returned_human_readable_time = TextFormatter.human_readable_time(dt.timedelta(days=3, hours=9, minutes=3, seconds=1, microseconds=909303))
        expected_human_readable_time = '3 d 9 h 3 min 2 s'
        self.assertEqual(returned_human_readable_time, expected_human_readable_time)

    def test_seconds(self):
        returned_human_readable_time = TextFormatter.human_readable_time(86400 + 3600 + 60 + 1.25)
        expected_human_readable_time = '1 d 1 h 1 min 1 s'
        self.assertEqual(returned_human_readable_time, expected_human_readable_time)

    def test_seconds_exactly_one_day(self):
        returned_human_readable_time = TextFormatter.human_readable_time(86400)
        expected_human_readable_time = '1 d'
        self.assertEqual(returned_human_readable_time, expected_human_readable_time)

    def test_zero(self):
        returned_human_readable_time = TextFormatter.human_readable_time(0)
        expected_human_readable_time = '0 s'
        self.assertEqual(returned_human_readable_time, expected_human_readable_time)


class TestTextFormatterSeparator(unittest.TestCase):
    def test_without_datetime(self):
        returned_separator = TextFormatter.separator('=*', with_datetime=False, width=60, now_override=NOW_OVERRIDE)
        expected_separator = '=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*'
        self.assertEqual(returned_separator, expected_separator)

    def test_with_datetime(self):
        returned_separator = TextFormatter.separator('=*', width=60, now_override=NOW_OVERRIDE)
        expected_separator = '=*=*=2013-12-24T12:00:00=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*'
        self.assertEqual(returned_separator, expected_separator)


class TestInterpretStrAsDatetime(unittest.TestCase):
    def test_format_1(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('24.12.2013T18:00', now_override=NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_1_hour_separator_period(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('24.12.2013T18.00', now_override=NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_1_date_separator_hyphen(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('24-12-2013T18:00', now_override=NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_1_date_separator_slash(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('24/12/2013T18:00', now_override=NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_2(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('24.12T18:00', now_override=NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_2_rollover(self):
        expected_datetime = dt.datetime(2014, 11, 24, 18, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('24.11T18:00', now_override=NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_3(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('24T18:00', now_override=NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_3_rollover(self):
        expected_datetime = dt.datetime(2014, 1, 23, 18, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('23T18:00', now_override=NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_4(self):
        expected_datetime = dt.datetime(2013, 12, 24, 18, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('18:00', now_override=NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)

    def test_format_4_rollover(self):
        expected_datetime = dt.datetime(2013, 12, 25, 10, 0).astimezone()
        intepreted_datetime = interpret_str_as_datetime('10:00', now_override=NOW_OVERRIDE)
        self.assertEqual(intepreted_datetime, expected_datetime)


if __name__ == '__main__':
    unittest.main()
