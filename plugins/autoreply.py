# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from discord.ext import commands
from somsiad_helper import *
from version import __version__

@client.command(aliases=['wersja'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
async def version(ctx):
    """Responds with current version of the bot"""
    await ctx.send(__version__)

@client.command()
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
async def ping(ctx):
    """Pong"""
    await ctx.send(':ping_pong: Pong!')

@client.command(aliases=['lennyface'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def lenny(ctx):
    """Responds with a lenny face"""
    await ctx.send('( ͡° ͜ʖ ͡°)')

@client.command()
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def flip(ctx):
    """Responds with the table flip emoticon"""
    await ctx.send('(╯°□°）╯︵ ┻━┻')

@client.command(aliases=['fix'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def unflip(ctx):
    """Responds with the table unflip emoticon"""
    await ctx.send('┬─┬ ノ( ゜-゜ノ)')

@client.command()
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def shrug(ctx):
    """Responds with the shrug emoticon"""
    await ctx.send('¯\_(ツ)_/¯')

@client.command()
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def fccchk(ctx):
    """:japanese_goblin:"""
    await ctx.send(':japanese_goblin:')

@client.command(aliases=['r', 'sub'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def subreddit(ctx, arg):
    """Responds with the URL of the given subreddit"""
    url = f'https://reddit.com/r/{arg}'
    await ctx.send(url)

@client.command(aliases=['u'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def user(ctx, arg):
    """Responds with the URL of the given Reddit user"""
    url = f'https://reddit.com/u/{arg}'
    await ctx.send(url)
