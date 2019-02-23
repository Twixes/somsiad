# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import asyncio
import locale
import datetime as dt
from typing import Optional, Union
import discord
from somsiad import somsiad
from utilities import TextFormatter


def str_to_datetime(argument: str) -> dt.datetime:
    try:
        datetime = dt.datetime.strptime(argument, '%d.%mT%H:%M')
        now_datetime = dt.datetime.now()
        datetime = datetime.replace(year=now_datetime.year)
    except ValueError:
        try:
            datetime = dt.datetime.strptime(argument, '%dT%H:%M')
            now_datetime = dt.datetime.now()
            datetime = datetime.replace(year=now_datetime.year, month=now_datetime.month)
        except ValueError:
            datetime = dt.datetime.strptime(argument, '%H:%M')
            now_datetime = dt.datetime.now()
            datetime = datetime.replace(year=now_datetime.year, month=now_datetime.month, day=now_datetime.day)
    return datetime.astimezone()


@somsiad.bot.command(aliases=['spal'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def burn(ctx, countdown_time: Optional[Union[int, locale.atoi, str_to_datetime]] = 300):
    """Removes the message after a specified mount time."""
    try:
        init_datetime = dt.datetime.now().astimezone()

        if isinstance(countdown_time, int):
            countdown_seconds = int(countdown_time)
            embed = discord.Embed(
                title=':fire: Twoja wiadomość zostanie usunięta za '
                f'{TextFormatter.hours_minutes_seconds(countdown_seconds)}',
                color=somsiad.color
            )
        elif isinstance(countdown_time, dt.datetime):
            timedelta = countdown_time - init_datetime
            countdown_seconds = timedelta.total_seconds()
            embed = discord.Embed(
                title=f':fire: Twoja wiadomość zostanie usunięta {TextFormatter.time_difference(countdown_time)}',
                color=somsiad.color
            )
        else:
            raise TypeError(f'countdown_time must be int or datetime.datetime, not {type(countdown_time).__name__}')

        if countdown_seconds < 3.0:
            raise ValueError('time until closing cannot be below 3 seconds')
        elif countdown_seconds > 1209600.0:
            raise ValueError('time until closing cannot be over 2 weeks')

        notice = await ctx.send(ctx.author.mention, embed=embed)

        await asyncio.sleep(countdown_seconds)
        try:
            await ctx.message.delete()
            await notice.delete()
        except discord.Forbidden:
            warning_embed = discord.Embed(
                title=':warning: Bot nie usunął wiadomości, bo nie ma uprawnień do zarządzania wiadomościami '
                'na kanale!',
                color=somsiad.color
            )
            await ctx.send(ctx.author.mention, embed=warning_embed)
    except ValueError as e:
        if str(e) == 'time until closing cannot be below 3 seconds':
            embed = discord.Embed(
                title=':warning: Odliczanie do zamknięcia kanału nie może trwać poniżej 3 sekund!',
                color=somsiad.color
            )
        elif str(e) == 'time until closing cannot be over 2 weeks':
            embed = discord.Embed(
                title=':warning: Odliczanie do zamknięcia kanału nie może trwać powyżej 2 tygodni!',
                color=somsiad.color
            )
        await ctx.send(ctx.author.mention, embed=embed)
