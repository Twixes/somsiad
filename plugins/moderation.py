# Copyright 2018–2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import datetime as dt
from typing import List, Union
from math import ceil

import discord
import psycopg2.errors
from discord.ext import commands

import data
from core import cooldown, has_permissions
from somsiad import Somsiad
from utilities import text_snippet, word_number_form


class Event(data.Base, data.MemberRelated, data.ChannelRelated):
    MAX_DETAILS_LENGTH = 1000

    id = data.Column(data.BigInteger, primary_key=True)
    type = data.Column(data.String(50), nullable=False)
    executing_user_id = data.Column(data.BigInteger, index=True)
    details = data.Column(data.String(MAX_DETAILS_LENGTH))
    occurred_at = data.Column(data.DateTime, nullable=False, default=dt.datetime.now)

    async def get_presentation(self, bot: commands.Bot) -> str:
        type_presentation = '???'
        if self.type == 'warned':
            type_presentation = 'Ostrzeżenie'
        elif self.type == 'kicked':
            type_presentation = 'Wyrzucenie'
        elif self.type == 'banned':
            type_presentation = 'Ban'
        elif self.type == 'unbanned':
            type_presentation = 'Unban'
        elif self.type == 'pardoned':
            type_presentation = 'Przebaczenie'
        elif self.type == 'joined':
            type_presentation = 'Dołączenie'
        elif self.type == 'left':
            type_presentation = 'Opuszczenie'
        parts = [type_presentation, self.occurred_at.strftime('%-d %B %Y o %-H:%M')]
        if self.channel_id is not None:
            discord_channel = self.discord_channel(bot)
            parts.append(f'na #{discord_channel}' if discord_channel is not None else 'na usuniętym kanale')
        if self.executing_user_id is not None:
            discord_executing_user = bot.get_user(self.executing_user_id)
            if discord_executing_user is None:
                discord_executing_user = await bot.fetch_user(self.executing_user_id)
            parts.append(
                f'przez {discord_executing_user}'
                if discord_executing_user is not None
                else 'przez usuniętego użytkownika'
            )
        return ' '.join(parts)

    @staticmethod
    def comprehend_types(input_string: str) -> List[str]:
        types = []
        if 'warn' in input_string or 'ostrzeż' in input_string or 'ostrzez' in input_string:
            types.append('warned')
        if 'kick' in input_string or 'wyrzuć' in input_string or 'wyrzuc' in input_string:
            types.append('kicked')
        if 'unban' in input_string or 'odban' in input_string:
            types.append('unbanned')
        if 'ban' in input_string or 'wygnan' in input_string:
            types.append('banned')
        if 'pardon' in input_string or 'przebacz' in input_string:
            types.append('pardoned')
        if 'join' in input_string or 'dołącz' in input_string or 'dolacz' in input_string:
            types.append('joined')
        if (
            'leave' in input_string
            or 'left' in input_string
            or 'odejście' in input_string
            or 'odejscie' in input_string
            or 'odszed' in input_string
            or 'odesz' in input_string
        ):
            types.append('left')
        if not types:
            raise ValueError
        return types


