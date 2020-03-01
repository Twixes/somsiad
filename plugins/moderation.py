# Copyright 2018–2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Union, Optional, List
import datetime as dt
import discord
from discord.ext import commands
from core import somsiad, ServerRelated, UserRelated, ChannelRelated
from utilities import word_number_form
from configuration import configuration
import data


class Event(data.Base, ServerRelated, UserRelated, ChannelRelated):
    id = data.Column(data.BigInteger, primary_key=True)
    type = data.Column(data.String(50), nullable=False)
    executing_user_id = data.Column(data.BigInteger, index=True)
    details = data.Column(data.String(2000))
    occurred_at = data.Column(data.DateTime, nullable=False, default=dt.datetime.utcnow)

    @property
    def discord_executing_user(self) -> Optional[discord.Guild]:
        return somsiad.get_user(self.executing_user_id) if self.executing_user_id is not None else None

    def __str__(self):
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
        parts = [
            type_presentation,
            self.occurred_at.replace(tzinfo=dt.timezone.utc).astimezone().strftime("%-d %B %Y o %H:%M")
        ]
        if self.channel_id is not None:
            discord_channel = self.discord_channel
            parts.append(f'na #{discord_channel}' if discord_channel is not None else 'na usuniętym kanale')
        if self.executing_user_id is not None:
            discord_executing_user = self.discord_executing_user
            parts.append(
                f'przez {discord_executing_user}' if discord_executing_user is not None else
                'przez usuniętego użytkownika'
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
                'leave' in input_string or 'left' in input_string or 'odejście' in input_string or
                'odejscie' in input_string or 'odszed' in input_string or 'odesz' in input_string
        ):
            types.append('left')
        if not types:
            raise ValueError
        return types


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Adds the joining event to the member's file."""
        with data.session(commit=True) as session:
            event = Event(type='joined', server_id=member.guild.id, user_id=member.id)
            session.add(event)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Adds the removal event to the member's file."""
        with data.session(commit=True) as session:
            event = Event(type='left', server_id=member.guild.id, user_id=member.id)
            session.add(event)

    @commands.Cog.listener()
    async def on_member_ban(self, server: discord.Guild, user: discord.User):
        """Adds the ban event to the member's file."""
        with data.session(commit=True) as session:
            event = Event(type='banned', server_id=server.id, user_id=user.id)
            session.add(event)

    @commands.Cog.listener()
    async def on_member_unban(self, server: discord.Guild, user: discord.User):
        """Adds the unban event to the member's file."""
        with data.session(commit=True) as session:
            event = Event(type='unbanned', server_id=server.id, user_id=user.id)
            session.add(event)

    @commands.command(aliases=['ostrzeż', 'ostrzez'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, subject_user: discord.Member, *, reason):
        """Warns the specified member."""
        with data.session(commit=True) as session:
            warning_count_query = session.query(Event).filter(
                Event.server_id == ctx.guild.id, Event.user_id == subject_user.id, Event.type == 'warned'
            ).statement.with_only_columns([data.func.count()])
            warning_count = session.execute(warning_count_query).scalar() + 1
            event = Event(
                type='warned', server_id=ctx.guild.id, channel_id=ctx.channel.id, user_id=subject_user.id,
                executing_user_id=ctx.author.id, details=reason
            )
            session.add(event)
        await self.bot.send(
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
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, subject_user: discord.Member, *, reason):
        """Kicks the specified member."""
        try:
            await subject_user.kick(reason=reason)
        except discord.Forbidden:
            await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', 'Bot nie może wyrzucić tego użytkownika'))
        else:
            with data.session(commit=True) as session:
                event = Event(
                    type='kicked', server_id=ctx.guild.id, channel_id=ctx.channel.id, user_id=subject_user.id,
                    executing_user_id=ctx.author.id, details=reason
                )
                session.add(event)
            await self.bot.send(ctx, embed=self.bot.generate_embed('✅', f'Wyrzucono {subject_user}'))

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
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, subject_user: discord.Member, *, reason):
        """Bans the specified member."""
        try:
            await subject_user.ban(reason=reason)
        except discord.Forbidden:
            await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', 'Bot nie może zbanować tego użytkownika'))
        else:
            with data.session(commit=True) as session:
                event = Event(
                    type='banned', server_id=ctx.guild.id, channel_id=ctx.channel.id, user_id=subject_user.id,
                    executing_user_id=ctx.author.id, details=reason
                )
                session.add(event)
            await self.bot.send(ctx, embed=self.bot.generate_embed('✅', f'Zbanowano {subject_user}'))

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
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def pardon(self, ctx, subject_user: discord.Member):
        """Clears specified member's warnings."""
        with data.session(commit=True) as session:
            warning_deleted_count = session.query(Event).filter(
                Event.server_id == ctx.guild.id, Event.user_id == subject_user.id, Event.type == 'warned'
            ).delete()
            if warning_deleted_count:
                warning_form = word_number_form(warning_deleted_count, 'ostrzeżenie', 'ostrzeżenia', 'ostrzeżeń')
                emoji = '✅'
                notice = f'Usunięto {warning_form} {subject_user}'
                event = Event(
                    type='pardoned', server_id=ctx.guild.id, channel_id=ctx.channel.id, user_id=subject_user.id,
                    executing_user_id=ctx.author.id, details=warning_form
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
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    @commands.guild_only()
    async def file(
            self, ctx, member: Union[discord.Member, int] = None, *, event_types: Event.comprehend_types = None
    ):
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
                events = events.filter(
                    Event.server_id == ctx.guild.id, Event.user_id == member_id
                )
            else:
                events = events.filter(
                    Event.server_id == ctx.guild.id, Event.user_id == member_id, Event.type.in_(event_types)
                )
            events = events.order_by(Event.occurred_at).all()
            if member == ctx.author:
                address = 'Twoja kartoteka'
            else:
                address = f'Kartoteka {member if member else "usuniętego użytkownika"}'
        if events:
            if event_types is None:
                event_types_description = ''
            elif len(event_types) == 1:
                event_types_description = ' podanego typu'
            elif len(event_types) > 1:
                event_types_description = ' podanych typów'
            event_number_form = word_number_form(len(events), 'zdarzenie', 'zdarzenia', 'zdarzeń')
            embed = discord.Embed(
                title=f':open_file_folder: {address} zawiera {event_number_form}{event_types_description}',
                description='Pokazuję 25 najnowszych.' if len(events) > 25 else '',
                color=self.bot.COLOR
            )
            for event in events[-25:]:
                embed.add_field(
                    name=str(event),
                    value=event.details if event.details is not None else '—',
                    inline=False
                )
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
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx, number_of_messages_to_delete: int = 1):
        """Removes last number_of_messages_to_delete messages from the channel."""
        number_of_messages_to_delete = min(number_of_messages_to_delete, 100)
        await ctx.channel.purge(limit=number_of_messages_to_delete+1)
        last_adjective_variant = word_number_form(
            number_of_messages_to_delete, 'ostatnią', 'ostatnie', 'ostatnich'
        )
        messages_noun_variant = word_number_form(
            number_of_messages_to_delete, 'wiadomość', 'wiadomości', include_number=False
        )

        await self.bot.send(
            ctx, embed=self.bot.generate_embed(
                '✅', f'Usunięto z kanału {last_adjective_variant} {messages_noun_variant}',
                self.bot.MESSAGE_AUTODESTRUCTION_NOTICE
            ),
            delete_after=self.bot.MESSAGE_AUTODESTRUCTION_TIME_IN_SECONDS
        )

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            notice = 'Podana wartość nie jest prawidłową liczbą wiadomości do usunięcia'
            await self.bot.send(
                ctx, embed=self.bot.generate_embed('⚠️', notice),
                delete_after=self.bot.MESSAGE_AUTODESTRUCTION_TIME_IN_SECONDS
            )


somsiad.add_cog(Moderation(somsiad))
