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
    """Text formatting utilities."""
    @staticmethod
    def limit_text_length(text: str, limit: int) -> str:
        words = text.split()
        cut_text = ''
        for word in words:
            if len(cut_text) + len(word) <= limit:
                cut_text += word + ' '

        if cut_text[-2:] == '. ':
            cut_text = cut_text.rstrip()
        else:
            cut_text = cut_text.rstrip().rstrip(',') + '...'

        return cut_text

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
                (str(number)[-1] == '2' or str(number)[-1] == '3' or str(number)[-1] == '4')
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
                input_buffer = input(f'{setting.input_instruction_with_default_value}:\n').strip()
            else:
                input_buffer = input(f'{step_number}. {setting.input_instruction_with_default_value}:\n').strip()

            try:
                if input_buffer == '':
                    set_value = setting.set_value() # Set the setting's value using its default_value
                    if set_value is None: # If None was set then there must be no default_value to fall back to
                        print('Nie podano obowiązkowej wartości!')
                        was_setting_input = False
                    else:
                        was_setting_input = True
                else:
                    set_value = setting.set_value(input_buffer)
                    was_setting_input = True
            except ValueError:
                print('Podano wartość nieodpowiedniego typu!')
                was_setting_input = False

        self.write_setting(setting, set_value)

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

    def info(self) -> str:
        """Returns a string presenting the current configuration in a human-readable form."""
        if self.required_settings is None:
            return ''
        else:
            info = ''
            for setting in self.required_settings:
                # Handle the unit
                if setting.unit is None:
                    line = f'{setting}: {self.configuration[setting.name]}'
                elif setting.unit == 'password':
                    line = f'{setting}: {"*" * len(self.configuration[setting.name])}'
                elif isinstance(setting.unit, tuple) and len(setting.unit) == 2:
                    unit_variant = (
                        setting.unit[0] if int(somsiad.conf[setting.name]) == 1 else setting.unit[1]
                    )
                    line = f'{setting}: {self.configuration[setting.name]} {unit_variant}'
                else:
                    line = f'{setting}: {self.configuration[setting.name]} {setting.unit}'
                info += line + '\n'

            line = f'Ścieżka pliku konfiguracyjnego: {self.configuration_file_path}'
            info += line

            return info

    class Setting:
        """A setting used for configuration."""
        __slots__ = '_name', '_description', '_input_instruction', '_unit', '_value_type', '_default_value', '_value'

        def __init__(
                self, name: str, *, description: str, input_instruction: str, unit: Union[tuple, str] = None,
                value_type: str = None, default_value=None, value=None
        ):
            self._name = str(name)
            self._input_instruction = str(input_instruction)
            self._description = str(description)
            self._value_type = value_type
            self._default_value = None if default_value is None else self._convert_to_value_type(default_value)
            if unit is None:
                self._unit = None
            else:
                self._unit = tuple(map(str, unit)) if isinstance(unit, (list, tuple)) else str(unit)
            self._value = self._convert_to_value_type(value)

        def __repr__(self) -> str:
            return f'Setting(\'{self._name}\')'

        def __str__(self) -> str:
            return self._description

        def _convert_to_value_type(self, value):
            if value is not None:
                if self._value_type == 'str':
                    return str(value)
                elif self._value_type == 'int':
                    return int(value)
                elif self._value_type == 'float':
                    return float(value)
                else:
                    return value
            else:
                return None

        def as_dict(self) -> str:
            return {
                'name': self._name,
                'description': self._description,
                'input_instruction': self._input_instruction,
                'unit': self._unit,
                'value_type': self._value_type,
                'default_value': self._default_value,
                'value': self._value
            }

        @property
        def name(self) -> str:
            return self._name

        @property
        def description(self) -> str:
            return self._description

        @property
        def input_instruction(self) -> str:
            return self._input_instruction

        @property
        def default_value(self):
            return self._default_value

        @property
        def unit(self) -> Union[tuple, str]:
            return self._unit

        @property
        def value(self):
            return self._value

        @property
        def input_instruction_with_default_value(self) -> str:
            if self.default_value is None:
                return self.input_instruction
            else:
                return f'{self.input_instruction} (domyślnie {self.default_value})'

        @property
        def value_with_unit(self) -> str:
            if self._value is None:
                return 'brak'
            else:
                if isinstance(self._unit, (list, tuple)):
                    if self._value_type in ('int', 'float') and abs(self._value) == 1:
                        return f'{self._value} {self._unit[0]}'
                    else:
                        return f'{self._value} {self._unit[1]}'
                else:
                    return f'{self.input_instruction} {self._unit})'

        def set_value(self, value=None):
            if value is None:
                self._value = self._default_value
            else:
                self._value = self._convert_to_value_type(value)

            return self._value


