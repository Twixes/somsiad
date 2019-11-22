# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import datetime as dt
from typing import Union, Optional
import discord
from somsiad import somsiad
from server_data import server_data_manager
from utilities import TextFormatter


class Files:
    """Handles logging user-related events on the server."""
    TABLE_NAME = 'files'
    TABLE_COLUMNS = (
        'event_id INTEGER NOT NULL PRIMARY KEY',
        'event_type TEXT NOT NULL',
        'channel_id INTEGER',
        'executing_user_id INTEGER',
        'subject_user_id INTEGER NOT NULL',
        'posix_timestamp INTEGER NOT NULL',
        'reason TEXT'
    )

    class Event:
        """A files event."""
        __slots__ = (
            'event_id', 'event_type', 'server_id', 'server', 'channel_id', 'channel', 'executing_user_id',
            'executing_user', 'subject_user_id', 'subject_user', 'posix_timestamp', 'local_datetime', 'reason'
        )

        def __init__(
                self, *, event_id: int = None, event_type: str, server_id: int, channel_id: int = None,
                executing_user_id: int = None, subject_user_id: int, posix_timestamp: int, reason: str = None
        ):
            self.event_id = event_id
            self.event_type = event_type
            self.server_id = server_id
            self.server = somsiad.bot.get_guild(server_id)
            self.channel_id = channel_id
            self.channel = None if channel_id is None else somsiad.bot.get_channel(channel_id)
            self.executing_user_id = executing_user_id
            self.executing_user = None if executing_user_id is None else somsiad.bot.get_user(executing_user_id)
            self.subject_user_id = subject_user_id
            self.subject_user = self.server.get_member(subject_user_id) or somsiad.bot.get_user(subject_user_id)
            self.posix_timestamp = posix_timestamp
            self.local_datetime = (
                dt.datetime.fromtimestamp(posix_timestamp).replace(tzinfo=dt.timezone.utc).astimezone()
            )
            self.reason = reason

        def __str__(self):
            if self.event_type == 'warned':
                return 'ostrzeżenie'
            elif self.event_type == 'kicked':
                return 'wyrzucenie'
            elif self.event_type == 'banned':
                return 'ban'
            elif self.event_type == 'unbanned':
                return 'unban'
            elif self.event_type == 'joined':
                return 'dołączenie'
            elif self.event_type == 'left':
                return 'opuszczenie'
            else:
                return '?'

        def __hash__(self):
            return hash(100000 * self.server_id + self.event_id)

        def __eq__(self, other):
            return self.server_id == other.server_id and self.event_id == other.event_id

    @classmethod
    def add_event(
            cls, *, event_type: str, server: discord.Guild, channel: discord.TextChannel = None,
            executing_user: discord.Member = None, subject_user = Union[discord.Guild, discord.TextChannel,
            discord.VoiceChannel, discord.Member, discord.Message], posix_timestamp: int = None, reason: str = None
    ):
        """Adds an event with specified parameters to the database of the provided server."""
        channel_id = None if channel is None else channel.id
        executing_user_id = None if executing_user is None else executing_user.id
        posix_timestamp = posix_timestamp or int(dt.datetime.utcnow().timestamp())

        server_data_manager.ensure_table_existence_for_server(server.id, cls.TABLE_NAME, cls.TABLE_COLUMNS)
        server_data_manager.servers[server.id]['db_cursor'].execute(
            f'''INSERT INTO {cls.TABLE_NAME}(event_type, channel_id, executing_user_id, subject_user_id,
            posix_timestamp, reason) VALUES (?, ?, ?, ?, ?, ?)''',
            (event_type, channel_id, executing_user_id, subject_user.id, posix_timestamp, reason)
        )
        server_data_manager.servers[server.id]['db'].commit()

    @staticmethod
    def comprehend_event_types(raw_event_types: str) -> list:
        event_types = []
        if 'warn' in raw_event_types or 'ostrzeż' in raw_event_types or 'ostrzez' in raw_event_types:
            event_types.append('warned')
        if 'kick' in raw_event_types or 'wyrzuć' in raw_event_types or 'wyrzuc' in raw_event_types:
            event_types.append('kicked')
        if 'unban' in raw_event_types or 'odban' in raw_event_types:
            event_types.append('unbanned')
        if 'ban' in raw_event_types or 'wygnan' in raw_event_types:
            event_types.append('banned')
        if 'join' in raw_event_types or 'dołącz' in raw_event_types or 'dolacz' in raw_event_types:
            event_types.append('joined')
        if (
                'leave' in raw_event_types or 'left' in raw_event_types or 'odejście' in raw_event_types or
                'odejscie' in raw_event_types or 'odszed' in raw_event_types or 'odesz' in raw_event_types
        ):
            event_types.append('left')

        return event_types

    @classmethod
    def get_events(
            cls, *, server: discord.Guild, event_types: Union[str, tuple, list] = None,
            channel: discord.TextChannel = None, subject_user: Union[
                discord.Guild, discord.TextChannel, discord.VoiceChannel, discord.Member, discord.Message
            ] = None
    ) -> tuple:
        """Returns a list of events on the provided server."""
        server_data_manager.ensure_table_existence_for_server(server.id, cls.TABLE_NAME, cls.TABLE_COLUMNS)
        condition_strings = []
        condition_variables = []
        if isinstance(event_types, str):
            condition_strings.append('event_type = ?')
            condition_variables.append(event_types)
        elif isinstance(event_types, (tuple, list)) and event_types:
            condition_strings.append(f'({" OR ".join(["event_type = ?" for _ in event_types])})')
            condition_variables.extend(event_types)
        if channel is not None:
            condition_strings.append('channel_id = ?')
            condition_variables.append(channel.id)
        if subject_user is not None:
            condition_strings.append('subject_user_id = ?')
            condition_variables.append(subject_user.id)

        combined_condition_string = f'WHERE {" AND ".join(condition_strings)}'
        server_data_manager.servers[server.id]['db_cursor'].execute(
            f'''SELECT event_id, event_type, channel_id, executing_user_id, subject_user_id,
            posix_timestamp, reason FROM {cls.TABLE_NAME} {combined_condition_string if condition_strings else ""}''',
            condition_variables
        )

        results_rows = server_data_manager.servers[server.id]['db_cursor'].fetchall()
        results_dicts = map(server_data_manager.dict_from_row, results_rows)

        events = [
            cls.Event(
                event_id=result['event_id'], event_type=result['event_type'], server_id=server.id,
                channel_id=result['channel_id'], executing_user_id=result['executing_user_id'],
                subject_user_id=result['subject_user_id'], posix_timestamp=result['posix_timestamp'],
                reason=result['reason']
            ) for result in results_dicts
        ]
        new_to_old_events = tuple(reversed(events)) # reverse the order of events so that the'yre ordered new to old

        return new_to_old_events


