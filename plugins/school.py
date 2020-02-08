# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import datetime as dt
import discord
from discord.ext import commands
from core import somsiad
from utilities import word_number_form, days_as_weeks
from configuration import configuration


class SchoolPeriod:
    def __init__(self, reference_date: dt.date = None):
        self.reference_date = reference_date or dt.date.today()
        self.is_summer_break = False
        end_date_for_year_of_date = self._find_end_date(self.reference_date.year)
        if end_date_for_year_of_date >= self.reference_date:
            self.start_date = self._find_start_date(self.reference_date.year-1)
            self.end_date = end_date_for_year_of_date
        else:
            self.start_date = self._find_start_date(self.reference_date.year)
            self.end_date = self._find_end_date(self.reference_date.year+1)
        self._calculate_basic_metrics()
        if self.days_passed < 0 or self.days_left < 0:
            self.is_summer_break = True
            self.end_date = self.start_date
            self.start_date = end_date_for_year_of_date
            self._calculate_basic_metrics()
        self._calculate_extra_metrics()

    def _calculate_basic_metrics(self):
        self.length = (self.end_date - self.start_date).days
        self.days_passed = (self.reference_date - self.start_date).days
        self.days_left = self.length - self.days_passed

    def _calculate_extra_metrics(self):
        self.fraction_passed = self.days_passed / self.length
        self.fraction_left = self.days_left / self.length

    @staticmethod
    def _find_start_date(start_year: int) -> dt.date:
        day = 1
        date = dt.date(year=start_year, month=9, day=day)
        while date.isoweekday() >= 5:
            day +=1
            date = dt.date(year=start_year, month=9, day=day)
        return date

    @staticmethod
    def _find_end_date(end_year: int) -> dt.date:
        day = 21
        date = dt.date(year=end_year, month=6, day=day)
        while date.isoweekday() != 5:
            day += 1
            date = dt.date(year=end_year, month=6, day=day)
        if end_year == 2019:
            date -= dt.timedelta(2)
        return date


@somsiad.group(aliases=['rokszkolny', 'wakacje', 'ilejeszcze'], invoke_without_command=True, case_insensitive=True)
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
)
async def how_much_longer(ctx):
    """Says how much of the school year or summer break is left."""
    current_school_period = SchoolPeriod()

    if not current_school_period.is_summer_break:
        if current_school_period.days_left == 0:
            embed = discord.Embed(
                title=':tada: Dziś zakończenie roku szkolnego',
                color=somsiad.COLOR
            )
        elif current_school_period.days_passed == 0:
            embed = discord.Embed(
                title=':chains: Dziś rozpoczęcie roku szkolnego',
                color=somsiad.COLOR
            )
        else:
            days_left_as_weeks = days_as_weeks(current_school_period.days_left)
            embed = discord.Embed(
                title=':books: Do końca roku szkolnego '
                f'{word_number_form(current_school_period.days_left, "został", "zostały", "zostało", include_number=False)} '
                f'{word_number_form(current_school_period.days_left, "dzień", "dni")}',
                description=f'To {days_left_as_weeks}.' if days_left_as_weeks is not None else None,
                color=somsiad.COLOR
            )
            embed.add_field(name='Postęp', value=f'{round(current_school_period.fraction_passed * 100, 1):n}%')
    else:
        days_left_as_weeks = days_as_weeks(current_school_period.days_left)
        embed = discord.Embed(
            title=':beach: Do końca wakacji '
            f'{word_number_form(current_school_period.days_left, "został", "zostały", "zostało", include_number=False)} '
            f'{word_number_form(current_school_period.days_left, "dzień", "dni")}',
            description=f'To {days_left_as_weeks}.' if days_left_as_weeks is not None else None,
            color=somsiad.COLOR
        )
        embed.add_field(
            name='Postęp', value=f'{round(current_school_period.fraction_passed * 100, 1):n}%'
        )

    embed.add_field(name='Data rozpoczęcia', value=current_school_period.start_date.strftime('%-d %B %Y'))
    embed.add_field(name='Data zakończenia', value=current_school_period.end_date.strftime('%-d %B %Y'))

    await somsiad.send(ctx, embed=embed)
