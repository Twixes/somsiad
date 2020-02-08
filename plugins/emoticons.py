# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from discord.ext import commands
from core import somsiad
from configuration import configuration


@somsiad.command(aliases=['lenny'])
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
)
async def lennyface(ctx):
    """( ͡° ͜ʖ ͡°)"""
    await somsiad.send(ctx, '( ͡° ͜ʖ ͡°)', mention=False)


@somsiad.command(aliases=['lenno'])
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
)
async def lennoface(ctx):
    """( ͡ʘ ͜ʖ ͡ʘ)"""
    await somsiad.send(ctx, '( ͡ʘ ͜ʖ ͡ʘ)', mention=False)


@somsiad.command(aliases=['wywróć'])
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
)
async def tableflip(ctx):
    """(╯°□°）╯︵ ┻━┻"""
    await somsiad.send(ctx, '(╯°□°）╯︵ ┻━┻', mention=False)


@somsiad.command(aliases=['odstaw'])
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
)
async def unflip(ctx):
    """┬─┬ ノ( ゜-゜ノ)"""
    await somsiad.send(ctx, '┬─┬ ノ( ゜-゜ノ)', mention=False)


@somsiad.command()
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
)
async def shrug(ctx):
    r"""¯\_(ツ)_/¯"""
    await somsiad.send(ctx, r'¯\_(ツ)_/¯', mention=False)


@somsiad.command(aliases=['dej'])
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
)
async def gib(ctx, *, thing = None):
    """༼ つ ◕_◕ ༽つ"""
    if thing is None:
        await somsiad.send(ctx, '༼ つ ◕_◕ ༽つ', mention=False)
    elif 'fccchk' in thing:
        await somsiad.send(ctx, f'༼ つ :japanese_goblin: ༽つ {thing}', mention=False)
    else:
        await somsiad.send(ctx, f'༼ つ ◕_◕ ༽つ {thing}', mention=False)


@somsiad.command()
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
)
async def fccchk(ctx):
    """:japanese_goblin:"""
    await somsiad.send(ctx, ':japanese_goblin:', mention=False)
