# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import datetime as dt
import locale
import discord
from somsiad import somsiad
from utilities import TextFormatter


class SchoolYear:
    def __init__(self, for_date: dt.date = None):
        self.for_date = dt.date.today() if for_date is None else for_date
        end_date_for_year_of_date = self._find_end_date(self.for_date.year)
        if end_date_for_year_of_date >= self.for_date:
            self.start_date = self._find_start_date(self.for_date.year-1)
            self.end_date = end_date_for_year_of_date
        else:
            self.start_date = self._find_start_date(self.for_date.year)
            self.end_date = self._find_end_date(self.for_date.year+1)

    def days_passed(self) -> int:
        timedelta = self.for_date - self.start_date
        return timedelta.days

    def days_left(self) -> int:
        timedelta = self.end_date - self.for_date
        return timedelta.days

    def length(self) -> int:
        timedelta = self.end_date - self.start_date
        return timedelta.days

    def fraction_passed(self) -> float:
        fraction = self.days_passed() / self.length()
        return fraction

    def fraction_left(self) -> float:
        fraction = self.days_left() / self.length()
        return fraction

    def is_ongoing(self) -> bool:
        timedelta = self.start_date - self.for_date
        return timedelta.days < 0

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

        return date


def present_days_as_weeks(number_of_days: int):
    if number_of_days // 7 == 0:
        return None
    elif number_of_days % 7 == 0:
        return f'To {TextFormatter.word_number_variant(number_of_days // 7, "tydzień", "tygodnie", "tygodni")}.'
    else:
        return (
            f'To {TextFormatter.word_number_variant(number_of_days // 7, "tydzień", "tygodnie", "tygodni")} '
            f'i {TextFormatter.word_number_variant(number_of_days % 7, "dzień", "dni")}.'
        )


@somsiad.bot.group(aliases=['rokszkolny', 'ilejeszcze'], invoke_without_command=True)
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def school_year(ctx):
    """Says how much of the school year is left."""
    school_year = SchoolYear()
    print(school_year.days_left())
    print(school_year.days_passed())
    if school_year.is_ongoing():
        days_left = school_year.days_left()
        if days_left == 0:
            embed = discord.Embed(
                title=':tada: Dziś zakończenie roku szkolnego',
                color=somsiad.color
            )
        else:
            embed = discord.Embed(
                title=':books: Do końca roku szkolnego '
                f'{TextFormatter.word_number_variant(days_left, "został", "zostały", "zostało", include_number=False)} '
                f'{TextFormatter.word_number_variant(days_left, "dzień", "dni")}',
                description=present_days_as_weeks(days_left),
                color=somsiad.color
            )
            embed.add_field(name='Postęp', value=f'{locale.str(round(school_year.fraction_passed() * 100, 1))}%')
    else:
        days_passed = school_year.days_passed()
        if days_passed == 0:
            embed = discord.Embed(
                title=':chains: Dziś rozpoczęcie roku szkolnego',
                color=somsiad.color
            )
        else:
            embed = discord.Embed(
                title=':beach: Rok szkolny zacznie się za '
                f'{TextFormatter.word_number_variant(-days_passed, "dzień", "dni")}',
                description=present_days_as_weeks(-days_passed),
                color=somsiad.color
            )

    embed.add_field(name='Data rozpoczęcia', value=school_year.start_date.strftime('%-d %B %Y'))
    embed.add_field(name='Data zakończenia', value=school_year.end_date.strftime('%-d %B %Y'))

    await ctx.send(ctx.author.mention, embed=embed)
