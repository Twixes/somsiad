# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import asyncio
import datetime as dt
import locale
from numbers import Number
from typing import Optional, Union

from discord.ext import commands

from core import cooldown
from utilities import human_amount_of_time, interpret_str_as_datetime


class Closing:
    STEPS = (0, 1, 2, 3, 4, 5, 10, 15, 30, 60, 120, 180, 300, 600, 900, 1800, 3600, 7200, 10800, 21600, 43200, 86400)

    def __init__(self, ctx: commands.Context, countdown_time: Union[Number, dt.datetime]):
        self.init_datetime = dt.datetime.now()
        self.countdown_active = True
        self.ctx = ctx

        if isinstance(countdown_time, Number):
            self.countdown_seconds = float(countdown_time)
            try:
                self.closing_datetime = self.init_datetime + dt.timedelta(seconds=self.countdown_seconds)
            except OverflowError:
                raise ValueError('time until closing cannot be over 2 weeks')
        elif isinstance(countdown_time, dt.datetime):
            timedelta = countdown_time - self.init_datetime
            self.countdown_seconds = timedelta.total_seconds()
            self.closing_datetime = countdown_time
        else:
            raise TypeError(f'countdown_time must be int or datetime.datetime, not {type(countdown_time).__name__}')

        if self.countdown_seconds < 3.0:
            raise ValueError('time until closing cannot be below 3 seconds')
        elif self.countdown_seconds > 1209600.0:
            raise ValueError('time until closing cannot be over 2 weeks')

    async def timeout_handler(self):
        embed = self.ctx.bot.generate_embed(
            '💣',
            f'Kanał zostanie zamknięty za {human_amount_of_time(self.countdown_seconds)}',
            'Napisz STOP by zatrzymać odliczanie.',
            timestamp=self.closing_datetime,
        )
        await self.ctx.send(self.ctx.author.mention, embed=embed)

        def wait_predicate(message):
            return (
                message.channel == self.ctx.channel
                and message.content.strip().strip(',./1!').lower() == 'stop'
                and message.author.permissions_in(self.ctx.channel).manage_channels
            )

        try:
            stop_message = await self.ctx.bot.wait_for('message', check=wait_predicate, timeout=self.countdown_seconds)
        except asyncio.TimeoutError:
            await self.ctx.channel.delete(reason=str(self.ctx.author))
        else:
            self.countdown_active = False
            closing_defusal_timedelta = self.closing_datetime - dt.datetime.now()
            embed = self.ctx.bot.generate_embed(
                '✋',
                'Odliczanie zostało zatrzymane '
                f'{human_amount_of_time(closing_defusal_timedelta.total_seconds())} przed zamknięciem kanału',
                timestamp=self.closing_datetime,
            )
            if stop_message.author.mention == self.ctx.author.mention:
                mentions = stop_message.author.mention
            else:
                mentions = f'{stop_message.author.mention} {self.ctx.author.mention}'
            await self.ctx.send(mentions, embed=embed)

    async def countdown_handler(self):
        next_lower_step_index = self._find_next_lower_step_index()
        await asyncio.sleep(self.countdown_seconds - self.STEPS[next_lower_step_index])
        for step_index in reversed(range(1, next_lower_step_index + 1)):
            if self.countdown_active:
                embed = self.ctx.bot.generate_embed(
                    '💣',
                    f'Kanał zostanie zamknięty za {human_amount_of_time(self.STEPS[step_index])}',
                    'Napisz STOP by zatrzymać odliczanie.',
                    timestamp=self.closing_datetime,
                )
                await self.ctx.send(embed=embed)
                await asyncio.sleep(self.STEPS[step_index] - self.STEPS[step_index - 1])
            else:
                break

    def _find_next_lower_step_index(self) -> int:
        step_index = len(self.STEPS) - 1
        while self.countdown_seconds - self.STEPS[step_index] <= 0:
            step_index -= 1
        return step_index


class Close(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['zamknij'])
    @cooldown()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def close(
        self, ctx, countdown_seconds: Optional[Union[float, locale.atof, interpret_str_as_datetime]] = 3600
    ):
        """Counts down to channel removal."""
        try:
            closing = Closing(ctx, countdown_seconds)
        except ValueError as e:
            notice = None
            if str(e) == 'time until closing cannot be below 3 seconds':
                notice = 'Odliczanie do zamknięcia kanału nie może trwać poniżej 3 sekund'
            elif str(e) == 'time until closing cannot be over 2 weeks':
                notice = 'Odliczanie do zamknięcia kanału nie może trwać powyżej 2 tygodni'
            if notice is not None:
                embed = self.bot.generate_embed('⚠️', notice)
                await self.bot.send(ctx, embed=embed)
        else:
            await asyncio.gather(closing.timeout_handler(), closing.countdown_handler())


def setup(bot: commands.Bot):
    bot.add_cog(Close(bot))
