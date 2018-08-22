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

@somsiad.client.command(aliases=['wersja'])
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
async def version(ctx):
    """Responds with current version of the bot."""
    if somsiad.does_member_have_elevated_permissions(ctx.author):
        version_string = f'{__version__}!'
    else:
        version_string = __version__
    await ctx.send(version_string)

@somsiad.client.command()
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
async def ping(ctx):
    """Pong!"""
    await ctx.send(':ping_pong: Pong!')

@somsiad.client.command(aliases=['lenny'])
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def lennyface(ctx):
    """( ͡° ͜ʖ ͡°)"""
    await ctx.send('( ͡° ͜ʖ ͡°)')

@somsiad.client.command()
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def tableflip(ctx):
    """(╯°□°）╯︵ ┻━┻"""
    await ctx.send('(╯°□°）╯︵ ┻━┻')

@somsiad.client.command()
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def unflip(ctx):
    """┬─┬ ノ( ゜-゜ノ)"""
    await ctx.send('┬─┬ ノ( ゜-゜ノ)')

@somsiad.client.command()
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def shrug(ctx):
    r"""¯\_(ツ)_/¯"""
    await ctx.send(r'¯\_(ツ)_/¯')

@somsiad.client.command(aliases=['dej'])
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def gib(ctx, *args):
    """༼ つ ◕_◕ ༽つ"""
    if len(args) == 0:
        await ctx.send('༼ つ ◕_◕ ༽つ')
    else:
        await ctx.send(f'༼ つ ◕_◕ ༽つ {" ".join(args)}')

@somsiad.client.command()
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def fccchk(ctx):
    """:japanese_goblin:"""
    await ctx.send(':japanese_goblin:')

@somsiad.client.command(aliases=['r', 'sub'])
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def subreddit(ctx, *args):
    """Responds with the URL of the given subreddit."""
    if len(args) == 0:
        url = 'https://reddit.com/r/all'
    else:
        url = f'https://reddit.com/r/{"".join(args)}'
    await ctx.send(url)

@somsiad.client.command(aliases=['u'])
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def user(ctx, *args):
    """Responds with the URL of the given Reddit user."""
    if len(args) == 0:
        url = f'https://reddit.com/u/{somsiad.conf["reddit_username"]}'
    else:
        url = f'https://reddit.com/u/{"".join(args)}'
    await ctx.send(url)
