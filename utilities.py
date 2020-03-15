# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Union, Optional, Sequence, Tuple
from numbers import Number
from dataclasses import dataclass
import asyncio
import locale
import calendar
import re
import datetime as dt
import numpy as np
from googleapiclient.discovery import build


@dataclass
class DatetimeFormat:
    format: str
    imply_year: bool = False
    imply_month: bool = False
    imply_day: bool = False


DHMS_REGEX = re.compile(
    r'^(?!$)(?:(?P<days>(?:\d+(?:[.,]\d*)?)|(?:[.,]\d*))d)?'
    r'(?:(?P<hours>(?:\d+(?:[.,]\d*)?)|(?:[.,]\d*))[hg])?'
    r'(?:(?P<minutes>(?:\d+(?:[.,]\d*)?)|(?:[.,]\d*))m(?:in)?)?'
    r'(?:(?P<seconds>(?:\d+(?:[.,]\d*)?)|(?:[.,]\d*))s(?:ec)?)?$'
)
DATETIME_FORMATS = (
    DatetimeFormat('%d.%m.%YT%H.%M'),
    DatetimeFormat('%d.%m.%yT%H.%M'),
    DatetimeFormat('%d.%mT%H.%M', True),
    DatetimeFormat('%dT%H.%M', True, True),
    DatetimeFormat('%H.%M', True, True, True)
)
URL_REGEX = re.compile(r'(https?:\/\/\S+\.\S+)')
URL_REGEX_PROTOCOL_SEPARATE = re.compile(r'(?:(\w+):\/\/)?(\S+\.\S+)')


class GoogleClient:
    FOOTER_TEXT = 'Google'
    FOOTER_ICON_URL = 'https://www.google.com/favicon.ico'

    @dataclass
    class GoogleResult:
        title: str
        snippet: str
        source_link: str
        display_link: str
        root_link: str
        image_link: Optional[str]
        type: str

    def __init__(self, developer_key: str, custom_search_engine_id: str, loop: asyncio.AbstractEventLoop):
        self.custom_search_engine_id = custom_search_engine_id
        self.search_client = build('customsearch', 'v1', developerKey=developer_key).cse()
        self.loop = loop

    async def search(
            self, query: str, *, language: str = 'pl', safe: str = 'active', search_type: str = None
    ) -> Optional[GoogleResult]:
        query = self.search_client.list(
            q=query, cx=self.custom_search_engine_id, hl=language, num=5 if search_type == 'image' else 1, safe=safe,
            searchType=search_type
        )
        results = await self.loop.run_in_executor(None, query.execute)
        if results['searchInformation']['totalResults'] != '0':
            if search_type == 'image':
                for result in results['items']:
                    if not result['link'] or result['link'].startswith('x-raw-image'):
                        continue
                    return self.GoogleResult(
                        result['title'], result['snippet'], result['image']['contextLink'], result['displayLink'],
                        f'{result["link"].split("://")[0]}://{result["displayLink"]}', result['link'], search_type
                    )
            else:
                result = results['items'][0]
                try:
                    image_link = result['pagemap']['cse_image'][0]['src']
                except KeyError:
                    image_link = None
                return self.GoogleResult(
                    result['title'], result['snippet'], result['link'], result['displayLink'],
                    f'{result["link"].split("://")[0]}://{result["displayLink"]}', image_link, search_type
                )
        return None


class YouTubeClient:
    FOOTER_ICON_URL = (
        'https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/'
        'YouTube_full-color_icon_%282017%29.svg/60px-YouTube_full-color_icon_%282017%29.svg.png'
    )
    FOOTER_TEXT = 'YouTube'

    @dataclass
    class YouTubeResult:
        id: str
        title: str
        url: str
        thumbnail_url: str

    def __init__(self, developer_key: str, loop: asyncio.AbstractEventLoop):
        self.search_client = build('youtube', 'v3', developerKey=developer_key).search()
        self.loop = loop

    async def search(self, query: str) -> Optional[YouTubeResult]:
        query = self.search_client.list(q=query, part='snippet', maxResults=1, type='video')
        response = await self.loop.run_in_executor(None, query.execute)
        items = response.get('items')
        if not items:
            return None
        video_id = items[0]['id']['videoId']
        return self.YouTubeResult(
            video_id, items[0]['snippet']['title'], f'https://www.youtube.com/watch?v={video_id}',
            items[0]['snippet']['thumbnails']['medium']['url']
        )


