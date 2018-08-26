# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import os
import logging
import datetime
import discord
from discord.ext.commands import Bot
from version import __version__


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

    def write_key_value(self, key, value):
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

        self.write_key_value(key, self.configuration[key])

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
            if self.configuration is {} or self.configuration is None:
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

    def info(self, verbose=False):
        """Returns a string presenting the current configuration in a human-readable form. Can print to the console."""
        if self.configuration_required is not None:
            info = ''
            for key_required in self.configuration_required:
                if key_required[4] is None:
                    line = f'{key_required[3]}: {self.configuration[key_required[0]]}'
                elif key_required[4] == 'password':
                    line = f'{key_required[3]}: {"*" * len(self.configuration[key_required[0]])}'
                elif isinstance(key_required[4], tuple) and len(key_required[4]) == 2:
                    unit_noun_variant = (key_required[4][0] if int(somsiad.conf[key_required[0]]) == 1 else
                        key_required[4][1])
                    line = f'{key_required[3]}: {self.configuration[key_required[0]]} {unit_noun_variant}'
                else:
                    line = f'{key_required[3]}: {self.configuration[key_required[0]]} {key_required[4]}'
                info += line + '\n'
                if verbose:
                    print(line)

            line = f'Ścieżka pliku konfiguracyjnego: {self.configuration_file_path}'
            info += line
            if verbose:
                print(line)

            return info


class Informator:
    @staticmethod
    def with_preposition_variant(number):
        return 'ze' if number >= 100 and number < 200 else 'z'

    @staticmethod
    def noun_variant(number, singular_form, plural_form):
        return singular_form if number == 1 else plural_form

    @staticmethod
    def adjective_variant(number, singular_form, plural_form_2_to_4, plural_form_5_to_1):
        if number == 1:
            return singular_form
        elif ((number != 12 and number != 13 and number != 14) and
                (str(number)[:1] == '2' or str(number)[:1] == '3' or str(number)[:1] == '4')):
            return plural_form_2_to_4
        else:
            return plural_form_5_to_1

    @staticmethod
    def separator(block, width, verbose=False):
        """Generates a separator string to the specified length out of given blocks. Can print to the console."""
        pattern = (block * int(width / len(block)) + block)[:width].strip()
        if verbose:
            print(pattern)
        return pattern

    def list_of_servers(self, client, verbose=False):
        """Generates a list of servers the bot is connected to, including the number of days since joining and
        the number of users. Can print to the console.
        """
        servers = sorted(client.guilds, key=lambda server: len(server.members), reverse=True)
        longest_server_name_length = 0
        longest_days_since_joining_info_length = 0
        list_of_servers = []

        for server in servers:
            if server.me is not None:
                if len(server.name) > longest_server_name_length:
                    longest_server_name_length = len(server.name)
                date_of_joining = server.me.joined_at.replace(tzinfo=datetime.timezone.utc).astimezone()
                days_since_joining = (datetime.datetime.now().astimezone() - date_of_joining).days
                days_since_joining_info = (f'{days_since_joining} '
                    f'{self.noun_variant(days_since_joining, "dnia", "dni")}')
                if len(days_since_joining_info) > longest_days_since_joining_info_length:
                    longest_days_since_joining_info_length = len(days_since_joining_info)

        for server in servers:
            if server.me is not None:
                date_of_joining = server.me.joined_at.replace(tzinfo=datetime.timezone.utc).astimezone()
                days_since_joining = (datetime.datetime.now().astimezone() - date_of_joining).days
                days_since_joining_info = (f'{days_since_joining} '
                    f'{self.noun_variant(days_since_joining, "dnia", "dni")}')
                list_of_servers.append(f'{server.name.ljust(longest_server_name_length)} - '
                    f'od {days_since_joining_info.ljust(longest_days_since_joining_info_length)} - '
                    f'{server.member_count} '
                    f'{self.noun_variant(server.member_count, "użytkownik", "użytkowników")}')

        list_of_servers = '\n'.join(list_of_servers)

        if verbose:
            print(list_of_servers)

        return list_of_servers

    def info(self, lines, separator_block=None, verbose=False):
        """Takes a list of lines containing bot information and returns a string ready for printing.
        Can print to the console.
        """
        info = ''
        if separator_block is not None:
            separator = self.separator(separator_block, os.get_terminal_size()[0])
            if verbose: print(separator)
        for line in lines:
            info += line + '\n'
            if verbose:
                print(line)
        if separator_block is not None and verbose:
            print(separator)
        info = info.strip('\n')
        return info


