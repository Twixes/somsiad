#!/usr/bin/env python3

# Copyright 2018 Habchy, ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from discord.ext import commands
import platform
import sys
import traceback
import logging
from somsiad_helper import *
from plugins import *

logging.basicConfig(filename='somsiad_log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# This is what happens every time the bot launches. In this case, it prints information
# like the server count, user count, and the bot's ID in the console.
@client.event
async def on_ready():
    print('\n== == == == == == == == == == == == == == == == == == == == == == == == == == ==')
    print('Obudzono Somsiada (ID:' + str(client.user.id) + ').')
    print('Połączono z ' + str(len(set(client.get_all_members()))) + ' użytkownikami na ' + str(len(client.guilds)) +
        ' serwerach.\n')
    print('Link do zaproszenia bota:')
    print('https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=536083543'.format(
        str(client.user.id)) + '\n')
    print('Aktywny token bota: ' + conf['discord_token'])
    print('Aktywny klucz API Google: ' + (conf['google_key'] if len(conf['google_key']) > 0 else
        'dezaktywowano moduł Google'))
    print('Cooldown wywołania przez użytkownika: ' + conf['user_command_cooldown'] + ' s')
    print('Prefiks komend: ' + conf['command_prefix'])
    print('Plik konfiguracyjny: ' + conf_file_path + '\n')
    print('Wersja Pythona: {}'.format(platform.python_version()) + ' • Wersja discord.py: {}'.format(
        discord.__version__) + '\n')
    print('Copyright 2018 Habchy, ondondil & Twixes')
    print('== == == == == == == == == == == == == == == == == == == == == == == == == == ==')
    return await client.change_presence(activity=discord.Game(name='Kiedyś to było | ' + conf['command_prefix'] +
        'pomocy'))

@client.event
async def on_command_error(ctx, error):
    '''Error handling'''
    ignored = (commands.CommandNotFound, commands.UserInputError)
    if isinstance(error, ignored):
        return
    elif isinstance(error, commands.DisabledCommand):
        return await ctx.send(f'{ctx.command} została wyłączona.')
    elif isinstance(error, commands.NoPrivateMessage):
        try:
            return await ctx.author.send(f'Komenda {ctx.command} nie może zostać użyta w prywatnej wiadomości.')
        except:
            pass
    print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

# Disable 'youtube' plugin if no Google API key is found
if conf['google_key'] == '':
    client.remove_command('youtube')

# Terminate the program if user did not provide bot token
if conf['discord_token'] != '':
    client.run(conf['discord_token'])
else:
    print('BŁĄD: Nie znaleziono tokenu bota w ' + str(conf_file_path))
    print('Zatrzymywanie programu...')
    sys.exit()
