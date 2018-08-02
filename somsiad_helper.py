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

# Check presence of config file holding user tokens

# If file doesn't exist, create one and ask for tokens on first run
conf_file_path = os.path.join(os.path.expanduser('~'), '.config', 'somsiad.conf')
if not os.path.exists(conf_file_path):
    with open(conf_file_path, 'w') as f:
        f.write('discord_token: ' + str(input('Wprowadź discordowy token bota:\n')) + '\n')
        f.write('google_key: ' +
            str(input('Wprowadź klucz API Google (lub pomiń, jeśli nie chcesz usług Google):\n')) + '\n')
        f.write('user_command_cooldown: ' +
            str(input('Wprowadź cooldown między wywołaniami bota przez danego użytkownika (w s):\n')) + '\n')
        f.write('command_prefix: ' + str(input('Wprowadź prefiks komend:\n')) + '\n')
        print('Zapisano konfigurację do ' + conf_file_path)
    print('Budzenie Somsiada...')

# If file exists, fetch the keys.
conf = {}
with open(conf_file_path) as f:
    for line in f.readlines():
        line = line.strip()
        line = line.split(':')
        conf[line[0].strip()] = line[1].strip()

bot_dir = os.getcwd()

client = Bot(description='Zawsze pomocny Somsiad', command_prefix=conf['command_prefix'])
client.remove_command('help') # Replaced with 'help' plugin