class Moderation(commands.Cog):
    PAGE_FIELDS = 20

    def __init__(self, bot: Somsiad):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Adds the joining event to the member's file."""
        try:
            with data.session(commit=True) as session:
                event = Event(type='joined', server_id=member.guild.id, user_id=member.id)
                session.add(event)
        except psycopg2.errors.ForeignKeyViolation:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Adds the removal event to the member's file."""
        try:
            with data.session(commit=True) as session:
                event = Event(type='left', server_id=member.guild.id, user_id=member.id)
                session.add(event)
        except psycopg2.errors.ForeignKeyViolation:
            pass

    @commands.Cog.listener()
    async def on_member_ban(self, server: discord.Guild, user: discord.User):
        """Adds the ban event to the member's file."""
        try:
            with data.session(commit=True) as session:
                event = Event(type='banned', server_id=server.id, user_id=user.id)
                session.add(event)
        except psycopg2.errors.ForeignKeyViolation:
            pass

    @commands.Cog.listener()
    async def on_member_unban(self, server: discord.Guild, user: discord.User):
        """Adds the unban event to the member's file."""
        try:
            with data.session(commit=True) as session:
                event = Event(type='unbanned', server_id=server.id, user_id=user.id)
                session.add(event)
        except psycopg2.errors.ForeignKeyViolation:
            pass

    @commands.command(aliases=['ostrzeż', 'ostrzez'])
    @cooldown()
    @commands.guild_only()
    @has_permissions(kick_members=True)
    async def warn(self, ctx, subject_user: discord.Member, *, reason):
        """Warns the specified member."""
        if reason and len(reason) > Event.MAX_DETAILS_LENGTH:
            return await self.bot.send(
                ctx, embed=self.bot.generate_embed('⚠️', f'Powód musi zawierać się w 1000 znaków lub mniej.')
            )
        with data.session(commit=True) as session:
            warning_count_query = (
                session.query(Event)
                .filter(Event.server_id == ctx.guild.id, Event.user_id == subject_user.id, Event.type == 'warned')
                .statement.with_only_columns([data.func.count()])
            )
            warning_count = session.execute(warning_count_query).scalar() + 1
            event = Event(
                type='warned',
                server_id=ctx.guild.id,
                channel_id=ctx.channel.id,
                user_id=subject_user.id,
                executing_user_id=ctx.author.id,
                details=reason,
            )
            session.add(event)
        return await self.bot.send(
            ctx, embed=self.bot.generate_embed('✅', f'Ostrzeżono {subject_user} po raz {warning_count}.')
        )

    @warn.error
    async def warn_error(self, ctx, error):
        notice = None
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'subject_user':
                notice = 'Musisz podać którego użytkownika chcesz ostrzec'
            elif error.param.name == 'reason':
                notice = 'Musisz podać powód ostrzeżenia'
        elif isinstance(error, commands.BadArgument):
            notice = 'Nie znaleziono na serwerze pasującego użytkownika'
        if notice is not None:
            await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', notice))

    @commands.command(aliases=['wyrzuć', 'wyrzuc'])
    @cooldown()
    @commands.guild_only()
    @has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, subject_user: discord.Member, *, reason):
        """Kicks the specified member."""
        if reason and len(reason) > Event.MAX_DETAILS_LENGTH:
            return await self.bot.send(
                ctx, embed=self.bot.generate_embed('⚠️', f'Powód musi zawierać się w 1000 znaków lub mniej.')
            )
        try:
            await subject_user.kick(reason=reason)
        except discord.Forbidden:
            return await self.bot.send(
                ctx, embed=self.bot.generate_embed('⚠️', 'Bot nie może wyrzucić tego użytkownika')
            )
        else:
            with data.session(commit=True) as session:
                event = Event(
                    type='kicked',
                    server_id=ctx.guild.id,
                    channel_id=ctx.channel.id,
                    user_id=subject_user.id,
                    executing_user_id=ctx.author.id,
                    details=reason,
                )
                session.add(event)
            return await self.bot.send(ctx, embed=self.bot.generate_embed('✅', f'Wyrzucono {subject_user}'))

    @kick.error
    async def kick_error(self, ctx, error):
        notice = None
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'subject_user':
                notice = 'Musisz podać którego użytkownika chcesz wyrzucić'
            elif error.param.name == 'reason':
                notice = 'Musisz podać powód wyrzucenia'
        elif isinstance(error, commands.BadArgument):
            notice = 'Nie znaleziono na serwerze pasującego użytkownika'
        if notice is not None:
            await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', notice))

    @commands.command(aliases=['zbanuj'])
    @cooldown()
    @commands.guild_only()
    @has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, subject_user: discord.Member, *, reason):
        """Bans the specified member."""
        if reason and len(reason) > Event.MAX_DETAILS_LENGTH:
            return await self.bot.send(
                ctx, embed=self.bot.generate_embed('⚠️', f'Powód musi zawierać się w 1000 znaków lub mniej.')
            )
        try:
            await subject_user.ban(reason=reason)
        except discord.Forbidden:
            return await self.bot.send(
                ctx, embed=self.bot.generate_embed('⚠️', 'Bot nie może zbanować tego użytkownika')
            )
        else:
            with data.session(commit=True) as session:
                event = Event(
                    type='banned',
                    server_id=ctx.guild.id,
                    channel_id=ctx.channel.id,
                    user_id=subject_user.id,
                    executing_user_id=ctx.author.id,
                    details=reason,
                )
                session.add(event)
            return await self.bot.send(ctx, embed=self.bot.generate_embed('✅', f'Zbanowano {subject_user}'))

    @ban.error
    async def ban_error(self, ctx, error):
        notice = None
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'subject_user':
                notice = 'Musisz podać którego użytkownika chcesz zbanować'
            elif error.param.name == 'reason':
                notice = 'Musisz podać powód bana'
        elif isinstance(error, commands.BadArgument):
            notice = 'Nie znaleziono na serwerze pasującego użytkownika'
        if notice is not None:
            await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', notice))

    @commands.command(aliases=['przebacz'])
    @cooldown()
    @commands.guild_only()
    @has_permissions(kick_members=True)
    async def pardon(self, ctx, subject_user: discord.Member):
        """Clears specified member's warnings."""
        with data.session(commit=True) as session:
            warning_deleted_count = (
                session.query(Event)
                .filter(Event.server_id == ctx.guild.id, Event.user_id == subject_user.id, Event.type == 'warned')
                .delete()
            )
            if warning_deleted_count:
                warning_form = word_number_form(warning_deleted_count, 'ostrzeżenie', 'ostrzeżenia', 'ostrzeżeń')
                emoji = '✅'
                notice = f'Usunięto {warning_form} {subject_user}'
                event = Event(
                    type='pardoned',
                    server_id=ctx.guild.id,
                    channel_id=ctx.channel.id,
                    user_id=subject_user.id,
                    executing_user_id=ctx.author.id,
                    details=warning_form,
                )
                session.add(event)
            else:
                emoji = 'ℹ️'
                notice = f'{subject_user} nie ma na ostrzeżeń do usunięcia'
        await self.bot.send(ctx, embed=self.bot.generate_embed(emoji, notice))

    @pardon.error
    async def pardon_error(self, ctx, error):
        notice = None
        if isinstance(error, commands.MissingRequiredArgument):
            notice = 'Musisz podać któremu użytkownikowi chcesz przebaczyć'
        elif isinstance(error, commands.BadArgument):
            notice = 'Nie znaleziono na serwerze pasującego użytkownika'
        if notice is not None:
            await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', notice))

    @commands.command(aliases=['kartoteka'])
    @cooldown()
    @commands.guild_only()
    async def file(self, ctx, member: Union[discord.Member, int] = None, *, event_types: Event.comprehend_types = None):
        """Responds with a list of the user's files events on the server."""
        if isinstance(member, int):
            search_by_non_member_id = True
            member_id = member
            try:
                member = await self.bot.fetch_user(member)
            except discord.NotFound:
                member = None
        else:
            search_by_non_member_id = False
            member = member or ctx.author
            member_id = member.id
        with data.session() as session:
            events = session.query(Event)
            if event_types is None:
                events = events.filter(Event.server_id == ctx.guild.id, Event.user_id == member_id)
            else:
                events = events.filter(
                    Event.server_id == ctx.guild.id, Event.user_id == member_id, Event.type.in_(event_types)
                )
            events = events.order_by(Event.occurred_at.desc()).all()
            if member == ctx.author:
                address = 'Twoja kartoteka'
            else:
                address = f'Kartoteka {member if member else "usuniętego użytkownika"}'
        if events:
            current_page_index = 0
            page_count = ceil(len(events) / self.PAGE_FIELDS)
            event_types_description = ''
            if event_types is not None:
                if len(event_types) == 1:
                    event_types_description = ' podanego typu'
                elif len(event_types) > 1:
                    event_types_description = ' podanych typów'
            event_number_form = word_number_form(len(events), 'zdarzenie', 'zdarzenia', 'zdarzeń')

            async def generate_events_embed() -> discord.Embed:
                embed = self.bot.generate_embed(
                    '📂',
                    f'{address} zawiera {event_number_form}{event_types_description}',
                )
                relevant_events = events[self.PAGE_FIELDS*current_page_index:self.PAGE_FIELDS*(current_page_index+1)]
                if page_count > 1:
                    embed.description = f"Strona {current_page_index+1}. z {page_count}. {word_number_form(len(relevant_events), 'zdarzenie', 'zdarzenia', 'zdarzeń')} na stronie."
                for event in events[self.PAGE_FIELDS*current_page_index:self.PAGE_FIELDS*(current_page_index+1)]:
                    embed.add_field(
                        name=await event.get_presentation(self.bot),
                        value=text_snippet(event.details, Event.MAX_DETAILS_LENGTH) if event.details is not None else '—',
                        inline=False,
                    )
                return embed

            file_message = await self.bot.send(ctx, embed=await generate_events_embed())
            await file_message.add_reaction('⬅️')
            await file_message.add_reaction('➡️')
            while True:
                reaction, user = await self.bot.wait_for(
                    'reaction_add', check=lambda reaction, user: str(reaction.emoji) in ('⬅️', '➡️')
                )
                if str(reaction.emoji) == '⬅️' and current_page_index > 0:
                    current_page_index -= 1
                elif str(reaction.emoji) == '➡️' and current_page_index < page_count - 1:
                    current_page_index += 1
                await file_message.edit(embed=await generate_events_embed())
        else:
            if search_by_non_member_id:
                embed = self.bot.generate_embed('⚠️', 'Nie znaleziono na serwerze pasującego użytkownika')
            else:
                notice = 'jest pusta' if event_types is None else 'nie zawiera zdarzeń podanego typu'
                embed = self.bot.generate_embed('📂', f'{address} {notice}')

            await self.bot.send(ctx, embed=embed)

    @file.error
    async def file_error(self, ctx, error):
        notice = None
        if isinstance(error, commands.BadUnionArgument):
            notice = 'Nie znaleziono na serwerze pasującego użytkownika'
        elif isinstance(error, commands.BadArgument):
            notice = 'Nie rozpoznano żadnego typu zdarzenia'
        if notice is not None:
            await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', notice))

    @commands.command(aliases=['wyczyść', 'wyczysc'])
    @cooldown()
    @commands.guild_only()
    @has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx, number_of_messages_to_delete: int = 1):
        """Removes last number_of_messages_to_delete messages from the channel."""
        number_of_messages_to_delete = min(number_of_messages_to_delete, 100)
        await ctx.channel.purge(limit=number_of_messages_to_delete + 1)
        last_adjective_variant = word_number_form(number_of_messages_to_delete, 'ostatnią', 'ostatnie', 'ostatnich')
        messages_noun_variant = word_number_form(
            number_of_messages_to_delete, 'wiadomość', 'wiadomości', include_number=False
        )
        embed = self.bot.generate_embed('✅', f'Usunięto z kanału {last_adjective_variant} {messages_noun_variant}')
        await self.bot.send(ctx, embed=embed)

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = self.bot.generate_embed('⚠️', 'Podana wartość nie jest prawidłową liczbą wiadomości do usunięcia')
            await self.bot.send(ctx, embed=embed)


def setup(bot: Somsiad):
    bot.add_cog(Moderation(bot))
