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
    @classmethod
    def start_date(cls, start_year: int = None, day: int = 1) -> dt.datetime:
        if start_year is None:
            start_year = cls.current_start_year()
        date = dt.datetime(year=start_year, month=9, day=day)

        if date.isoweekday() < 5:
            return date
        else:
            return cls.start_date(start_year, day+1)

    @classmethod
    def end_date(cls, end_year: int = None, day: int = 21) -> dt.datetime:
        if end_year is None:
            end_year = cls.current_end_year()

        date = dt.datetime(year=end_year, month=6, day=day)

        if date.isoweekday() == 5:
            return date
        else:
            return cls.end_date(end_year, day+1)

    @classmethod
    def current_start_year(cls) -> int:
        today_date = dt.datetime.today()
        end_date = cls.end_date(today_date.year-1)
        timedelta = end_date - today_date

        if timedelta.days < 0:
            return today_date.year
        else:
            return today_date.year - 1

    @classmethod
    def current_end_year(cls) -> int:
        return cls.current_start_year() + 1

    @classmethod
    def days_passed(cls) -> int:
        timedelta = dt.datetime.today() - cls.start_date()
        return timedelta.days

    @classmethod
    def days_left(cls) -> int:
        timedelta = cls.end_date() - dt.datetime.today()
        return timedelta.days

    @classmethod
    def length(cls) -> int:
        timedelta = cls.end_date() - cls.start_date()
        return timedelta.days

    @classmethod
    def fraction_passed(cls) -> float:
        fraction = cls.days_passed() / cls.length()
        return fraction

    @classmethod
    def fraction_left(cls) -> float:
        fraction = cls.days_left() / cls.length()
        return fraction

    @classmethod
    def is_ongoing(cls) -> bool:
        timedelta = cls.start_date() - dt.datetime.today()
        if timedelta.days < 0:
            return True
        else:
            return False


@somsiad.bot.group(aliases=['rokszkolny', 'ilejeszcze'], invoke_without_command=True)
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def school_year(ctx):
    """Says how much of the school year is left."""
    days_passed = SchoolYear.days_passed()
    days_left = SchoolYear.days_left()

    if days_left // 7 == 0:
        description = None
    elif days_left % 7 == 0:
        description = f'To {TextFormatter.word_number_variant(days_left // 7, "tydzień", "tygodnie", "tygodni")}.'
    else:
        description = (
            f'To {TextFormatter.word_number_variant(days_left // 7, "tydzień", "tygodnie", "tygodni")} '
            f'i {TextFormatter.word_number_variant(days_left % 7, "dzień", "dni")}.'
        )

    if SchoolYear.is_ongoing():
        embed = discord.Embed(
            title=':books: Do końca roku szkolnego '
            f'{TextFormatter.word_number_variant(days_left, "został", "zostały", "zostało", include_number=False)} '
            f'{TextFormatter.word_number_variant(days_left, "dzień", "dni")}',
            description=description,
            color=somsiad.color
        )
        embed.add_field(
            name='Postęp', value=f'{locale.str(round(SchoolYear.fraction_passed() * 100, 1))}%', inline=False
        )
    else:
        embed = discord.Embed(
            title=':beach: Rok szkolny zacznie się za '
            f'{TextFormatter.word_number_variant(-days_passed, "dzień", "dni")}',
            description=description,
            color=somsiad.color
        )
    embed.add_field(name='Data rozpoczęcia', value=SchoolYear.start_date().strftime('%-d %B %Y'))
    embed.add_field(name='Data zakończenia', value=SchoolYear.end_date().strftime('%-d %B %Y'))

    await ctx.send(ctx.author.mention, embed=embed)
