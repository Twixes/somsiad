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
import datetime
from typing import Union
import discord
from discord.ext.commands import Bot
from version import __version__


class TextFormatter:
    @staticmethod
    def with_preposition_variant(number: int) -> str:
        """Returns the gramatically correct variant of the 'with' preposition in Polish."""
        return 'ze' if 100 <= number < 200 else 'z'

    @staticmethod
    def noun_variant(number: int, singular_form: str, plural_form: str, *, include_number: bool = True) -> str:
        """Returns the gramatically correct variant of the given noun in Polish."""
        proper_form = singular_form if number == 1 else plural_form

        if include_number:
            return f'{number} {proper_form}'
        else:
            return proper_form

    @staticmethod
    def adjective_variant(
            number: int, singular_form: str, plural_form_2_to_4: str, plural_form_5_to_1: str,
            *, include_number: bool = True
    ) -> str:
        """Returns the gramatically correct variant of the given adjective in Polish."""
        if number == 1:
            proper_form = singular_form
        elif (
                (str(number)[-1:] == '2' or str(number)[-1:] == '3' or str(number)[-1:] == '4')
                and number not in (12, 13, 14)
        ):
            proper_form = plural_form_2_to_4
        else:
            proper_form = plural_form_5_to_1

        if include_number:
            return f'{number} {proper_form}'
        else:
            return proper_form

    @classmethod
    def human_readable_time_ago(cls, utc_datetime: datetime.datetime, *, date=True, time=True, days=True) -> str:
        local_datetime = utc_datetime.replace(tzinfo=datetime.timezone.utc).astimezone()
        delta = datetime.datetime.now().astimezone() - local_datetime

        combined_information = []
        if date:
            date_string = local_datetime.strftime('%d.%m.%Y')
            combined_information.append(date_string)
        if time:
            time_string = local_datetime.strftime('%H:%M')
            if date:
                combined_information.append(f' o {time_string}')
            else:
                combined_information.append(time_string)
        if days:
            days_since = delta.days
            if days_since == 0:
                days_since_string = 'dzisiaj'
            elif days_since == 1:
                days_since_string = 'wczoraj'
            else:
                days_since_string = f'{cls.noun_variant(days_since, "dzień", "dni")} temu'

            if date or time:
                combined_information.append(f', {days_since_string}')
            else:
                combined_information.append(days_since_string)

        return ''.join(combined_information)

    @staticmethod
    def separator(block: str, width: int = os.get_terminal_size()[0]) -> str:
        """Generates a separator string to the specified length out of given blocks. Can print to the console."""
        pattern = (block * int(width / len(block)) + block)[:width].strip()
        return pattern

    @classmethod
    def generate_console_block(
            cls, info_lines: list, separator_block: str = None, *, first_console_block: bool = True
    ) -> str:
        """Takes a list of lines and returns a string ready for printing in the console."""
        info_block = []
        separator = None
        if separator_block is not None:
            separator = cls.separator(separator_block)
        if separator is not None and first_console_block:
            info_block.append(separator)
        for line in info_lines:
            info_block.append(line)
        if separator is not None:
            info_block.append(separator)

        return '\n'.join(info_block)


