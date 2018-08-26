#!/usr/bin/env python3

# Copyright 2018 Habchy, ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import platform
import logging
import discord
from discord.ext import commands
from somsiad_helper import *
from version import __version__
from plugins import *


logging.basicConfig(
    filename='somsiad.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

informator = Informator()

# This is what happens every time the bot launches
# In this case, it prints information like the user count, server count, and the bot's ID in the console
def print_info():
    number_of_users = len(set(somsiad.client.get_all_members()))
    number_of_servers = len(somsiad.client.guilds)

    info_lines = (
        f'Obudzono Somsiada (ID {somsiad.client.user.id}).',
        '',
        f'Połączono {informator.with_preposition_variant(number_of_users)} {number_of_users} '
        f'{informator.noun_variant(number_of_users, "użytkownikiem", "użytkownikami")} na {number_of_servers} '
        f'{informator.noun_variant(number_of_servers, "serwerze", "serwerach")}:',
        informator.list_of_servers(somsiad.client),
        '',
        'Link do zaproszenia bota:',
        somsiad.invite_url,
        '',
        somsiad.configurator.info(),
        '',
        f'Somsiad {__version__} • discord.py {discord.__version__} • Python {platform.python_version()}',
        '',
        'Copyright 2018 Habchy, ondondil & Twixes',
    )

    informator.info(info_lines, '== ', verbose=True)


@somsiad.client.event
async def on_ready():
    """Does things once the bot comes online."""
    print_info()
    await somsiad.client.change_presence(
        activity=discord.Game(name=f'Kiedyś to było | {somsiad.conf["command_prefix"]}pomocy')
    )


@somsiad.client.event
async def on_guild_join(server):
    """Does things whenever the bot joins a server."""
    print_info()


@somsiad.client.event
async def on_guild_remove(server):
    """Does things whenever the bot leaves a server."""
    print_info()


@somsiad.client.event
async def on_command_error(ctx, error):
    """Handles command errors."""
    ignored = (commands.CommandNotFound, commands.UserInputError)
    if isinstance(error, ignored):
        return
    elif isinstance(error, commands.DisabledCommand):
        return await ctx.send(f'Komenda {ctx.command} została wyłączona.')
    elif isinstance(error, commands.NoPrivateMessage):
        try:
            return await ctx.author.send(f'Komenda {somsiad.conf["command_prefix"]}{ctx.command} '
                'nie może zostać użyta w prywatnej wiadomości.')
        except:
            pass
    somsiad.logger.error(f'Ignoring an exception in the {somsiad.conf["command_prefix"]}{ctx.command} command: '
        f'{error}.')


if __name__ == '__main__':
    somsiad.run()