class Somsiad:
    color = 0x7289da
    user_agent = f'SomsiadBot/{__version__}'

    bot_dir_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    storage_dir_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'somsiad')
    conf_dir_path = os.path.join(os.path.expanduser('~'), '.config')
    conf_file_path = os.path.join(conf_dir_path, 'somsiad.conf')

    logger = None
    configurator = None
    client = None
    user_converter = None
    member_converter = None

    message_autodestruction_time_in_seconds = 5
    message_autodestruction_notice = (
        'Ta wiadomość ulegnie autodestrukcji w ciągu '
        f'{TextFormatter.noun_variant(message_autodestruction_time_in_seconds, "sekundy", "sekund")} od wysłania.'
    )

    required_settings = [
        Configurator.Setting(
            'discord_token', description='Token bota', input_instruction='Wprowadź discordowy token bota',
            value_type='str'
        ),
        Configurator.Setting(
            'command_prefix', description='Prefiks komend', input_instruction='Wprowadź prefiks komend',
            value_type='str', default_value='!'
        ),
        Configurator.Setting(
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
        if not os.path.exists(self.storage_dir_path):
            os.makedirs(self.storage_dir_path)
        if not os.path.exists(self.conf_dir_path):
            os.makedirs(self.conf_dir_path)
        self.required_settings.extend(additional_required_settings)
        self.configurator = Configurator(self.conf_file_path, self.required_settings)
        self.client = Bot(
            description='Zawsze pomocny Somsiad',
            command_prefix=self.conf['command_prefix'],
            case_insensitive=True
        )
        self.client.remove_command('help') # Replaced with the 'help_direct' plugin
        self.member_converter = discord.ext.commands.MemberConverter()
        self.user_converter = discord.ext.commands.UserConverter()

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
            if server is not None:
                if len(server.name) > longest_server_name_length:
                    longest_server_name_length = len(server.name)
                days_since_joining_info = TextFormatter.human_readable_time_ago(server.me.joined_at)
                if len(days_since_joining_info) > longest_days_since_joining_info_length:
                    longest_days_since_joining_info_length = len(days_since_joining_info)

        for server in servers:
            if server is not None:
                days_since_joining_info = TextFormatter.human_readable_time_ago(server.me.joined_at)
                list_of_servers.append(
                    f'{server.name.ljust(longest_server_name_length)} - '
                    f'dołączono {days_since_joining_info.ljust(longest_days_since_joining_info_length)} - '
                    f'{TextFormatter.noun_variant(server.member_count, "użytkownik", "użytkowników")}'
                )

        return list_of_servers


# Plugin settings
ADDITIONAL_REQUIRED_SETTINGS = (
    Configurator.Setting(
        'google_key', description='Klucz API Google', input_instruction='Wprowadź klucz API Google', value_type='str'
    ),
    Configurator.Setting(
        'google_custom_search_engine_id', description='Identyfikator CSE Google',
        input_instruction='Wprowadź identyfikator CSE Google', value_type='str'
    ),
    Configurator.Setting(
        'goodreads_key', description='Klucz API Goodreads', input_instruction='Wprowadź klucz API Goodreads',
        value_type='str'
    ),
    Configurator.Setting(
        'giphy_key', description='Klucz API Giphy', input_instruction='Wprowadź klucz API Giphy', value_type='str'
    ),
    Configurator.Setting(
        'omdb_key', description='Klucz API OMDb', input_instruction='Wprowadź klucz API OMDb', value_type='str'
    ),
    Configurator.Setting(
        'reddit_id', description='ID aplikacji redditowej', input_instruction='Wprowadź ID aplikacji redditowej',
        value_type='str'
    ),
    Configurator.Setting(
        'reddit_secret', description='Szyfr aplikacji redditowej',
        input_instruction='Wprowadź szyfr aplikacji redditowej', value_type='str'
    ),
    Configurator.Setting(
        'reddit_username', description='Redditowa nazwa użytkownika',
        input_instruction='Wprowadź redditową nazwę użytkownika', value_type='str'
    ),
    Configurator.Setting(
        'reddit_password', description='Hasło do konta na Reddicie',
        input_instruction='Wprowadź hasło do konta na Reddicie', value_type='str'
    ),
    Configurator.Setting(
        'reddit_account_min_age_in_days', description='Minimalny wiek weryfikowanego konta na Reddicie',
        input_instruction='Wprowadź minimalny wiek weryfikowanego konta na Reddicie w dniach',
        unit=('dzień', 'dni'), value_type='int', default_value=14
    ),
    Configurator.Setting(
        'reddit_account_min_karma', description='Minimalna karma weryfikowanego konta na Reddicie',
        input_instruction='Wprowadź minimalną karmę weryfikowanego konta na Reddicie', value_type='int',
        default_value=0
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
    await ctx.send(f'{ctx.author.mention}\n{__version__}')


@somsiad.client.command()
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def ping(ctx):
    """Pong!"""
    await ctx.send(f'{ctx.author.mention}\n:ping_pong: Pong!')


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
