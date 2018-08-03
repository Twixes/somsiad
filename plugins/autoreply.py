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


@client.command()
@commands.cooldown(1, conf['user_command_cooldown'], commands.BucketType.user)
@commands.guild_only()
async def ping(ctx):
    '''Check if bot is working.'''
    await ctx.send(':ping_pong: Pong!')

@client.command(aliases=['lennyface'])
@commands.cooldown(1, conf['user_command_cooldown'], commands.BucketType.user)
@commands.guild_only()
async def lenny(ctx):
    '''Lenny face.'''
    await ctx.send('( ͡° ͜ʖ ͡°)')

@client.command()
@commands.cooldown(1, conf['user_command_cooldown'], commands.BucketType.user)
@commands.guild_only()
async def flip(ctx):
    '''Flip tables.'''
    await ctx.send('(╯°□°）╯︵ ┻━┻')

@client.command(aliases=['fix'])
@commands.cooldown(1, conf['user_command_cooldown'], commands.BucketType.user)
@commands.guild_only()
async def unflip(ctx):
    '''Unflip tables.'''
    await ctx.send('┬─┬ノ(ಠ_ಠノ)')

@client.command()
@commands.cooldown(1, conf['user_command_cooldown'], commands.BucketType.user)
@commands.guild_only()
async def shrug(ctx):
    '''Shrug.'''
    await ctx.send('¯\_(ツ)_/¯')

@client.command()
@commands.cooldown(1, conf['user_command_cooldown'], commands.BucketType.user)
@commands.guild_only()
async def fccchk(ctx):
    ''':japanese_goblin:'''
    await ctx.send(':japanese_goblin:')

@client.command(aliases=['r', 'sub'])
@commands.cooldown(1, conf['user_command_cooldown'], commands.BucketType.user)
@commands.guild_only()
async def subreddit(ctx, arg):
    '''Returns full URL for given subreddit name.'''
    url = 'https://reddit.com/r/{}'.format(arg)
    await ctx.send(url)

@client.command(aliases=['u'])
@commands.cooldown(1, conf['user_command_cooldown'], commands.BucketType.user)
@commands.guild_only()
async def user(ctx, arg):
    '''Returns full URL for given Reddit username.'''
    url = 'https://reddit.com/u/{}'.format(arg)
    await ctx.send(url)
