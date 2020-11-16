# Copyright 2019-2020 Twixes

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

import data
from core import cooldown
from utilities import human_datetime, interpret_str_as_datetime, md_link, utc_to_naive_local


class Burning(data.Base, data.ChannelRelated, data.UserRelated):
    confirmation_message_id = data.Column(data.BigInteger, primary_key=True)
    target_message_id = data.Column(data.BigInteger, nullable=False)
    requested_at = data.Column(data.DateTime, nullable=False)
    execute_at = data.Column(data.DateTime, nullable=False)
    has_been_executed = data.Column(data.Boolean, nullable=False, default=False)


class Burn(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.burnings_set_off = set()

    async def set_off_burning(
        self,
        confirmation_message_id: int,
        target_message_id: int,
        channel_id: int,
        user_id: int,
        requested_at: dt.datetime,
        execute_at: dt.datetime,
    ):
        if confirmation_message_id in self.burnings_set_off:
            return
        self.burnings_set_off.add(confirmation_message_id)
        await discord.utils.sleep_until(execute_at.astimezone())
        if confirmation_message_id not in self.burnings_set_off:
            return
        self.burnings_set_off.remove(confirmation_message_id)
        channel = self.bot.get_channel(channel_id)
        try:
            target_message = await channel.fetch_message(target_message_id)
            confirmation_message = await channel.fetch_message(confirmation_message_id)
        except (AttributeError, discord.NotFound):
            pass
        else:
            try:
                await target_message.delete()
            except discord.NotFound:
                pass
            else:
                burning_description = md_link(
                    f'Usunięto twoją wiadomość wysłaną {human_datetime(requested_at)}.', confirmation_message.jump_url
                )
                burning_embed = self.bot.generate_embed('✅', 'Spalono wiadomość', burning_description)
                burning_message = await channel.send(f'<@{user_id}>', embed=burning_embed)
                confirmation_description = md_link(
                    f'Usunięto twoją wiadomość {human_datetime()}.', burning_message.jump_url
                )
                confirmation_embed = self.bot.generate_embed('✅', 'Spalono wiadomość', confirmation_description)
                await confirmation_message.edit(embed=confirmation_embed)
        with data.session(commit=True) as session:
            reminder = session.query(Burning).get(confirmation_message_id)
            reminder.has_been_executed = True

    @commands.Cog.listener()
    async def on_ready(self):
        with data.session() as session:
            for reminder in session.query(Burning).filter(Burning.has_been_executed == False):
                self.bot.loop.create_task(
                    self.set_off_burning(
                        reminder.confirmation_message_id,
                        reminder.target_message_id,
                        reminder.channel_id,
                        reminder.user_id,
                        reminder.requested_at,
                        reminder.execute_at,
                    )
                )

    @commands.command(aliases=['spal'])
    @cooldown()
    @commands.bot_has_permissions(manage_messages=True)
    async def burn(self, ctx, execute_at: interpret_str_as_datetime):
        """Removes the message after a specified mount time."""
        confirmation_description = (
            md_link(f'**Zostanie ona usunięta {human_datetime(execute_at)}.**', ctx.message.jump_url)
            + '\n*Spalenie zostanie anulowane jeśli usuniesz tę wiadomość. Możesz to zrobić przy użyciu komendy `nie`.*'
        )
        confirmation_embed = self.bot.generate_embed('🔥', f'Spalę twoją wiadomość', confirmation_description)
        confirmation_message = await self.bot.send(ctx, embed=confirmation_embed)
        if confirmation_message is None:
            return
        try:
            details = {
                'confirmation_message_id': confirmation_message.id,
                'target_message_id': ctx.message.id,
                'channel_id': ctx.channel.id,
                'user_id': ctx.author.id,
                'requested_at': utc_to_naive_local(ctx.message.created_at),
                'execute_at': execute_at,
            }
            with data.session(commit=True) as session:
                reminder = Burning(**details)
                session.add(reminder)
                self.bot.loop.create_task(self.set_off_burning(**details))
        except:
            await confirmation_message.delete()
            raise

    @burn.error
    async def burn_error(self, ctx, error):
        notice = None
        if isinstance(error, commands.MissingRequiredArgument):
            notice = 'Nie podano daty i godziny/liczby minut'
        elif isinstance(error, commands.BadArgument):
            notice = 'Nie rozpoznano poprawnej daty i godziny/liczby minut'
        elif isinstance(error, commands.BotMissingPermissions):
            notice = 'Bot nie ma wymaganych do tego uprawnień (zarządzanie wiadomościami)'
        if notice is not None:
            await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', notice))


def setup(bot: commands.Bot):
    bot.add_cog(Burn(bot))
