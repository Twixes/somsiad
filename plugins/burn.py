# Copyright 2019 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Optional, Union
import asyncio
import locale
import datetime as dt
import discord
from core import somsiad
from utilities import human_amount_of_time, human_timedelta, interpret_str_as_datetime
from configuration import configuration


@somsiad.command(aliases=['spal'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def burn(ctx, countdown_time: Optional[Union[int, locale.atoi, interpret_str_as_datetime]] = 300):
    """Removes the message after a specified mount time."""
    if isinstance(countdown_time, int):
        countdown_seconds = int(countdown_time)
        if countdown_seconds < 3.0:
            countdown_seconds = 3.0
        elif countdown_seconds > 1209600.0:
            countdown_seconds = 1209600.0
        embed_before = discord.Embed(
            title=':fire: Twoja wiadomość zostanie usunięta za '
            f'{human_amount_of_time(countdown_seconds)}',
            color=somsiad.COLOR
        )
        embed_after = discord.Embed(
            title=':white_check_mark: Twoja wiadomość została usunięta po '
            f'{human_amount_of_time(countdown_seconds)}',
            color=somsiad.COLOR
        )
    elif isinstance(countdown_time, dt.datetime):
        now = dt.datetime.now().astimezone()
        countdown_timedelta = countdown_time - now
        countdown_seconds = countdown_timedelta.total_seconds()
        if countdown_seconds < 3.0:
            countdown_seconds = 3.0
        elif countdown_seconds > 1209600.0:
            countdown_seconds = 1209600.0
        bound_countdown_datetime = (
            dt.datetime.now() + dt.timedelta(seconds=countdown_seconds)
        )
        embed_before = discord.Embed(
            title=':fire: Twoja wiadomość zostanie usunięta '
            f'{human_timedelta(bound_countdown_datetime, naive=False, days_difference=False)}',
            color=somsiad.COLOR
        )
        embed_after = discord.Embed(
            title=':white_check_mark: Twoja wiadomość została usunięta '
            f'{human_timedelta(bound_countdown_datetime, naive=False, days_difference=False)}',
            color=somsiad.COLOR
        )
    else:
        raise TypeError(f'countdown_time must be int or datetime.datetime, not {type(countdown_time).__name__}')

    notice = await ctx.send(ctx.author.mention, embed=embed_before)

    await asyncio.sleep(countdown_seconds)
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        embed_warning = discord.Embed(
            title=':warning: Bot nie usunął wiadomości wysłanej '
            f'{human_timedelta(ctx.message.created_at, days_difference=False)}, '
            'bo nie ma uprawnień do zarządzania wiadomościami na kanale!',
            color=somsiad.COLOR
        )
        await ctx.send(ctx.author.mention, embed=embed_warning)
    else:
        await notice.edit(embed=embed_after)
