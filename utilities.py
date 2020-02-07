# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Union, Optional, Sequence
from numbers import Number
from collections import namedtuple
import locale
import calendar
import re
import datetime as dt
import numpy as np

DatetimeFormat = namedtuple('DatetimeFormat', ('format', 'imply_year', 'imply_month', 'imply_day'))

DATETIME_FORMATS = (
    DatetimeFormat('%d.%m.%YT%H.%M', False, False, False),
    DatetimeFormat('%d.%mT%H.%M', True, False, False),
    DatetimeFormat('%dT%H.%M', True, True, False),
    DatetimeFormat('%H.%M', True, True, True)
)
ACCEPTED_LOCALES = ('pl_PL.utf8', 'pl_PL.UTF-8')
URL_REGEX = re.compile(r'(https?://[\S]+\.[\S]+)')


def first_url(string: str) -> Optional[str]:
    """Return the first well-formed URL found in the string."""
    search_result = URL_REGEX.search(string)
    return search_result.group().rstrip('()[{]};:\'",<.>') if search_result is not None else None


def text_snippet(text: str, limit: int) -> str:
    """Return the text limited in length to the specified number of characters."""
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
                cut_text += ' ' + word
            else:
                break
        return cut_text.rstrip(',') + '…'
    return '…'


def with_preposition_form(number: Number) -> str:
    """Return the gramatically correct form of the "with" preposition in Polish."""
    while number > 1000: number /= 1000
    return 'ze' if 100 <= number < 200 else 'z'


def word_number_form(
        number: Number, singular_form: str, plural_form: str, plural_form_5_to_1: str = None,
        fractional_form: str = None, *, include_number: bool = True, include_with: bool = False
) -> str:
    """Return the gramatically correct form of the specifiec word in Polish based on the number."""
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
        parts.append(with_preposition_form(number))
    if include_number:
        parts.append(f'{number:n}')
    parts.append(proper_form)

    return ' '.join(parts)


def human_timedelta(
        datetime: dt.datetime, *, naive: bool = True, date: bool = True, time: bool = True,
        days_difference: bool = True, name_month: bool = True, now_override: dt.datetime = None
) -> str:
    """Return the difference between the provided datetime and now in Polish."""
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
            time_difference_parts.append(f'{word_number_form(-timedelta.days, "dzień", "dni")} temu')
        else:
            time_difference_parts.append(f'za {word_number_form(timedelta.days, "dzień", "dni")}')

    return ', '.join(time_difference_parts)


def human_amount_of_time(time: Union[dt.timedelta, Number]) -> str:
    """Return the provided amoutt of in Polish."""
    if isinstance(time, dt.timedelta):
        total_seconds = int(round(time.total_seconds()))
    elif isinstance(time, Number):
        total_seconds = int(round(time))
    else:
        raise TypeError('time must be datetime.timedelta or numbers.Number')

    if total_seconds == 0.0:
        return '0 s'

    days = total_seconds // 86400
    total_seconds -= days * 86400
    hours = total_seconds // 3600
    total_seconds -= hours * 3600
    minutes = total_seconds // 60
    total_seconds -= minutes * 60
    seconds = total_seconds
    information = []
    if days >= 1:
        information.append(f'{days:n} d')
    if hours >= 1:
        information.append(f'{hours:n} h')
    if minutes >= 1:
        information.append(f'{minutes:n} min')
    if seconds >= 1:
        information.append(f'{seconds:n} s')

    return ' '.join(information)


def days_as_weeks(number_of_days: int, none_if_no_weeks: bool = True) -> Optional[str]:
    number_of_weeks, number_of_leftover_days = divmod(number_of_days, 7)
    if number_of_weeks == 0:
        return None if none_if_no_weeks else word_number_form(number_of_leftover_days, 'dzień', 'dni')
    elif number_of_leftover_days == 0:
        return word_number_form(number_of_weeks, 'tydzień', 'tygodnie', 'tygodni')
    else:
        return (
            f'{word_number_form(number_of_weeks, "tydzień", "tygodnie", "tygodni")} '
            f'i {word_number_form(number_of_leftover_days, "dzień", "dni")}'
        )


def interpret_str_as_datetime(string: str, roll_over: str = True, now_override: dt.datetime = None) -> dt.datetime:
    """Interpret the provided string as a datetime."""
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


def rolling_average(data: Sequence[Number], roll: int, pad_mode: str = 'constant') -> np.ndarray:
    data = np.pad(data, roll // 2, pad_mode)
    data = np.cumsum(data)
    data[roll:] = data[roll:] - data[:-roll]
    data = data[roll - 1:] / roll
    return data


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