@somsiad.bot.event
async def on_member_join(member):
    """Adds the joining event to the member's file."""
    Files.add_event(event_type='joined', server=member.guild, subject_user=member)


@somsiad.bot.event
async def on_member_remove(member):
    """Adds the removal event to the member's file."""
    Files.add_event(event_type='left', server=member.guild,subject_user=member)


@somsiad.bot.event
async def on_member_ban(server, member):
    """Adds the unban event to the member's file."""
    Files.add_event(event_type='banned', server=server, subject_user=member)


@somsiad.bot.event
async def on_member_unban(server, member):
    """Adds the unban event to the member's file."""
    Files.add_event(event_type='unbanned', server=server, subject_user=member)


@somsiad.bot.command(aliases=['ostrzeż', 'ostrzez'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
@discord.ext.commands.has_permissions(kick_members=True)
async def warn(ctx, subject_user: discord.Member, *, reason):
    """Warns the specified member."""
    Files.add_event(
        event_type='warned', server=ctx.guild, channel=ctx.channel, executing_user=ctx.author,
        subject_user=subject_user, reason=reason
    )
    warnings = Files.get_events(server=ctx.guild, event_types='warned', subject_user=subject_user)

    embed = discord.Embed(
        title=f':white_check_mark: Ostrzeżono {subject_user} po raz {len(warnings)}.',
        color=somsiad.COLOR
    )

    await ctx.send(ctx.author.mention, embed=embed)


@warn.error
async def warn_error(ctx, error):
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        if error.param.name == 'subject_user':
            embed = discord.Embed(
                title=f':warning: Musisz podać którego użytkownika chcesz ostrzec!',
                color=somsiad.COLOR
            )
        elif error.param.name == 'reason':
            embed = discord.Embed(
                title=f':warning: Musisz podać powód ostrzeżenia!',
                color=somsiad.COLOR
            )
        await ctx.send(ctx.author.mention, embed=embed)
    elif isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Nie znaleziono na serwerze pasującego użytkownika!',
            color=somsiad.COLOR
        )
        await ctx.send(ctx.author.mention, embed=embed)


@somsiad.bot.command(aliases=['wyrzuć', 'wyrzuc'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
@discord.ext.commands.has_permissions(kick_members=True)
async def kick(ctx, subject_user: discord.Member, *, reason):
    """Kicks the specified member."""
    try:
        await subject_user.kick(reason=reason)
    except discord.Forbidden:
        embed = discord.Embed(
            title=f':warning: Bot nie ma uprawnień do wyrzucenia tego użytkownika!',
            color=somsiad.COLOR
        )
        return await ctx.send(ctx.author.mention, embed=embed)

    Files.add_event(
        event_type='kicked', server=ctx.guild, channel=ctx.channel, executing_user=ctx.author,
        subject_user=subject_user, reason=reason
    )

    embed = discord.Embed(
        title=f':white_check_mark: Wyrzucono {subject_user}',
        color=somsiad.COLOR
    )

    return await ctx.send(ctx.author.mention, embed=embed)


@kick.error
async def kick_error(ctx, error):
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        if error.param.name == 'subject_user':
            embed = discord.Embed(
                title=f':warning: Musisz podać którego użytkownika chcesz wyrzucić!',
                color=somsiad.COLOR
            )
        elif error.param.name == 'reason':
            embed = discord.Embed(
                title=f':warning: Musisz podać powód wyrzucenia!',
                color=somsiad.COLOR
            )
        await ctx.send(ctx.author.mention, embed=embed)
    elif isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Nie znaleziono na serwerze pasującego użytkownika!',
            color=somsiad.COLOR
        )
        await ctx.send(ctx.author.mention, embed=embed)


@somsiad.bot.command(aliases=['zbanuj'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
@discord.ext.commands.has_permissions(ban_members=True)
async def ban(ctx, subject_user: discord.Member, *, reason):
    """Bans the specified member."""
    try:
        await subject_user.ban(reason=reason)
    except discord.Forbidden:
        embed = discord.Embed(
            title=f':warning: Bot nie ma uprawnień do zbanowania tego użytkownika!',
            color=somsiad.COLOR
        )
        return await ctx.send(ctx.author.mention, embed=embed)

    embed = discord.Embed(
        title=f':white_check_mark: Zbanowano {subject_user}',
        color=somsiad.COLOR
    )

    return await ctx.send(ctx.author.mention, embed=embed)


@ban.error
async def ban_error(ctx, error):
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        if error.param.name == 'subject_user':
            embed = discord.Embed(
                title=f':warning: Musisz podać którego użytkownika chcesz zbanować!',
                color=somsiad.COLOR
            )
        elif error.param.name == 'reason':
            embed = discord.Embed(
                title=f':warning: Musisz podać powód bana!',
                color=somsiad.COLOR
            )
        await ctx.send(ctx.author.mention, embed=embed)
    elif isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Nie znaleziono na serwerze pasującego użytkownika!',
            color=somsiad.COLOR
        )
        await ctx.send(ctx.author.mention, embed=embed)


@somsiad.bot.command(aliases=['kartoteka'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def file(ctx, member: Optional[discord.Member] = None, *, raw_event_types: str = None):
    """Responds with a list of the user's files entries on the server."""
    if member is None:
        member = ctx.author

    if raw_event_types is None:
        event_types = None
    else:
        event_types = Files.comprehend_event_types(raw_event_types)

    entries = Files.get_events(server=ctx.guild, subject_user=member, event_types=event_types)

    if entries:
        if event_types is None:
            event_types_description = ""
        elif len(event_types) == 1:
            event_types_description = " podanego typu"
        elif len(event_types) > 1:
            event_types_description = " podanych typów"
        embed = discord.Embed(
            title=f':open_file_folder: {"Twoja kartoteka" if member == ctx.author else f"Kartoteka {member}"} '
            f'zawiera {TextFormatter.word_number_variant(len(entries), "zdarzenie", "zdarzenia", "zdarzeń")}'
            f'{event_types_description}',
            color=somsiad.COLOR
        )
        for entry in entries:
            entry_info = [str(entry).capitalize(), entry.local_datetime.strftime("%-d %B %Y o %H:%M")]
            if entry.channel is not None:
                entry_info.append(f'#{entry.channel}')
            if entry.executing_user is not None:
                entry_info.append(str(entry.executing_user))
            embed.add_field(
                name=" – ".join(entry_info),
                value=entry.reason if entry.reason is not None else '*Brak szczegółów.*',
                inline=False
                )
    else:
        if event_types is None:
            embed = discord.Embed(
                title=f':open_file_folder: {"Twoja kartoteka" if member == ctx.author else f"Kartoteka {member}"} '
                'jest pusta',
                color=somsiad.COLOR
            )
        else:
            embed = discord.Embed(
                title=f':open_file_folder: {"Twoja kartoteka" if member == ctx.author else f"Kartoteka {member}"} '
                'nie zawiera zdarzeń podanego typu',
                color=somsiad.COLOR
            )

    await ctx.send(ctx.author.mention, embed=embed)


@file.error
async def file_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Nie znaleziono na serwerze pasującego użytkownika!',
            color=somsiad.COLOR
        )
        await ctx.send(ctx.author.mention, embed=embed)


@somsiad.bot.command(aliases=['wyczyść', 'wyczysc'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
@discord.ext.commands.has_permissions(manage_messages=True)
@discord.ext.commands.bot_has_permissions(manage_messages=True)
async def purge(ctx, number_of_messages_to_delete: int = 1):
    """Removes last number_of_messages_to_delete messages from the channel."""
    # limit the number of messages to delete to 100
    number_of_messages_to_delete = min(number_of_messages_to_delete, 100)

    await ctx.channel.purge(limit=number_of_messages_to_delete+1)

    last_adjective_variant = TextFormatter.word_number_variant(
        number_of_messages_to_delete, 'ostatnią', 'ostatnie', 'ostatnich'
    )
    messages_noun_variant = TextFormatter.word_number_variant(
        number_of_messages_to_delete, 'wiadomość', 'wiadomości', include_number=False
    )
    embed = discord.Embed(
        title=f':white_check_mark: Usunięto z kanału {last_adjective_variant} {messages_noun_variant}',
        description=somsiad.MESSAGE_AUTODESTRUCTION_NOTICE,
        color=somsiad.COLOR
    )

    await ctx.send(ctx.author.mention, embed=embed, delete_after=somsiad.message_autodestruction_time_in_seconds)


@purge.error
async def purge_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.BotMissingPermissions):
        embed = discord.Embed(
            title=':warning: Nie usunięto z kanału żadnych wiadomości, ponieważ bot nie ma tutaj do tego uprawnień',
            description=somsiad.MESSAGE_AUTODESTRUCTION_NOTICE,
            color=somsiad.COLOR
        )
        await ctx.send(ctx.author.mention, embed=embed, delete_after=somsiad.message_autodestruction_time_in_seconds)
    elif isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Podana wartość nie jest prawidłową liczbą wiadomości do usunięcia',
            description=somsiad.MESSAGE_AUTODESTRUCTION_NOTICE,
            color=somsiad.COLOR
        )
        await ctx.send(ctx.author.mention, embed=embed, delete_after=somsiad.message_autodestruction_time_in_seconds)
