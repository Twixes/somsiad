# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Optional, Union
import datetime as dt
import locale
import discord
from somsiad import somsiad
from utilities import TextFormatter


class SchoolYear:
    def __init__(self, reference_date: dt.date = None):
        self.reference_date = reference_date or dt.date.today()
        end_date_for_year_of_date = self._find_end_date(self.reference_date.year)
        if end_date_for_year_of_date >= self.reference_date:
            self.start_date = self._find_start_date(self.reference_date.year-1)
            self.end_date = end_date_for_year_of_date
        else:
            self.start_date = self._find_start_date(self.reference_date.year)
            self.end_date = self._find_end_date(self.reference_date.year+1)
        self.length = (self.end_date - self.start_date).days
        self.days_passed = (self.reference_date - self.start_date).days
        self.days_left = self.length - self.days_passed
        self.fraction_passed = self.days_passed / self.length
        self.fraction_left = self.days_left / self.length
        self.is_ongoing = self.days_passed >= 0 and self.days_left >= 0

    def _find_start_date(self, start_year: int) -> dt.date:
        day = 1
        date = dt.date(year=start_year, month=9, day=day)
        while date.isoweekday() >= 5:
            day +=1
            date = dt.date(year=start_year, month=9, day=day)
        return date

    def _find_end_date(self, end_year: int) -> dt.date:
        day = 21
        date = dt.date(year=end_year, month=6, day=day)
        while date.isoweekday() != 5:
            day += 1
            date = dt.date(year=end_year, month=6, day=day)
        if end_year == 2019:
            date -= dt.timedelta(2)
        return date


class SummerBreak:
    def __init__(self, next_school_year: SchoolYear):
        previous_school_year = SchoolYear(dt.date(next_school_year.start_date.year, 1, 1))
        self.start_date = previous_school_year.end_date
        self.end_date = next_school_year.start_date
        self.length = (self.end_date - self.start_date).days
        self.days_passed = (next_school_year.reference_date - self.start_date).days
        self.days_left = self.length - self.days_passed
        self.fraction_passed = self.days_passed / self.length
        self.fraction_left = self.days_left / self.length
        self.is_ongoing = self.days_passed >= 0 and self.days_left >= 0

def get_current_school_time() -> Union[SchoolYear, SummerBreak]:
    school_year = SchoolYear()
    if school_year.is_ongoing:
        print(school_year.fraction_passed + school_year.fraction_left)
        return school_year
    else:
        summer_break = SummerBreak(school_year)
        return summer_break


def present_days_as_weeks(number_of_days: int) -> Optional[str]:
    if number_of_days // 7 == 0:
        return None
    elif number_of_days % 7 == 0:
        return f'To {TextFormatter.word_number_variant(number_of_days // 7, "tydzień", "tygodnie", "tygodni")}.'
    else:
        return (
            f'To {TextFormatter.word_number_variant(number_of_days // 7, "tydzień", "tygodnie", "tygodni")} '
            f'i {TextFormatter.word_number_variant(number_of_days % 7, "dzień", "dni")}.'
        )


@somsiad.bot.group(aliases=['rokszkolny', 'wakacje', 'ilejeszcze'], invoke_without_command=True, case_insensitive=True)
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def how_much_more(ctx):
    """Says how much of the school year or summer break is left."""
    current_school_time = get_current_school_time()

    if isinstance(current_school_time, SchoolYear):
        current_school_year = current_school_time
        if current_school_year.days_left == 0:
            embed = discord.Embed(
                title=':tada: Dziś zakończenie roku szkolnego',
                color=somsiad.COLOR
            )
        elif current_school_year.days_passed == 0:
            embed = discord.Embed(
                title=':chains: Dziś rozpoczęcie roku szkolnego',
                color=somsiad.COLOR
            )
        else:
            embed = discord.Embed(
                title=':books: Do końca roku szkolnego '
                f'{TextFormatter.word_number_variant(current_school_year.days_left, "został", "zostały", "zostało", include_number=False)} '
                f'{TextFormatter.word_number_variant(current_school_year.days_left, "dzień", "dni")}',
                description=present_days_as_weeks(current_school_year.days_left),
                color=somsiad.COLOR
            )
            embed.add_field(name='Postęp', value=f'{locale.str(round(current_school_year.fraction_passed * 100, 1))}%')
    else:
        current_summber_break = current_school_time
        embed = discord.Embed(
            title=':beach: Do końca wakacji '
            f'{TextFormatter.word_number_variant(current_summber_break.days_left, "został", "zostały", "zostało", include_number=False)} '
            f'{TextFormatter.word_number_variant(current_summber_break.days_left, "dzień", "dni")}',
            description=present_days_as_weeks(current_summber_break.days_left),
            color=somsiad.COLOR
        )
        embed.add_field(
            name='Postęp', value=f'{locale.str(round(current_summber_break.fraction_passed * 100, 1))}%'
        )

    embed.add_field(name='Data rozpoczęcia', value=current_school_time.start_date.strftime('%-d %B %Y'))
    embed.add_field(name='Data zakończenia', value=current_school_time.end_date.strftime('%-d %B %Y'))

    await ctx.send(ctx.author.mention, embed=embed)