def first_url(string: str, *, protocol_separate: bool = False) -> Union[str, Tuple[Optional[str], Optional[str]]]:
    """Return the first well-formed URL found in the string."""
    if protocol_separate:
        search_result = URL_REGEX_PROTOCOL_SEPARATE.search(string)
        if search_result is None:
            return None, None
        else:
            return tuple((
                part.lower().rstrip('()[{]};:\'",<.>') if part is not None else None for part in search_result.groups()
            ))
    else:
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
        number: Union[Number, str], singular_form: str, plural_form: str, plural_form_5_to_1: str = None,
        fractional_form: str = None, *, include_number: bool = True, include_with: bool = False
) -> str:
    """Return the gramatically correct form of the specifiec word in Polish based on the number."""
    if isinstance(number, str):
        return f'{number} {plural_form_5_to_1 or plural_form}'
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


def utc_to_naive_local(datetime: dt.datetime) -> dt.datetime:
    if datetime.tzinfo == dt.timezone.utc:
        return datetime.astimezone().replace(tzinfo=None)
    elif datetime.tzinfo is None:
        return datetime.replace(tzinfo=dt.timezone.utc).astimezone().replace(tzinfo=None)
    else:
        raise ValueError('datetime is neither naive nor UTC-aware')


def human_datetime(
        datetime: Optional[dt.datetime] = None, *, utc: bool = False, date: bool = True, time: bool = True,
        days_difference: bool = True, name_month: bool = True, now_override: dt.datetime = None
) -> str:
    """Return the difference between the provided datetime and now in Polish."""
    if datetime is None:
        datetime = dt.datetime.now()
    else:
        datetime = datetime if not utc else utc_to_naive_local(datetime)
    time_difference_parts = []

    if date or time:
        datetime_parts = []
        if date:
            if name_month:
                datetime_parts.append(datetime.strftime('%-d %B %Y'))
            else:
                datetime_parts.append(datetime.strftime('%-d.%m.%Y'))
        if time:
            datetime_parts.append(datetime.strftime('%-H:%M'))
        time_difference_parts.append(' o '.join(datetime_parts))

    if days_difference:
        timedelta = datetime.date() - (dt.date.today() if now_override is None else now_override.date())
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


def interpret_str_as_datetime(
        string: str, roll_over: bool = True, now_override: dt.datetime = None, years_in_future_limit: Optional[int] = 5
) -> dt.datetime:
    """Interpret the provided string as a datetime."""
    now = now_override or dt.datetime.now()
    string = string.replace(',', '.')
    timedelta_arguments = {}
    # string as numbers of minute strategy
    try:
        timedelta_arguments['minutes'] = float(string)
    except ValueError:
        pass
    # string as custom 'dhms' format strategy
    match = DHMS_REGEX.match(string)
    if match is not None:
        for group, value in match.groupdict().items():
            if value is None:
                continue
            try:
                timedelta_arguments[group] = float(value)
            except ValueError:
                timedelta_arguments.clear()
                break
    if any(timedelta_arguments.values()):
        datetime = now + dt.timedelta(**timedelta_arguments)
        if years_in_future_limit is not None and datetime > now.replace(year=now.year+years_in_future_limit):
            raise ValueError
    else:
        # string as datetime strategy
        string = string.replace('-', '.').replace('/', '.').replace(':', '.').strip('T')
        for datetime_format in DATETIME_FORMATS:
            try:
                datetime = dt.datetime.strptime(string, datetime_format.format)
            except ValueError:
                continue
            else:
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
    return datetime


def calculate_age(birth_date: dt.date, at_date: Optional[dt.date] = None) -> int:
    at_date = at_date or dt.date.today()
    age = at_date.year - birth_date.year
    if (at_date.month, at_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    elif (2, 29) == (at_date.month, at_date.day) == (birth_date.month, birth_date.day):
        age //= 4
    return age


def md_link(text: str, url: str) -> str:
    return f'[{text}]({url})'


def rolling_average(data: Sequence[Number], roll: int, pad_mode: str = 'constant') -> np.ndarray:
    data = np.pad(data, roll // 2, pad_mode)
    data = np.cumsum(data)
    data[roll:] = data[roll:] - data[:-roll]
    data = data[roll - 1:] / roll
    return data


def setlocale(accepted_locales: Sequence[str] = ('pl_PL.utf8', 'pl_PL.UTF-8')):
    """Set program locale and first day of the week."""
    for accepted_locale in accepted_locales:
        try:
            locale.setlocale(locale.LC_ALL, accepted_locale)
        except locale.Error:
            continue
        else:
            break
    else:
        raise Exception(
            f'no locale from the list of accepted ones ({", ".join(accepted_locales)}) was found in the system'
        )

    return calendar.setfirstweekday(calendar.MONDAY)
