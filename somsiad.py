# Copyright 2018 Habchy, ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import os
import platform
import logging
import datetime
from typing import Union
import discord
from discord.ext.commands import Bot
from version import __version__


class TextFormatter:
    @staticmethod
    def with_preposition_variant(number: int):
        """Returns the gramatically correct variant of the 'with' preposition in Polish."""
        return 'ze' if 100 <= number < 200 else 'z'

    @staticmethod
    def noun_variant(number: int, singular_form: str, plural_form: str):
        """Returns the gramatically correct variant of the given noun in Polish."""
        return singular_form if number == 1 else plural_form

    @staticmethod
    def adjective_variant(number: int, singular_form: str, plural_form_2_to_4: str, plural_form_5_to_1: str):
        """Returns the gramatically correct variant of the given adjective in Polish."""
        if number == 1:
            return singular_form
        elif (
                (str(number)[-1:] == '2' or str(number)[-1:] == '3' or str(number)[-1:] == '4')
                and number not in (12, 13, 14)
        ):
            return plural_form_2_to_4
        else:
            return plural_form_5_to_1

    @staticmethod
    def separator(block: str, width: int) -> str:
        """Generates a separator string to the specified length out of given blocks. Can print to the console."""
        pattern = (block * int(width / len(block)) + block)[:width].strip()
        return pattern

    @classmethod
    def generate_console_block(
            cls, info_lines: list, separator_block: str = None, first_console_block: bool = True
    ) -> str:
        """Takes a list of lines and returns a string ready for printing in the console."""
        info_block = []
        separator = None
        if separator_block is not None:
            separator = cls.separator(separator_block, os.get_terminal_size()[0])
        if separator is not None and first_console_block:
            info_block.append(separator)
        for line in info_lines:
            info_block.append(line)
        if separator is not None:
            info_block.append(separator)

        return '\n'.join(info_block)


class Configurator:
    configuration_file_path = None
    configuration_file = None
    configuration_required = None
    configuration = {}

    def __init__(self, configuration_file_path, configuration_required=None):
        self.configuration_file_path = configuration_file_path
        self.configuration_required = configuration_required

        if configuration_required is None:
            self.load()
        else:
            self.ensure_completeness()

    def write_key_value(self, key):
        """Writes a key-value pair to the configuration file."""
        with open(self.configuration_file_path, 'a') as self.configuration_file:
            self.configuration_file.write(f'{key}={self.configuration[key]}\n')

    def obtain_key_value(self, key, default_value, instruction, step_number=None):
        """Asks the CLI user to input a setting."""
        while True:
            if step_number is None:
                self.configuration[key] = input(f'{instruction}:\n')
            else:
                self.configuration[key] = input(f'{step_number}. {instruction}:\n')

            if self.configuration[key].strip() == '':
                if default_value is None:
                    continue
                else:
                    self.configuration[key] = default_value
                    break
            else:
                break

        self.write_key_value(key)

    def ensure_completeness(self):
        """Loads the configuration from the file specified during class initialization and ensures
        that all required keys are present. If not, the CLI user is asked to input missing settings.
        If the file doesn't exist yet, configuration is started from scratch.
        """
        was_configuration_changed = False
        step_number = 1

        if os.path.exists(self.configuration_file_path):
            self.load()

        if self.configuration_required is not None:
            if not self.configuration:
                for key_required in self.configuration_required:
                    self.obtain_key_value(key_required[0], key_required[1], key_required[2], step_number)
                    step_number += 1
                was_configuration_changed = True
            else:
                for key_required in self.configuration_required:
                    is_key_required_present = False
                    for key in self.configuration:
                        if key == key_required[0]:
                            is_key_required_present = True
                            break
                    if not is_key_required_present:
                        self.obtain_key_value(key_required[0], key_required[1], key_required[2], step_number)
                        was_configuration_changed = True
                    step_number += 1

        if was_configuration_changed:
            print(f'Gotowe! Konfigurację zapisano w {self.configuration_file_path}.')

        return self.configuration

    def load(self):
        """Loads the configuration from the file specified during class initialization."""
        with open(self.configuration_file_path, 'r') as self.configuration_file:
            for line in self.configuration_file.readlines():
                if not line.strip().startswith('#'):
                    line = line.strip().split('=')
                    self.configuration[line[0].strip()] = line[1].strip() if len(line) >= 2 else None

        return self.configuration

    def info(self):
        """Returns a string presenting the current configuration in a human-readable form."""
        if self.configuration_required is not None:
            info = ''
            for key_required in self.configuration_required:
                if key_required[4] is None:
                    line = f'{key_required[3]}: {self.configuration[key_required[0]]}'
                elif key_required[4] == 'password':
                    line = f'{key_required[3]}: {"*" * len(self.configuration[key_required[0]])}'
                elif isinstance(key_required[4], tuple) and len(key_required[4]) == 2:
                    unit_noun_variant = (
                        key_required[4][0] if int(somsiad.conf[key_required[0]]) == 1 else key_required[4][1]
                    )
                    line = f'{key_required[3]}: {self.configuration[key_required[0]]} {unit_noun_variant}'
                else:
                    line = f'{key_required[3]}: {self.configuration[key_required[0]]} {key_required[4]}'
                info += line + '\n'

            line = f'Ścieżka pliku konfiguracyjnego: {self.configuration_file_path}'
            info += line

            return info

        return None


