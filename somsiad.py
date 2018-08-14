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
from version import __version__
from somsiad_helper import *
from plugins import *

logging.basicConfig(filename='somsiad.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# This is what happens every time the bot launches
# In this case, it prints information like the user count server count, and the bot's ID in the console
@client.event
async def on_ready():
    number_of_users = len(set(client.get_all_members()))
    number_of_servers = len(client.guilds)
    with_preposition_variant = 'ze' if number_of_users >= 100 and number_of_users < 200 else 'z'
    user_noun_variant = 'użytkownikiem' if number_of_users == 1 else 'użytkownikami'
    server_noun_variant = 'serwerze' if number_of_servers == 1 else 'serwerach'
    print('\n== == == == == == == == == == == == == == == == == == == == == == == == == == ==')
    print(f'Obudzono Somsiada (ID {str(client.user.id)}).')
    print(f'Połączono {with_preposition_variant} {str(number_of_users)} {user_noun_variant} na {str(number_of_servers)}'
        f' {server_noun_variant}.')
    print('\nLink do zaproszenia bota:')
    print(f'https://discordapp.com/oauth2/authorize?client_id={str(client.user.id)}&scope=bot&permissions=536083543')
    print(f'\nToken bota: {conf["discord_token"]}')
    print(f'Klucz API Google: {conf["google_key"]}')
    print(f'ID aplikacji redditowej: {conf["reddit_id"]}')
    print(f'Szyfr aplikacji redditowej: {conf["reddit_secret"]}')
    print(f'Redditowa nazwa użytkownika: {conf["reddit_username"]}')
    print(f'Hasło do konta na Reddicie: {"*" * len(conf["reddit_password"])}')
    print(f'Cooldown wywołania komendy przez użytkownika: {conf["user_command_cooldown_seconds"]} s')
    print(f'Prefiks komend: {conf["command_prefix"]}')
    print(f'Ścieżka pliku konfiguracyjnego: {conf_file_path}')
    print(f'\nSomsiad {__version__} • discord.py {discord.__version__} • Python {platform.python_version()}')
    print('\nCopyright 2018 Habchy, ondondil & Twixes')
    print('== == == == == == == == == == == == == == == == == == == == == == == == == == ==')
    return await client.change_presence(activity=discord.Game(name=f'Kiedyś to było | {conf["command_prefix"]}pomocy'))

@client.event
async def on_command_error(ctx, error):
    '''Error handling'''
    ignored = (commands.CommandNotFound, commands.UserInputError)
    if isinstance(error, ignored):
        return
    elif isinstance(error, commands.DisabledCommand):
        return await ctx.send(f'Komenda {ctx.command} została wyłączona.')
    elif isinstance(error, commands.NoPrivateMessage):
        try:
            return await ctx.author.send(f'Komenda {ctx.command} nie może zostać użyta w prywatnej wiadomości.')
        except:
            pass
    print(f'Ignorowanie wyjątku w komendzie {ctx.command}:', file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

# Terminate the program if admin did not provide bot token
if conf['discord_token'] != '':
    client.run(conf['discord_token'])
else:
    print(f'BŁĄD: Nie znaleziono tokenu bota w {str(conf_file_path)}')
    print('Zatrzymywanie programu...')
    sys.exit()
