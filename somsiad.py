# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import List
import os
import sys
import asyncio
import platform
import logging
import random
import itertools
import datetime as dt
import discord
from discord.ext.commands import Bot
from version import __version__
from utilities import TextFormatter
from configuration import configuration
import data

COPYRIGHT = '© 2018-2019 Twixes, ondondil et al.'

class Somsiad(Bot):
    COLOR = 0x7289da
    USER_AGENT = f'SomsiadBot/{__version__}'
    WEBSITE_URL = 'https://somsiad.net'
    EMOJIS = [
        '🐜', '🅱️', '🔥', '🐸', '🤔', '💥', '👌', '💩', '🐇', '🐰', '🦅', '🙃', '😎', '😩', '👹', '👺', '🤖', '✌️',
        '🙌', '👋', '💪', '👀', '👷', '🕵️', '💃', '🎩', '🤠', '🐕', '🐈', '🐹', '🐨', '🐽', '🐙', '🐧', '🐔', '🐎',
        '🦄', '🐝', '🐢', '🐬', '🐋', '🐐', '🌵', '🌻', '🌞', '☄️', '⚡', '🦆', '🦉', '🦊', '🍎', '🍉', '🍇', '🍑',
        '🍍', '🍆', '🍞', '🧀', '🍟', '🎂', '🍬', '🍭', '🍪', '🥑', '🥔', '🎨', '🎷', '🎺', '👾', '🎯', '🥁', '🚀',
        '🛰️', '⚓', '🏖️', '✨', '🌈', '💡', '💈', '🔭', '🎈', '🎉', '💯', '💝', '☢️', '🆘', '♨️', '💭'
    ]
    IGNORED_ERRORS = (
        discord.ext.commands.CommandNotFound,
        discord.ext.commands.MissingRequiredArgument,
        discord.ext.commands.BadArgument
    )
    MESSAGE_AUTODESTRUCTION_TIME_IN_SECONDS = 5
    MESSAGE_AUTODESTRUCTION_NOTICE = (
        'Ta wiadomość ulegnie autodestrukcji w ciągu '
        f'{TextFormatter.word_number_variant(MESSAGE_AUTODESTRUCTION_TIME_IN_SECONDS, "sekundy", "sekund")} od wysłania.'
    )

    bot_dir_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    storage_dir_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'somsiad')
    cache_dir_path = os.path.join(os.path.expanduser('~'), '.cache', 'somsiad')

    def __init__(self):
        super().__init__(
            command_prefix=self._get_prefix, help_command=None, description='Zawsze pomocny Somsiad',
            case_insensitive=True
        )
        self.run_datetime = None
        self.logger = logging.getLogger('Somsiad')
        logging.basicConfig(
            filename=os.path.join(self.bot_dir_path, 'somsiad.log'),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        if not os.path.exists(self.storage_dir_path):
            os.makedirs(self.storage_dir_path)
        if not os.path.exists(self.cache_dir_path):
            os.makedirs(self.cache_dir_path)
        self.conf = configuration
        self.prefix_safe_commands = tuple(map(
            lambda command: f'{self.conf["command_prefix"]}{command}',
            ('help', 'pomocy', 'pomoc', 'prefix', 'prefiks', 'przedrostek', 'info', 'informacje', 'ping')
        ))

    async def on_ready(self):
        print(self.info())
        self.ensure_registration_of_all_servers()
        await self.cycle_presence()

    async def on_command_error(self, ctx, error):
        if isinstance(error, self.IGNORED_ERRORS):
            pass
        elif isinstance(error, discord.ext.commands.NoPrivateMessage):
            embed = discord.Embed(
                title=f':warning: Ta komenda nie może być użyta w prywatnych wiadomościach!',
                color=self.COLOR
            )
            await ctx.send(embed=embed)
        elif isinstance(error, discord.ext.commands.DisabledCommand):
            embed = discord.Embed(
                title=f':warning: Ta komenda jest wyłączona!',
                color=self.COLOR
            )
            await ctx.send(ctx.author.mention, embed=embed)
        else:
            prefixed_command_qualified_name = f'{self.conf["command_prefix"]}{ctx.command.qualified_name}'
            if ctx.guild is None:
                log_entry = (
                    f'Ignoring {type(error).__name__} type exception in command {prefixed_command_qualified_name} '
                    f'used by {ctx.author} (ID {ctx.author.id}) in direct messages: "{error}"'
                )
            else:
                log_entry = (
                    f'Ignoring {type(error).__name__} type exception in command {prefixed_command_qualified_name} '
                    f'used by {ctx.author} (ID {ctx.author.id}) on server {ctx.guild} (ID {ctx.guild.id}): "{error}"'
                )
            self.logger.error(log_entry)

    def controlled_run(self):
        self.run_datetime = dt.datetime.now()
        try:
            self.run(self.conf['discord_token'], reconnect=True)
        except discord.errors.ClientException:
            self.logger.critical('Client could not come online! The Discord bot token provided may be faulty.')
        else:
            self.logger.info('Client started.')

    def ensure_registration_of_all_servers(self):
        session = data.Session()
        server_ids_already_registered = [server.id for server in session.query(data.Server).all()]
        session.add_all((
            data.Server(id=server.id, joined_at=server.me.joined_at) for server in self.guilds
            if server.id not in server_ids_already_registered
        ))
        session.commit()
        session.close()

    def invite_url(self) -> str:
        """Return the invitation URL of the bot."""
        return discord.utils.oauth_url(self.user.id, discord.Permissions(305392727))

    def info(self) -> str:
        """Return a block of bot information."""
        number_of_users = len(set(self.get_all_members()))
        number_of_servers = len(self.guilds)
        info_lines = [
            f'Obudzono Somsiada (ID {self.user.id}).',
            '',
            f'Połączono {TextFormatter.with_preposition_variant(number_of_users)} '
            f'{TextFormatter.word_number_variant(number_of_users, "użytkownikiem", "użytkownikami")} '
            f'na {TextFormatter.word_number_variant(number_of_servers, "serwerze", "serwerach")}.',
            '',
            'Link do zaproszenia bota:',
            self.invite_url(),
            '',
            *map(str, self.conf.settings.values()),
            '',
            f'Somsiad {__version__} • discord.py {discord.__version__} • Python {platform.python_version()}',
            '',
            COPYRIGHT
        ]
        return '\n'.join(info_lines)

    async def cycle_presence(self):
        """Cycle through prefix safe commands in the presence."""
        prefix_safe_commands = ('pomocy', 'prefiks', 'info', 'ping')
        for command in itertools.cycle(prefix_safe_commands):
            await self.change_presence(
                activity=discord.Game(name=f'Kiedyś to było | {self.conf["command_prefix"]}{command}')
            )
            await asyncio.sleep(15)

    def _get_prefix(self, bot: Bot, message: discord.Message) -> List[str]:
        user_id = bot.user.id
        prefixes = [f'<@!{user_id}> ', f'<@{user_id}> ']
        session = data.Session()
        data_server = session.query(data.Server).filter(data.Server.id == message.guild.id).one_or_none()
        session.close()
        does_server_have_custom_command_prefix = data_server is not None and data_server.command_prefix is not None
        is_message_a_prefix_safe_command = message.content.startswith(self.prefix_safe_commands)
        if does_server_have_custom_command_prefix:
            prefixes.append(data_server.command_prefix)
        if not does_server_have_custom_command_prefix or is_message_a_prefix_safe_command:
            prefixes.append(self.conf['command_prefix'])
        return prefixes


somsiad = Somsiad()


@somsiad.command(aliases=['nope', 'nie'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def no(ctx, member: discord.Member = None):
    """Removes the last message sent by the bot in the channel on the requesting user's request."""
    member = member or ctx.author

    if member == ctx.author or ctx.author.permissions_in(ctx.channel).manage_messages:
        async for message in ctx.history(limit=10):
            if message.author == ctx.me and member in message.mentions:
                await message.delete()
                break


@somsiad.command(aliases=['prefiks', 'przedrostek'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
@discord.ext.commands.has_permissions(administrator=True)
async def prefix(ctx, new_prefix = None):
    """Presents the current command prefix or changes it."""
    session = data.Session()
    data_server = session.query(data.Server).filter(data.Server.id == ctx.guild.id).one()

    if new_prefix is None:
        embed = discord.Embed(
            title=':wrench: Obecny prefiks to '
            f'*{data_server.command_prefix or somsiad.conf["command_prefix"]}*'
            f'{" (wartość domyślna)" if data_server.command_prefix is None else ""}',
            color=somsiad.COLOR
        )
    elif len(new_prefix) > data.Server.COMMAND_PREFIX_MAX_LENGTH:
        embed = discord.Embed(
            title=':warning: Prefiks nie może być dłuższy niż '
            f'{TextFormatter.word_number_variant(data.Server.COMMAND_PREFIX_MAX_LENGTH, "znak", "znaki", "znaków")}!',
            color=somsiad.COLOR
        )
    else:
        data_server.command_prefix = new_prefix
        session.commit()
        embed = discord.Embed(
            title=f':white_check_mark: Ustawiono nowy prefiks *{new_prefix}*',
            color=somsiad.COLOR
        )
    session.close()
    await ctx.send(ctx.author.mention, embed=embed)


@somsiad.command(aliases=['wersja', 'v'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def version(ctx):
    """Responds with current version of the bot."""
    embed = discord.Embed(
        title=f'{random.choice(somsiad.EMOJIS)} Somsiad {__version__}',
        url=somsiad.WEBSITE_URL,
        color=somsiad.COLOR
    )
    embed.set_footer(text=COPYRIGHT)
    await ctx.send(ctx.author.mention, embed=embed)


@somsiad.command(aliases=['informacje'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def info(ctx):
    """Responds with current version of the bot."""
    embed = discord.Embed(
        title=f':information_source: Somsiad {__version__}',
        url=somsiad.WEBSITE_URL,
        color=somsiad.COLOR
    )
    embed.add_field(name='Liczba serwerów', value=len(somsiad.guilds))
    embed.add_field(name='Liczba użytkowników', value=len(set(somsiad.get_all_members())))
    embed.add_field(
        name='Czas pracy', value=TextFormatter.human_readable_time(dt.datetime.now() - somsiad.run_datetime)
    )
    embed.add_field(name='Właściciel instancji', value=(await somsiad.application_info()).owner.mention)
    embed.set_footer(text=COPYRIGHT)
    await ctx.send(ctx.author.mention, embed=embed)


@somsiad.command()
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def ping(ctx):
    """Pong!"""
    embed = discord.Embed(
        title=':ping_pong: Pong!',
        color=somsiad.COLOR
    )
    await ctx.send(ctx.author.mention, embed=embed)