class Somsiad:
    color = 0x7289da
    user_agent = f'SomsiadBot/{__version__}'
    bot_dir_path = os.getcwd()
    storage_dir_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'somsiad')
    conf_dir_path = os.path.join(os.path.expanduser('~'), '.config')
    conf_file_path = os.path.join(conf_dir_path, 'somsiad.conf')
    logger = logging.getLogger()
    member_converter = discord.ext.commands.MemberConverter()
    configurator = None
    client = None

    def __init__(self, required_configuration_extension):
        logging.basicConfig(
            filename='somsiad.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        if not os.path.exists(self.storage_dir_path):
            os.makedirs(self.storage_dir_path)
        if not os.path.exists(self.conf_dir_path):
            os.makedirs(self.conf_dir_path)
        required_configuration = [
            # (key, default_value, instruction, description, unit)
            ('discord_token', None, 'Wprowadź discordowy token bota', 'Token bota', None),
            ('command_prefix', '!', 'Wprowadź prefiks komend (domyślnie !)', 'Prefiks komend', None),
            (
                'command_cooldown_per_user_in_seconds', 1, 'Wprowadź cooldown wywołania komendy przez użytkownika '
                '(w sekundach, domyślnie 1)', 'Cooldown wywołania komendy przez użytkownika', ('sekunda', 'sekund')
            )
        ]
        for setting in required_configuration_extension:
            required_configuration.append(setting)
        self.configurator = Configurator(self.conf_file_path, required_configuration)
        self.client = Bot(
            description='Zawsze pomocny Somsiad',
            command_prefix=self.conf['command_prefix'],
            case_insensitive=True
        )
        self.client.remove_command('help') # Replaced with the 'help_direct' plugin

    def run(self):
        """Launches the bot."""
        try:
            self.client.run(somsiad.conf['discord_token'])
            self.logger.info('Client online.')
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
            return discord.utils.oauth_url(self.client.user.id, discord.Permissions(536083543))
        except discord.errors.ClientException:
            return None

    def list_of_servers(self):
        """Generates a list of servers the bot is connected to, including the number of days since joining
        and the number of users.
        """
        servers = sorted(self.client.guilds, key=lambda server: len(server.members), reverse=True)
        longest_server_name_length = 0
        longest_days_since_joining_info_length = 0
        list_of_servers = []

        for server in servers:
            if server.me is not None:
                if len(server.name) > longest_server_name_length:
                    longest_server_name_length = len(server.name)
                date_of_joining = server.me.joined_at.replace(tzinfo=datetime.timezone.utc).astimezone()
                days_since_joining = (datetime.datetime.now().astimezone() - date_of_joining).days
                days_since_joining_info = (
                    f'{days_since_joining} {TextFormatter.noun_variant(days_since_joining, "dnia", "dni")}'
                )
                if len(days_since_joining_info) > longest_days_since_joining_info_length:
                    longest_days_since_joining_info_length = len(days_since_joining_info)

        for server in servers:
            if server.me is not None:
                date_of_joining = server.me.joined_at.replace(tzinfo=datetime.timezone.utc).astimezone()
                days_since_joining = (datetime.datetime.now().astimezone() - date_of_joining).days
                days_since_joining_info = (
                    f'{days_since_joining} {TextFormatter.noun_variant(days_since_joining, "dnia", "dni")}'
                )
                list_of_servers.append(
                    f'{server.name.ljust(longest_server_name_length)} - '
                    f'od {days_since_joining_info.ljust(longest_days_since_joining_info_length)} - '
                    f'{server.member_count} '
                    f'{TextFormatter.noun_variant(server.member_count, "użytkownik", "użytkowników")}'
                )

        return list_of_servers

    async def is_user_bot_owner(self, user: Union[discord.User, discord.Member]) -> bool:
        """Returns whether the provided user/member is the owner of this instance of the bot."""
        application_info = await self.client.application_info()
        return application_info.owner == user


# Required configuration
required_configuration_extension = [
    # (key, default_value, instruction, description, unit)
    ('google_key', None, 'Wprowadź klucz API Google', 'Klucz API Google', None),
    ('google_custom_search_engine_id', None, 'Wprowadź identyfikator CSE Google', 'Identyfikator CSE Google', None),
    ('goodreads_key', None, 'Wprowadź klucz API Goodreads', 'Klucz API Goodreads', None),
    ('giphy_key', None, 'Wprowadź klucz API Giphy', 'Klucz API Giphy', None),
    ('reddit_id', None, 'Wprowadź ID aplikacji redditowej', 'ID aplikacji redditowej', None),
    ('reddit_secret', None, 'Wprowadź szyfr aplikacji redditowej', 'Szyfr aplikacji redditowej', None),
    ('reddit_username', None, 'Wprowadź redditową nazwę użytkownika', 'Redditowa nazwa użytkownika', None),
    ('reddit_password', None, 'Wprowadź hasło do konta na Reddicie', 'Hasło do konta na Reddicie', 'password'),
    ('reddit_account_min_age_in_days', 14, 'Wprowadź minimalny wiek weryfikowanego konta na Reddicie '
        '(w dniach, domyślnie 14)', 'Minimalny wiek weryfikowanego konta na Reddicie', ('dzień', 'dni')),
    ('reddit_account_min_karma', 0, 'Wprowadź minimalną karmę weryfikowanego konta na Reddicie (domyślnie 0)',
        'Minimalna karma weryfikowanego konta na Reddicie', None)
]

somsiad = Somsiad(required_configuration_extension)


def print_info(first_console_block=True):
    """Prints information about the bot to the console."""
    number_of_users = len(set(somsiad.client.get_all_members()))
    number_of_servers = len(somsiad.client.guilds)

    info_lines = [
        f'Obudzono Somsiada (ID {somsiad.client.user.id}).',
        '',
        f'Połączono {TextFormatter.with_preposition_variant(number_of_users)} {number_of_users} '
        f'{TextFormatter.noun_variant(number_of_users, "użytkownikiem", "użytkownikami")} na {number_of_servers} '
        f'{TextFormatter.noun_variant(number_of_servers, "serwerze", "serwerach")}:',
        '\n'.join(somsiad.list_of_servers()),
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


@somsiad.client.command(aliases=['wersja'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def version(ctx):
    """Responds with current version of the bot."""
    if ctx.channel.permissions_for(ctx.author).manage_roles:
        version_string = f'{__version__}!'
    else:
        version_string = __version__
    await ctx.send(version_string)


@somsiad.client.command()
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def ping(ctx):
    """Pong!"""
    await ctx.send(':ping_pong: Pong!')


@somsiad.client.event
async def on_ready():
    """Does things once the bot comes online."""
    print_info()
    await somsiad.client.change_presence(
        activity=discord.Game(name=f'Kiedyś to było | {somsiad.conf["command_prefix"]}pomocy')
    )


@somsiad.client.event
async def on_guild_join():
    """Does things whenever the bot joins a server."""
    print_info(first_console_block=False)


@somsiad.client.event
async def on_guild_remove():
    """Does things whenever the bot leaves a server."""
    print_info(first_console_block=False)


@somsiad.client.event
async def on_command_error(ctx, error):
    """Handles common command errors."""
    if isinstance(error, (discord.ext.commands.CommandNotFound, discord.ext.commands.UserInputError)):
        pass
    elif isinstance(error, discord.ext.commands.DisabledCommand):
        await ctx.send(f'Komenda {ctx.command} została wyłączona.')
    elif isinstance(error, discord.ext.commands.NoPrivateMessage):
        embed = discord.Embed(
            title=f':warning: Komenda {somsiad.conf["command_prefix"]}{ctx.command} nie może zostać użyta w prywatnej '
            'wiadomości.',
            color=somsiad.color
        )
        await ctx.author.send(embed=embed)

    somsiad.logger.error(
        f'Ignoring an exception in the {somsiad.conf["command_prefix"]}{ctx.command} command: {error}.'
    )
