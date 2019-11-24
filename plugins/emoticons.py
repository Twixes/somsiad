# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from core import somsiad
from configuration import configuration


@somsiad.command(aliases=['lenny'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def lennyface(ctx):
    """( ͡° ͜ʖ ͡°)"""
    await ctx.send('( ͡° ͜ʖ ͡°)')


@somsiad.command(aliases=['lenno'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def lennoface(ctx):
    """( ͡ʘ ͜ʖ ͡ʘ)"""
    await ctx.send('( ͡ʘ ͜ʖ ͡ʘ)')


@somsiad.command(aliases=['wywróć'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def tableflip(ctx):
    """(╯°□°）╯︵ ┻━┻"""
    await ctx.send('(╯°□°）╯︵ ┻━┻')


@somsiad.command(aliases=['odstaw'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def unflip(ctx):
    """┬─┬ ノ( ゜-゜ノ)"""
    await ctx.send('┬─┬ ノ( ゜-゜ノ)')


@somsiad.command()
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def shrug(ctx):
    r"""¯\_(ツ)_/¯"""
    await ctx.send(r'¯\_(ツ)_/¯')


@somsiad.command(aliases=['dej'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def gib(ctx, *, thing = None):
    """༼ つ ◕_◕ ༽つ"""
    if thing is None:
        await ctx.send('༼ つ ◕_◕ ༽つ')
    elif 'fccchk' in thing:
        await ctx.send(f'༼ つ :japanese_goblin: ༽つ {thing}')
    else:
        await ctx.send(f'༼ つ ◕_◕ ༽つ {thing}')


@somsiad.command()
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def fccchk(ctx):
    """:japanese_goblin:"""
    await ctx.send(':japanese_goblin:')
