#! /usr/bin/python3

#  somsiad.py - a Discord bot
#  Copyright (c) 2018 ondondil.

#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <https://www.gnu.org/licenses/>.

import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
import platform
import sys
import traceback
import logging
from somsiad_helper import *
from plugins import (wiki_search, g_search, urban_dict, eightball, isitup, image_search, simple_text_responses, help,
    youtube)

logging.basicConfig(filename='somsiad_log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# This is what happens every time the bot launches. In this case, it prints information
# like the server count, user count, and the bot's ID in the console.
@client.event
async def on_ready():
    print('')
    print('== == == == == == == == == == == == == == == == == == == == == == == == == == ==')
    print('Obudzono Somsiada (ID:' + str(client.user.id) + ').')
    print('Połączono z ' + str(len(set(client.get_all_members()))) + ' użytkownikami na ' + str(len(client.guilds)) +
        ' serwerach.')
    print('')
    print('Link do zaproszenia bota:')
    print('https://discordapp.com/oauth2/authorize?client_id=' + '{}&scope=bot&permissions=536083543'.format(
        str(client.user.id)))
    print('')
    print('Aktywny token bota: ' + conf['discord'])
    print('Aktywny klucz API YouTube: ' + (conf['youtube'] if len(conf['youtube']) > 0 else
        'dezaktywowano moduł YouTube'))
    print('Cooldown wywołania przez użytkownika: ' + conf['cooldown'] + ' s')
    print('Prefiks komend: ' + conf['prefix'])
    print('Konfiguracja zapisana w: ' + conf_file_path)
    print('')
    print('Wersja Pythona: {}'.format(platform.python_version()) +' • Wersja discord.py: {}'.format(
        discord.__version__))
    print('')
    print('Stworzono na podstawie BasicBota 2.1 Habchy\'ego#1665.')
    print('== == == == == == == == == == == == == == == == == == == == == == == == == == ==')
    return await client.change_presence(activity=discord.Game(name='Kiedyś to było... | ' + conf['prefix'] + 'pomocy'))

@client.event
async def on_command_error(ctx, error):
    """Error handling"""
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

# Disable 'youtube' plugin if no youtube API key is found
if conf['youtube'] == "":
    client.remove_command('youtube')

# Terminate the program if user did not provide bot token
if conf['discord'] != "":
    client.run(conf['discord'])
else:
    print("BŁĄD: Nie znaleziono tokenu bota w " + str(conf_file_path))
    print("Zatrzymywanie programu...")
    sys.exit()
