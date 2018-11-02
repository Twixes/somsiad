# Copyright 2018 Habchy, ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import os
import sys
import platform
import logging
from typing import Union
import discord
from discord.ext.commands import Bot
from version import __version__
from utilities import Configurator, Setting, TextFormatter


class Somsiad:
    color = 0x7289da
    user_agent = f'SomsiadBot/{__version__}'

    bot_dir_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    conf_dir_path = os.path.join(os.path.expanduser('~'), '.config')
    conf_file_path = os.path.join(conf_dir_path, 'somsiad.json')
    storage_dir_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'somsiad')
    cache_dir_path = os.path.join(os.path.expanduser('~'), '.cache', 'somsiad')

    logger = None
    configurator = None
    bot = None
    user_converter = None
    member_converter = None

    message_autodestruction_time_in_seconds = 5
    message_autodestruction_notice = (
        'Ta wiadomość ulegnie autodestrukcji w ciągu '
        f'{TextFormatter.word_number_variant(message_autodestruction_time_in_seconds, "sekundy", "sekund")} od wysłania.'
    )

    required_settings = [
        Setting(
            'discord_token', description='Token bota', input_instruction='Wprowadź discordowy token bota',
            value_type='str'
        ),
        Setting(
            'command_prefix', description='Prefiks komend', input_instruction='Wprowadź prefiks komend',
            value_type='str', default_value='!'
        ),
        Setting(
            'command_cooldown_per_user_in_seconds', description='Cooldown wywołania komendy przez użytkownika',
            input_instruction='Wprowadź cooldown wywołania komendy przez użytkownika w sekundach',
            unit=('sekunda', 'sekund'), value_type='float', default_value=1.0
        )
    ]

    def __init__(self, additional_required_settings: Union[list, tuple] = None):
        self.logger = logging.getLogger('Somsiad')
        logging.basicConfig(
            filename=os.path.join(self.bot_dir_path, 'somsiad.log'),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        if not os.path.exists(self.conf_dir_path):
            os.makedirs(self.conf_dir_path)
        if not os.path.exists(self.storage_dir_path):
            os.makedirs(self.storage_dir_path)
        if not os.path.exists(self.cache_dir_path):
            os.makedirs(self.cache_dir_path)
        self.required_settings.extend(additional_required_settings)
        self.configurator = Configurator(self.conf_file_path, self.required_settings)
        self.bot = Bot(
            description='Zawsze pomocny Somsiad',
            command_prefix=self.conf['command_prefix'],
            case_insensitive=True
        )
        self.bot.remove_command('help') # Replaced with the 'help_direct' plugin
        self.member_converter = discord.ext.commands.MemberConverter()
        self.user_converter = discord.ext.commands.UserConverter()

    def run(self):
        """Launches the bot."""
        try:
            self.bot.run(somsiad.conf['discord_token'])
            self.logger.info('Client started.')
        except discord.errors.ClientException:
            self.logger.critical('Client could not come online! The Discord bot token provided may be faulty.')

    @property
    def conf(self):
        """Returns current configuration of the bot."""
        return self.configurator.configuration

    @property
    def invite_url(self):
        """Returns the invitation URL of the bot."""
        try:
            return discord.utils.oauth_url(self.bot.user.id, discord.Permissions(536083543))
        except discord.errors.ClientException:
            return None

    def list_of_servers(self):
        """Generates a list of servers the bot is connected to, including the number of days since joining
        and the number of users.
        """
        servers = [guild for guild in self.bot.guilds if guild.me is not None]
        sorted_servers = sorted(servers, key=lambda server: server.me.joined_at, reverse=True)
        longest_server_name_length = 0
        longest_days_since_joining_info_length = 0
        list_of_servers = []

        for server in sorted_servers:
            if len(server.name) > longest_server_name_length:
                longest_server_name_length = len(server.name)
            days_since_joining_info = TextFormatter.time_ago(server.me.joined_at, name_month=False)
            if len(days_since_joining_info) > longest_days_since_joining_info_length:
                longest_days_since_joining_info_length = len(days_since_joining_info)

        for server in sorted_servers:
            days_since_joining_info = TextFormatter.time_ago(server.me.joined_at, name_month=False)
            list_of_servers.append(
                f'{server.name.ljust(longest_server_name_length)} - '
                f'dołączono {days_since_joining_info.ljust(longest_days_since_joining_info_length)} - '
                f'{TextFormatter.word_number_variant(server.member_count, "użytkownik", "użytkowników")}'
            )

        return list_of_servers


# Plugin settings
ADDITIONAL_REQUIRED_SETTINGS = (
    Setting(
        'google_key', description='Klucz API Google', input_instruction='Wprowadź klucz API Google', value_type='str'
    ),
    Setting(
        'google_custom_search_engine_id', description='Identyfikator CSE Google',
        input_instruction='Wprowadź identyfikator CSE Google', value_type='str'
    ),
    Setting(
        'goodreads_key', description='Klucz API Goodreads', input_instruction='Wprowadź klucz API Goodreads',
        value_type='str'
    ),
    Setting(
        'giphy_key', description='Klucz API Giphy', input_instruction='Wprowadź klucz API Giphy', value_type='str'
    ),
    Setting(
        'omdb_key', description='Klucz API OMDb', input_instruction='Wprowadź klucz API OMDb', value_type='str'
    ),
    Setting(
        'last_fm_key', description='Klucz API Last.fm', input_instruction='Wprowadź klucz API Last.fm', value_type='str'
    ),
    Setting(
        'reddit_id', description='ID aplikacji redditowej', input_instruction='Wprowadź ID aplikacji redditowej',
        value_type='str'
    ),
    Setting(
        'reddit_secret', description='Szyfr aplikacji redditowej',
        input_instruction='Wprowadź szyfr aplikacji redditowej', value_type='str'
    ),
    Setting(
        'reddit_username', description='Redditowa nazwa użytkownika',
        input_instruction='Wprowadź redditową nazwę użytkownika', value_type='str'
    ),
    Setting(
        'reddit_password', description='Hasło do konta na Reddicie',
        input_instruction='Wprowadź hasło do konta na Reddicie', value_type='str'
    ),
    Setting(
        'reddit_account_min_age_in_days', description='Minimalny wiek weryfikowanego konta na Reddicie',
        input_instruction='Wprowadź minimalny wiek weryfikowanego konta na Reddicie w dniach',
        unit=('dzień', 'dni'), value_type='int', default_value=14
    ),
    Setting(
        'reddit_account_min_karma', description='Minimalna karma weryfikowanego konta na Reddicie',
        input_instruction='Wprowadź minimalną karmę weryfikowanego konta na Reddicie', value_type='int',
        default_value=0
    )
)


somsiad = Somsiad(ADDITIONAL_REQUIRED_SETTINGS)


def print_info(first_console_block=True):
    """Prints information about the bot to the console."""
    number_of_users = len(set(somsiad.bot.get_all_members()))
    number_of_servers = len(somsiad.bot.guilds)

    info_lines = [
        f'Obudzono Somsiada (ID {somsiad.bot.user.id}).',
        '',
        f'Połączono {TextFormatter.with_preposition_variant(number_of_users)} '
        f'{TextFormatter.word_number_variant(number_of_users, "użytkownikiem", "użytkownikami")} '
        f'na {TextFormatter.word_number_variant(number_of_servers, "serwerze", "serwerach")}:',
        *somsiad.list_of_servers(),
        '',
        'Link do zaproszenia bota:',
        somsiad.invite_url,
        '',
        somsiad.configurator.info(),
        '',
        f'Somsiad {__version__} • discord.py {discord.__version__} • Python {platform.python_version()}',
        '',
        'Copyright 2018 Habchy, ondondil & Twixes'
    ]

    print(TextFormatter.generate_console_block(info_lines, '== ', first_console_block=first_console_block))


@somsiad.bot.command(aliases=['nope', 'nie'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def no(ctx, member: discord.Member = None):
    """Removes the last message sent by the bot in the channel on the requesting user's request."""
    if member is None:
        member = ctx.author

    if member == ctx.author or ctx.author.permissions_in(ctx.channel).manage_messages:
        async for message in ctx.history(limit=10):
            if message.author == ctx.me and member in message.mentions:
                await message.delete()
                break


@somsiad.bot.command(aliases=['wersja'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def version(ctx):
    """Responds with current version of the bot."""
    await ctx.send(f'{ctx.author.mention}\n{__version__}')


@somsiad.bot.command()
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def ping(ctx):
    """Pong!"""
    await ctx.send(f'{ctx.author.mention}\n:ping_pong: Pong!')


@somsiad.bot.event
async def on_ready():
    """Does things once the bot comes online."""
    print_info()
    await somsiad.bot.change_presence(
        activity=discord.Game(name=f'Kiedyś to było | {somsiad.conf["command_prefix"]}pomocy')
    )


@somsiad.bot.event
async def on_guild_join(server):
    """Does things whenever the bot joins a server."""
    print_info(first_console_block=False)


@somsiad.bot.event
async def on_guild_remove(server):
    """Does things whenever the bot leaves a server."""
    print_info(first_console_block=False)


@somsiad.bot.event
async def on_command_error(ctx, error):
    """Handles command errors."""
    ignored_errors = (discord.ext.commands.CommandNotFound, discord.ext.commands.BadArgument)

    if ctx.command is not None:
        command_with_prefix = f'{somsiad.conf["command_prefix"]}{ctx.command.qualified_name}'

    if isinstance(error, ignored_errors):
        pass
    elif isinstance(error, discord.ext.commands.NoPrivateMessage):
        embed = discord.Embed(
            title=f':warning: Komenda {command_with_prefix} nie może być użyta '
            'w prywatnych wiadomościach',
            color=somsiad.color
        )
        await ctx.send(embed=embed)
    elif isinstance(error, discord.ext.commands.DisabledCommand):
        embed = discord.Embed(
            title=f':warning: Komenda jest wyłączona',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)
    else:
        somsiad.logger.error(
            f'Ignoring an exception of type {type(error)} in the {command_with_prefix} command used by {ctx.author} '
            f'on server {ctx.guild}: {error}'
        )
