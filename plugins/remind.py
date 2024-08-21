# Copyright 2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import datetime as dt
import re
from typing import List, Optional
from sqlalchemy.dialects import postgresql

from sentry_sdk import capture_exception
from somsiad import Somsiad

import discord
from discord.ext import commands

import data
from core import cooldown
from utilities import human_datetime, interpret_str_as_datetime, md_link, utc_to_naive_local


class Reminder(data.Base, data.ChannelRelated, data.UserRelated):
    MAX_CONTENT_LENGTH = 100

    confirmation_message_id = data.Column(data.BigInteger, primary_key=True)
    content = data.Column(data.String(MAX_CONTENT_LENGTH), nullable=False)
    extra_mentions = data.Column(postgresql.ARRAY(data.String(30)), nullable=True)
    requested_at = data.Column(data.DateTime, nullable=False)
    execute_at = data.Column(data.DateTime, nullable=False)
    has_been_executed = data.Column(data.Boolean, nullable=False, default=False)


class Remind(commands.Cog):
    def __init__(self, bot: Somsiad):
        self.bot = bot
        self.reminders_set_off = set()

    async def set_off_reminder(
        self,
        confirmation_message_id: int,
        channel_id: int,
        user_id: int,
        content: str,
        extra_mentions: Optional[List[str]],
        requested_at: dt.datetime,
        execute_at: dt.datetime,
    ):
        if confirmation_message_id in self.reminders_set_off:
            return
        self.reminders_set_off.add(confirmation_message_id)
        try:
            await discord.utils.sleep_until(execute_at.astimezone())
        except ValueError:
            capture_exception()
            return
        if confirmation_message_id not in self.reminders_set_off:
            return
        self.reminders_set_off.remove(confirmation_message_id)
        channel = await self.bot.fetch_channel(channel_id)
        try:
            confirmation_message = await channel.fetch_message(confirmation_message_id)
        except (AttributeError, discord.NotFound):
            pass
        else:
            confirmation_message.mentions
            reminder_description = md_link(
                f'Przypomnienie z {human_datetime(requested_at)}.', confirmation_message.jump_url
            )
            reminder_embed = self.bot.generate_embed('🍅', content, reminder_description, timestamp=execute_at)
            mentions = [str(user_id)]
            if extra_mentions:
                for id in extra_mentions:
                    if id not in mentions:
                        mentions.append(id)
            mentions_joined = ', '.join([f'<@{mention}>' for mention in mentions])
            reminder_message = await channel.send(mentions_joined, embed=reminder_embed)
            confirmation_description = md_link(
                f'Przypomniano ci tutaj "{content}" {human_datetime()}.', reminder_message.jump_url
            )
            confirmation_embed = self.bot.generate_embed('🍅', 'Zrealizowano przypomnienie', confirmation_description, timestamp=execute_at)
            await confirmation_message.edit(embed=confirmation_embed)
        with data.session(commit=True) as session:
            reminder = session.query(Reminder).get(confirmation_message_id)
            reminder.has_been_executed = True

    @commands.Cog.listener()
    async def on_ready(self):
        with data.session() as session:
            for reminder in session.query(Reminder).filter(Reminder.has_been_executed == False):
                self.bot.loop.create_task(
                    self.set_off_reminder(
                        reminder.confirmation_message_id,
                        reminder.channel_id,
                        reminder.user_id,
                        reminder.content,
                        reminder.extra_mentions,
                        reminder.requested_at,
                        reminder.execute_at,
                    )
                )

    @cooldown()
    @commands.command(aliases=['przypomnij', 'przypomnienie', 'pomidor'])
    async def remind(
        self, ctx: commands.Context, execute_at: interpret_str_as_datetime, *, content: commands.clean_content(fix_channel_mentions=True)
    ):
        if len(content) > Reminder.MAX_CONTENT_LENGTH:
            raise commands.BadArgument
        description = (
            f'**Przypomnę ci tutaj "{content}" {human_datetime(execute_at)}.**\n*Przypomnienie zostanie anulowane '
            'jeśli usuniesz tę wiadomość (możesz zrobić to komendą `nie`).*'
        )
        embed = self.bot.generate_embed('🍅', 'Ustawiono przypomnienie', description, timestamp=execute_at)
        confirmation_message = await self.bot.send(ctx, embed=embed)
        extra_mentions = re.findall(r"<@((?:!|&)?[0-9]{15,20})>", ctx.message.content)
        if confirmation_message is None:
            return
        try:
            details = {
                'confirmation_message_id': confirmation_message.id,
                'channel_id': ctx.channel.id,
                'content': content,
                'extra_mentions': extra_mentions,
                'user_id': ctx.author.id,
                'requested_at': utc_to_naive_local(ctx.message.created_at),
                'execute_at': execute_at,
            }
            with data.session(commit=True) as session:
                reminder = Reminder(**details)
                session.add(reminder)
                self.bot.loop.create_task(self.set_off_reminder(**details))
        except:
            await confirmation_message.delete()
            raise

    @remind.error
    async def remind_error(self, ctx, error):
        notice = None
        description = None
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'execute_at':
                notice = 'Nie podano daty i godziny/liczby minut'
                description = 'Przykłady: `przypomnij 08.04.2024T16:00 Zaćmienie`, `przypomnij 5min Piekarnik`, `przypomnij 2d12h Premiera filmu`'
            elif error.param.name == 'content':
                notice = 'Nie podano treści przypomnienia'
        elif isinstance(error, commands.BadArgument):
            error_string = str(error)
            if 'execute_at' in error_string:
                notice = 'Nie rozpoznano poprawnej daty i godziny/liczby minut'
                description = 'Przykłady: `przypomnij 08.04.2024T16:00 Zaćmienie`, `przypomnij 5min Piekarnik`, `przypomnij 2d12h Premiera filmu`'
            elif 'content' in error_string:
                notice = 'Treść przypomnienia nie może przekraczać 50 znaków'
        if notice is not None:
            await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', notice, description))


async def setup(bot: Somsiad):
    await bot.add_cog(Remind(bot))