class Configurator:
    """Handles bot configuration."""
    def __init__(self, configuration_file_path: str, required_settings: tuple = None):
        self.configuration_file_path = configuration_file_path
        self.required_settings = required_settings
        self.configuration = {}

        self.ensure_completeness()

    def write_setting(self, setting, value):
        """Writes a key-value pair to the configuration file."""
        self.configuration[setting.name] = value
        with open(self.configuration_file_path, 'a') as configuration_file:
            configuration_file.write(f'{setting.name}={self.configuration[setting.name]}\n')

    def input_setting(self, setting, step_number: int = None):
        """Asks the CLI user to input a setting."""
        was_setting_input = False

        while not was_setting_input:
            if step_number is None:
                buffer = input(f'{setting.input_instruction}:\n').strip()
            else:
                buffer = input(f'{step_number}. {setting.input_instruction}:\n').strip()

            if buffer == '':
                if setting.default_value is None:
                    was_setting_input = False
                else:
                    buffer = str(setting.default_value).strip()
                    was_setting_input = True
            else:
                was_setting_input = True

        self.write_setting(setting, buffer)

    def ensure_completeness(self) -> dict:
        """Loads the configuration from the file specified during class initialization and ensures
        that all required keys are present. If not, the CLI user is asked to input missing settings.
        If the file doesn't exist yet, configuration is started from scratch.
        """
        was_configuration_changed = False
        step_number = 1

        if os.path.exists(self.configuration_file_path):
            self.load()

        if self.required_settings is not None:
            if not self.configuration:
                for required_setting in self.required_settings:
                    self.input_setting(required_setting, step_number)
                    step_number += 1
                was_configuration_changed = True
            else:
                for required_setting in self.required_settings:
                    is_setting_present = False
                    for setting in self.configuration:
                        if setting == required_setting.name:
                            is_setting_present = True
                            break
                    if not is_setting_present:
                        self.input_setting(required_setting, step_number)
                        was_configuration_changed = True
                    step_number += 1

        if was_configuration_changed:
            print(f'Gotowe! Konfigurację zapisano w {self.configuration_file_path}.')

        return self.configuration

    def load(self) -> dict:
        """Loads the configuration from the file specified during class initialization."""
        with open(self.configuration_file_path, 'r') as configuration_file:
            for line in configuration_file.readlines():
                if not line.strip().startswith('#'):
                    line = line.strip().split('=', 1)
                    self.configuration[line[0].strip()] = line[1]

        return self.configuration

    def info(self):
        """Returns a string presenting the current configuration in a human-readable form."""
        if self.required_settings is not None:
            info = ''
            for setting in self.required_settings:
                # Handle the unit
                if setting.unit is None:
                    line = f'{setting.description}: {self.configuration[setting.name]}'
                elif setting.unit == 'password':
                    line = f'{setting.description}: {"*" * len(self.configuration[setting.name])}'
                elif isinstance(setting.unit, tuple) and len(setting.unit) == 2:
                    unit_variant = (
                        setting.unit[0] if int(somsiad.conf[setting.name]) == 1 else setting.unit[1]
                    )
                    line = f'{setting.description}: {self.configuration[setting.name]} {unit_variant}'
                else:
                    line = f'{setting.description}: {self.configuration[setting.name]} {setting.unit}'
                info += line + '\n'

            line = f'Ścieżka pliku konfiguracyjnego: {self.configuration_file_path}'
            info += line

            return info
        else:
            return None

    class SettingTemplate:
        """A bot setting template."""
        def __init__(
                self, name: str, description: str, input_instruction: str, default_value=None,
                unit: Union[tuple, str] = None
        ):
            self.name = name
            self.input_instruction = input_instruction
            self.description = description
            self.default_value = default_value
            self.unit = unit


