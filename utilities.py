# Copyright 2018-2019 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Union
import locale
import calendar
import re
from collections import namedtuple
import datetime as dt
from numbers import Number

ACCEPTED_LOCALES = ('pl_PL.utf8', 'pl_PL.UTF-8')


class TextFormatter:
    """Text formatting utilities."""
    _URL_REGEX = re.compile(r'(https?://[\S]+\.[\S]+)')

    @classmethod
    def find_url(cls, string: str) -> str:
        """Returns the first well-formed URL found in the string."""
        search_result = cls._URL_REGEX.search(string)
        return search_result.group().rstrip('()[{]};:\'",<.>') if search_result is not None else None

    @staticmethod
    def limit_text_length(text: str, limit: int) -> str:
        if not text:
            return ''
        stripped_text = text.strip()
        if len(stripped_text) <= limit:
            return stripped_text
        words = stripped_text.split()
        if limit > len(words[0]):
            cut_text = words[0]
            for word in words[1:]:
                if len(cut_text) + 1 + len(word) < limit:
                    cut_text = f'{cut_text} {word}'
                else:
                    break
            return cut_text.rstrip(',') + '…'
        return '…'

    @staticmethod
    def with_preposition_variant(number: Number) -> str:
        """Returns the gramatically correct variant of the 'with' preposition in Polish."""
        while number > 1000:
            number /= 1000
        return 'ze' if 100 <= number < 200 else 'z'

    @classmethod
    def word_number_variant(
            cls, number: Number, singular_form: str, plural_form: str, plural_form_5_to_1: str = None,
            fractional_form: str = None, *, include_number: bool = True, include_with: bool = False
    ) -> str:
        """Returns the gramatically correct variant of the given word in Polish."""
        absolute_number = abs(number)
        absolute_number_floored = int(absolute_number)

        if fractional_form is not None and absolute_number != absolute_number_floored:
            proper_form = fractional_form
        else:
            absolute_number = absolute_number_floored
            if absolute_number == 1:
                proper_form = singular_form
            elif absolute_number % 10 in (2, 3, 4) and absolute_number % 100 not in (12, 13, 14):
                proper_form = plural_form
            else:
                if plural_form_5_to_1 is not None:
                    proper_form = plural_form_5_to_1
                else:
                    proper_form = plural_form

        parts = []
        if include_with:
            parts.append(cls.with_preposition_variant(number))
        if include_number:
            parts.append(locale.str(number))
        parts.append(proper_form)

        return ' '.join(parts)

    @classmethod
    def time_difference(
            cls, datetime: dt.datetime, *, naive=True, date=True, time=True, days_difference=True,
            name_month=True, now_override: dt.datetime = None
    ) -> str:
        """Returns the difference between the provided datetime and now as text in Polish."""
        local_datetime = datetime.replace(tzinfo=dt.timezone.utc).astimezone() if naive else datetime.astimezone()

        time_difference_parts = []

        if date or time:
            datetime_parts = []
            if date:
                if name_month:
                    datetime_parts.append(local_datetime.strftime('%-d %B %Y'))
                else:
                    datetime_parts.append(local_datetime.strftime('%-d.%m.%Y'))
            if time:
                datetime_parts.append(local_datetime.strftime('%-H:%M'))
            time_difference_parts.append(' o '.join(datetime_parts))

        if days_difference:
            timedelta = local_datetime.date()
            timedelta -= dt.date.today() if now_override is None else now_override.date()
            if timedelta.days == -2:
                time_difference_parts.append('przedwczoraj')
            elif timedelta.days == -1:
                time_difference_parts.append('wczoraj')
            elif timedelta.days == 0:
                time_difference_parts.append('dzisiaj')
            elif timedelta.days == 1:
                time_difference_parts.append('jutro')
            elif timedelta.days == 2:
                time_difference_parts.append('pojutrze')
            elif timedelta.days < 0:
                time_difference_parts.append(f'{cls.word_number_variant(-timedelta.days, "dzień", "dni")} temu')
            else:
                time_difference_parts.append(f'za {cls.word_number_variant(timedelta.days, "dzień", "dni")}')

        return ', '.join(time_difference_parts)

    @staticmethod
    def human_readable_time(time: Union[dt.timedelta, Number]) -> str:
        information = []

        if isinstance(time, dt.timedelta):
            total_seconds = int(round(time.total_seconds()))
        elif isinstance(time, Number):
            total_seconds = int(round(time))
        else:
            raise TypeError('time must be datetime.timedelta or numbers.Number')

        if total_seconds == 0.0:
            information.append(f'0 s')
        else:
            days = total_seconds // 86400
            total_seconds -= days * 86400
            hours = total_seconds // 3600
            total_seconds -= hours * 3600
            minutes = total_seconds // 60
            total_seconds -= minutes * 60
            seconds = total_seconds
            if days >= 1:
                information.append(f'{days} d')
            if hours >= 1:
                information.append(f'{hours} h')
            if minutes >= 1:
                information.append(f'{minutes} min')
            if seconds >= 1:
                information.append(f'{seconds} s')

        return ' '.join(information)


def interpret_str_as_datetime(string: str, roll_over: str = True, now_override: dt.datetime = None) -> dt.datetime:
    DatetimeFormat = namedtuple('DatetimeFormat', ('format', 'imply_year', 'imply_month', 'imply_day'))
    DATETIME_FORMATS = (
        DatetimeFormat('%d.%m.%YT%H.%M', False, False, False),
        DatetimeFormat('%d.%mT%H.%M', True, False, False),
        DatetimeFormat('%dT%H.%M', True, True, False),
        DatetimeFormat('%H.%M', True, True, True)
    )
    string = string.replace('-', '.').replace('/', '.').replace(':', '.')
    for datetime_format in DATETIME_FORMATS:
        try:
            datetime = dt.datetime.strptime(string, datetime_format.format)
        except ValueError:
            continue
        else:
            now = now_override or dt.datetime.now()
            if datetime_format.imply_day:
                datetime = datetime.replace(day=now.day)
            if datetime_format.imply_month:
                datetime = datetime.replace(month=now.month)
            if datetime_format.imply_year:
                datetime = datetime.replace(year=now.year)
            if roll_over and datetime < now:
                # if implied date is in the past, roll it over so it's not
                if datetime_format.imply_day:
                    datetime += dt.timedelta(1)
                elif datetime_format.imply_month:
                    if now.month == 12:
                        datetime = datetime.replace(year=now.year+1, month=1)
                    else:
                        datetime = datetime.replace(month=now.month+1)
                elif datetime_format.imply_year:
                    datetime = datetime.replace(year=now.year+1)
            break
    else:
        raise ValueError
    return datetime.astimezone()


def setlocale(locale_index: int = 0):
    """Set program locale and first day of the week."""
    try:
        locale.setlocale(locale.LC_ALL, ACCEPTED_LOCALES[locale_index])
    except locale.Error:
        return setlocale(locale_index + 1)
    except IndexError:
        raise Exception(
            f'no locale from the list of accepted ones ({", ".join(ACCEPTED_LOCALES)}) was found in the system'
        )
    return calendar.setfirstweekday(calendar.MONDAY)
