# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from somsiad import somsiad


@somsiad.client.command(aliases=['lenny'])
@discord.ext.commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], discord.ext.commands.BucketType.user)
@discord.ext.commands.guild_only()
async def lennyface(ctx):
    """( ͡° ͜ʖ ͡°)"""
    await ctx.send('( ͡° ͜ʖ ͡°)')


@somsiad.client.command(aliases=['lenno'])
@discord.ext.commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], discord.ext.commands.BucketType.user)
@discord.ext.commands.guild_only()
async def lennoface(ctx):
    """( ͡ʘ ͜ʖ ͡ʘ)"""
    await ctx.send('( ͡ʘ ͜ʖ ͡ʘ)')


@somsiad.client.command()
@discord.ext.commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], discord.ext.commands.BucketType.user)
@discord.ext.commands.guild_only()
async def tableflip(ctx):
    """(╯°□°）╯︵ ┻━┻"""
    await ctx.send('(╯°□°）╯︵ ┻━┻')


@somsiad.client.command()
@discord.ext.commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], discord.ext.commands.BucketType.user)
@discord.ext.commands.guild_only()
async def unflip(ctx):
    """┬─┬ ノ( ゜-゜ノ)"""
    await ctx.send('┬─┬ ノ( ゜-゜ノ)')


@somsiad.client.command()
@discord.ext.commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], discord.ext.commands.BucketType.user)
@discord.ext.commands.guild_only()
async def shrug(ctx):
    r"""¯\_(ツ)_/¯"""
    await ctx.send(r'¯\_(ツ)_/¯')


@somsiad.client.command(aliases=['dej'])
@discord.ext.commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], discord.ext.commands.BucketType.user)
@discord.ext.commands.guild_only()
async def gib(ctx, *args):
    """༼ つ ◕_◕ ༽つ"""
    if not args:
        await ctx.send('༼ つ ◕_◕ ༽つ')
    else:
        await ctx.send(f'༼ つ ◕_◕ ༽つ {" ".join(args)}')


@somsiad.client.command()
@discord.ext.commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], discord.ext.commands.BucketType.user)
@discord.ext.commands.guild_only()
async def fccchk(ctx):
    """:japanese_goblin:"""
    await ctx.send(':japanese_goblin:')
