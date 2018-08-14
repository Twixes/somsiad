# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from discord.ext.commands import Bot
import os

brand_color = 0x7289da
bot_dir = os.getcwd()

class Configurator:
    step_number = None
    configuration_file = None
    configuration = {}

    def __init__(self, configuration_file):
        self.configuration_file = configuration_file

    def write_key_value_pair(self, key, default_value, instruction):
        while True:
            self.configuration[key] = input(f'{self.step_number}. {instruction}:\n')
            if self.configuration[key].strip() == '':
                if default_value == None:
                    continue
                else:
                    self.configuration[key] = default_value
                    break
            else:
                break
        self.configuration_file.write(f'{key}={self.configuration[key]}\n')
        self.step_number += 1

    def assure_completeness(self, configuration_required, configuration = {}):
        self.step_number = 1
        if configuration is {}:
            for item_required in configuration_required:
                self.write_key_value_pair(item_required[0], item_required[1], item_required[2])
                self.step_number += 1
        else:
            self.configuration = configuration
            for item_required in configuration_required:
                is_required_item_present = False
                for item in conf:
                    if item == item_required[0]:
                        is_required_item_present = True
                        break
                if not is_required_item_present:
                    self.write_key_value_pair(item_required[0], item_required[1], item_required[2])
                self.step_number += 1
        return self.configuration

    def read(self):
        for line in self.configuration_file.readlines():
            line = line.strip().split('=')
            self.configuration[line[0].strip()] = line[1].strip()
        return self.configuration

conf_required = (
    ('discord_token', None, 'Wprowadź discordowy token bota',),
    ('google_key', None, 'Wprowadź klucz API Google',),
    ('reddit_id', None, 'Wprowadź ID aplikacji redditowej',),
    ('reddit_secret', None, 'Wprowadź szyfr aplikacji redditowej',),
    ('reddit_username', None, 'Wprowadź redditową nazwę użytkownika',),
    ('reddit_password', None, 'Wprowadź hasło do konta na Reddicie',),
    ('reddit_account_minimum_age_days', 14, 'Wprowadź minimalny wiek weryfikowanego konta na Reddicie '
        '(w dniach, domyślnie 14)',),
    ('reddit_account_minimum_karma', 0, 'Wprowadź minimalną karmę weryfikowanego konta na Reddicie (domyślnie 0)',),
    ('user_command_cooldown_seconds', 1, 'Wprowadź cooldown między wywołaniami komendy przez danego użytkownika '
        '(w sekundach, domyślnie 1)',),
    ('command_prefix', '!', 'Wprowadź prefiks komend (domyślnie !)',),
)

# Check whether the configuration file exists
# If it doesn't, create it and configure on first run
conf_file_path = os.path.join(os.path.expanduser('~'), '.config', 'somsiad.conf')
if not os.path.exists(conf_file_path):
    with open(conf_file_path, 'w') as f:
        configurator = Configurator(f)
        configurator.assure_completeness(conf_required)

        print(f'Gotowe! Konfigurację zapisano w {conf_file_path}.')
    print('Budzenie Somsiada...')

# Load the configuration
conf = {}
with open(conf_file_path, 'r+') as f:
    configurator = Configurator(f)
    conf = configurator.read()
    conf = configurator.assure_completeness(conf_required, conf)

client = Bot(description='Zawsze pomocny Somsiad', command_prefix=conf['command_prefix'])
client.remove_command('help') # Replaced with the 'help' plugin