class Somsiad:
    color = 0x7289da
    user_agent = f'SomsiadBot/{__version__}'
    bot_dir_path = os.getcwd()
    storage_dir_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'somsiad')
    conf_dir_path = os.path.join(os.path.expanduser('~'), '.config')
    conf_file_path = os.path.join(conf_dir_path, 'somsiad.conf')
    logger = None
    configurator = None
    conf = None
    client = None

    def __init__(self, conf_required_extension):
        logging.basicConfig(
            filename='somsiad.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger()
        if not os.path.exists(self.storage_dir_path):
            os.makedirs(self.storage_dir_path)
        if not os.path.exists(self.conf_dir_path):
            os.makedirs(self.conf_dir_path)
        conf_required = [
            # (key, default_value, instruction, description, unit,)
            ('discord_token', None, 'Wprowadź discordowy token bota', 'Token bota', None,),
            ('command_prefix', '!', 'Wprowadź prefiks komend (domyślnie !)', 'Prefiks komend', None,),
            ('user_command_cooldown_seconds', 1, 'Wprowadź cooldown wywołania komendy przez użytkownika '
                '(w sekundach, domyślnie 1)', 'Cooldown wywołania komendy przez użytkownika', ('sekunda', 'sekund',),),
        ]
        for setting in conf_required_extension:
            conf_required.append(setting)
        self.configurator = Configurator(self.conf_file_path, conf_required)
        self.conf = self.configurator.configuration
        self.client = Bot(
            description='Zawsze pomocny Somsiad',
            command_prefix=self.conf['command_prefix'],
            case_insensitive=True
        )

    def run(self):
        try:
            self.client.run(somsiad.conf['discord_token'])
            self.logger.info('Client online.')
        except discord.errors.ClientException:
            self.logger.critical('Client could not come online! The Discord bot token provided may be faulty.')

    @staticmethod
    def does_member_have_elevated_permissions(member):
        return member.guild_permissions.administrator


# Required configuration
conf_required_extension = [
    # (key, default_value, instruction, description, unit,)
    ('google_key', None, 'Wprowadź klucz API Google', 'Klucz API Google', None,),
    ('google_custom_search_engine_id', None, 'Wprowadź identyfikator CSE Google', 'Identyfikator CSE Google', None,),
    ('goodreads_key', None, 'Wprowadź klucz API Goodreads', 'Klucz API Goodreads', None,),
    ('giphy_key', None, 'Wprowadź klucz API Giphy', 'Klucz API Giphy', None,),
    ('reddit_id', None, 'Wprowadź ID aplikacji redditowej', 'ID aplikacji redditowej', None,),
    ('reddit_secret', None, 'Wprowadź szyfr aplikacji redditowej', 'Szyfr aplikacji redditowej', None,),
    ('reddit_username', None, 'Wprowadź redditową nazwę użytkownika', 'Redditowa nazwa użytkownika', None,),
    ('reddit_password', None, 'Wprowadź hasło do konta na Reddicie', 'Hasło do konta na Reddicie', 'password',),
    ('reddit_account_min_age_days', 14, 'Wprowadź minimalny wiek weryfikowanego konta na Reddicie '
        '(w dniach, domyślnie 14)', 'Minimalny wiek weryfikowanego konta na Reddicie', ('dzień', 'dni',),),
    ('reddit_account_min_karma', 0, 'Wprowadź minimalną karmę weryfikowanego konta na Reddicie (domyślnie 0)',
        'Minimalna karma weryfikowanego konta na Reddicie', None,),
]


somsiad = Somsiad(conf_required_extension)


somsiad.client.remove_command('help') # Replaced with the 'help_direct' plugin
