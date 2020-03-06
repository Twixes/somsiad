# Copyright 2020 Twixes

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
from core import ChannelRelated, UserRelated, cooldown
from utilities import utc_to_naive_local, human_datetime, interpret_str_as_datetime, md_link
import data


class Reminder(data.Base, ChannelRelated, UserRelated):
    MAX_CONTENT_LENGTH = 100

    confirmation_message_id = data.Column(data.BigInteger, primary_key=True)
    content = data.Column(data.String(MAX_CONTENT_LENGTH), nullable=False)
    requested_at = data.Column(data.DateTime, nullable=False)
    execute_at = data.Column(data.DateTime, nullable=False)
    has_been_executed = data.Column(data.Boolean, nullable=False, default=False)


class Remind(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def set_off_reminder(
            self, confirmation_message_id: int, channel_id: int, user_id: int, content: str,
            requested_at: dt.datetime, execute_at: dt.datetime
    ):
        await discord.utils.sleep_until(execute_at.astimezone())
        channel = self.bot.get_channel(channel_id)
        try:
            confirmation_message = await channel.fetch_message(confirmation_message_id)
        except discord.NotFound:
            pass
        else:
            reminder_description = md_link(
                f'Przypomnienie z {human_datetime(requested_at)}.', confirmation_message.jump_url
            )
            reminder_embed = self.bot.generate_embed('🍅', content, reminder_description)
            reminder_message = await channel.send(f'<@{user_id}>', embed=reminder_embed)
            confirmation_description = md_link(
                f'Przypomniano ci tutaj "{content}" {human_datetime()}.', reminder_message.jump_url
            )
            confirmation_embed = self.bot.generate_embed('🍅', 'Zrealizowano przypomnienie', confirmation_description)
            await confirmation_message.edit(embed=confirmation_embed)
        with data.session(commit=True) as session:
            reminder = session.query(Reminder).get(confirmation_message_id)
            reminder.has_been_executed = True

    @commands.Cog.listener()
    async def on_ready(self):
        with data.session() as session:
            for reminder in session.query(Reminder).filter(Reminder.has_been_executed == False):
                self.bot.loop.create_task(self.set_off_reminder(
                    reminder.confirmation_message_id, reminder.channel_id, reminder.user_id,
                    reminder.content, reminder.requested_at, reminder.execute_at
                ))

    @commands.command(aliases=['przypomnij', 'pomidor'])
    @cooldown()
    async def remind(
            self, ctx, execute_at: interpret_str_as_datetime, *,
            content: commands.clean_content(fix_channel_mentions=True)
    ):
        if len(content) > Reminder.MAX_CONTENT_LENGTH:
            raise commands.BadArgument
        description = f'Przypomnę ci tutaj "{content}" {human_datetime(execute_at)}.'
        embed = self.bot.generate_embed('🍅', 'Ustawiono przypomnienie', description)
        confirmation_message = await self.bot.send(ctx, embed=embed)
        try:
            details = {
                'confirmation_message_id': confirmation_message.id, 'channel_id': ctx.channel.id, 'content': content,
                'user_id': ctx.author.id, 'requested_at': utc_to_naive_local(ctx.message.created_at),
                'execute_at': execute_at
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
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'execute_at':
                notice = 'Nie podano daty i godziny/liczby minut'
            elif error.param.name == 'content':
                notice = 'Nie podano treści przypomnienia'
        elif isinstance(error, commands.BadArgument):
            error_string = str(error)
            if 'execute_at' in error_string:
                notice = 'Nie rozpoznano poprawnej daty i godziny/liczby minut'
            elif 'content' in error_string:
                notice = 'Treść przypomnienia nie może przekraczać 50 znaków'
        if notice is not None:
            await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', notice))


def setup(bot: commands.Bot):
    bot.add_cog(Remind(bot))