class Somsiad:
    color = 0x7289da
    user_agent = f'SomsiadBot/{__version__}'
    bot_dir_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    storage_dir_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'somsiad')
    conf_dir_path = os.path.join(os.path.expanduser('~'), '.config')
    conf_file_path = os.path.join(conf_dir_path, 'somsiad.conf')
    logger = None
    member_converter = None
    configurator = None
    client = None

    _ESSENTIAL_REQUIRED_SETTINGS = (
        Configurator.SettingTemplate(
            'discord_token', 'Token bota', 'Wprowadź discordowy token bota'
        ),
        Configurator.SettingTemplate(
            'command_prefix', 'Prefiks komend', 'Wprowadź prefiks komend (domyślnie !)', '!'
        ),
        Configurator.SettingTemplate(
            'command_cooldown_per_user_in_seconds', 'Cooldown wywołania komendy przez użytkownika',
            'Wprowadź cooldown wywołania komendy przez użytkownika (w sekundach, domyślnie 1)', 1, ('sekunda', 'sekund')
        )
    )

    def __init__(self, additional_required_settings):
        self.logger = logging.getLogger()
        logging.basicConfig(
            filename=os.path.join(self.bot_dir_path, 'somsiad.log'),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        if not os.path.exists(self.storage_dir_path):
            os.makedirs(self.storage_dir_path)
        if not os.path.exists(self.conf_dir_path):
            os.makedirs(self.conf_dir_path)
        combined_required_settings = self._ESSENTIAL_REQUIRED_SETTINGS + additional_required_settings
        self.configurator = Configurator(self.conf_file_path, combined_required_settings)
        self.client = Bot(
            description='Zawsze pomocny Somsiad',
            command_prefix=self.conf['command_prefix'],
            case_insensitive=True
        )
        self.client.remove_command('help') # Replaced with the 'help_direct' plugin
        self.member_converter = discord.ext.commands.MemberConverter()

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
        servers = sorted(self.client.guilds, key=lambda server: server.me.joined_at, reverse=True)
        longest_server_name_length = 0
        longest_days_since_joining_info_length = 0
        list_of_servers = []

        for server in servers:
            if server.me is not None:
                if len(server.name) > longest_server_name_length:
                    longest_server_name_length = len(server.name)
                days_since_joining_info = TextFormatter.human_readable_time_ago(server.me.joined_at)
                if len(days_since_joining_info) > longest_days_since_joining_info_length:
                    longest_days_since_joining_info_length = len(days_since_joining_info)

        for server in servers:
            if server.me is not None:
                days_since_joining_info = TextFormatter.human_readable_time_ago(server.me.joined_at)
                list_of_servers.append(
                    f'{server.name.ljust(longest_server_name_length)} - '
                    f'dołączono {days_since_joining_info.ljust(longest_days_since_joining_info_length)} - '
                    f'{TextFormatter.noun_variant(server.member_count, "użytkownik", "użytkowników")}'
                )

        return list_of_servers

    async def is_user_bot_owner(self, user: Union[discord.User, discord.Member]) -> bool:
        """Returns whether the provided user/member is the owner of this instance of the bot."""
        application_info = await self.client.application_info()
        return application_info.owner == user


# Plugin settings
ADDITIONAL_REQUIRED_SETTINGS = (
    Configurator.SettingTemplate(
        'google_key', 'Klucz API Google', 'Wprowadź klucz API Google'
    ),
    Configurator.SettingTemplate(
        'google_custom_search_engine_id', 'Identyfikator CSE Google', 'Wprowadź identyfikator CSE Google'
    ),
    Configurator.SettingTemplate(
        'goodreads_key', 'Klucz API Goodreads', 'Wprowadź klucz API Goodreads'
    ),
    Configurator.SettingTemplate(
        'giphy_key', 'Klucz API Giphy', 'Wprowadź klucz API Giphy'
    ),
    Configurator.SettingTemplate(
        'omdb_key', 'Klucz API OMDb', 'Wprowadź klucz API OMDb'
    ),
    Configurator.SettingTemplate(
        'reddit_id', 'ID aplikacji redditowej', 'Wprowadź ID aplikacji redditowej'
    ),
    Configurator.SettingTemplate(
        'reddit_secret', 'Szyfr aplikacji redditowej', 'Wprowadź szyfr aplikacji redditowej'
    ),
    Configurator.SettingTemplate(
        'reddit_username', 'Redditowa nazwa użytkownika', 'Wprowadź redditową nazwę użytkownika'
    ),
    Configurator.SettingTemplate(
        'reddit_password', 'Hasło do konta na Reddicie', 'Wprowadź hasło do konta na Reddicie', unit='password'
    ),
    Configurator.SettingTemplate(
        'reddit_account_min_age_in_days', 'Minimalny wiek weryfikowanego konta na Reddicie',
        'Wprowadź minimalny wiek weryfikowanego konta na Reddicie (w dniach, domyślnie 14)', 14, ('dzień', 'dni')
    ),
    Configurator.SettingTemplate(
        'reddit_account_min_karma', 'Minimalna karma weryfikowanego konta na Reddicie',
        'Wprowadź minimalną karmę weryfikowanego konta na Reddicie (domyślnie 0)', 0
    )
)

somsiad = Somsiad(ADDITIONAL_REQUIRED_SETTINGS)


def print_info(first_console_block=True):
    """Prints information about the bot to the console."""
    number_of_users = len(set(somsiad.client.get_all_members()))
    number_of_servers = len(somsiad.client.guilds)

    info_lines = [
        f'Obudzono Somsiada (ID {somsiad.client.user.id}).',
        '',
        f'Połączono {TextFormatter.with_preposition_variant(number_of_users)} '
        f'{TextFormatter.noun_variant(number_of_users, "użytkownikiem", "użytkownikami")} '
        f'na {TextFormatter.noun_variant(number_of_servers, "serwerze", "serwerach")}:',
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
async def version(ctx):
    """Responds with current version of the bot."""
    await ctx.send(__version__)


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
async def on_guild_join(guild):
    """Does things whenever the bot joins a server."""
    print_info(first_console_block=False)


@somsiad.client.event
async def on_guild_remove(guild):
    """Does things whenever the bot leaves a server."""
    print_info(first_console_block=False)


@somsiad.client.event
async def on_command_error(ctx, error):
    """Handles common command errors."""
    if isinstance(error, discord.ext.commands.NoPrivateMessage):
        embed = discord.Embed(
            title=f':warning: Komenda {somsiad.conf["command_prefix"]}{ctx.invoked_with} nie może być użyta '
            'w prywatnych wiadomościach.',
            color=somsiad.color
        )
        await ctx.send(embed=embed)
    elif isinstance(error, discord.ext.commands.DisabledCommand):
        await ctx.send(f'Komenda {somsiad.conf["command_prefix"]}{ctx.invoked_with} została wyłączona.')

    somsiad.logger.error(
        f'Ignoring an exception in the {somsiad.conf["command_prefix"]}{ctx.invoked_with} command '
        f'used by {ctx.author} on {ctx.guild}: {error}.'
    )
