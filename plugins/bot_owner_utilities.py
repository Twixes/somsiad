# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from somsiad import somsiad


@somsiad.client.command(aliases=['ogłoś', 'oglos'])
@discord.ext.commands.cooldown(1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user)
@discord.ext.commands.is_owner()
async def announce(ctx, *args):
    """Makes an announcement on all servers smaller than 10000 members not containing "bot" in their name."""
    announcement = ' '.join(args)

    embed = discord.Embed(
        title='Ogłoszenie somsiedzkie',
        description=announcement,
        color=somsiad.color
    )

    for server in ctx.bot.guilds:
        if 'bot' not in server.name and server.member_count < 10000:
            if server.system_channel is not None and server.system_channel.permissions_for(ctx.me).send_messages:
                await server.system_channel.send(embed=embed)
            else:
                for channel in server.text_channels:
                    if channel.permissions_for(ctx.me).send_messages:
                        await channel.send(embed=embed)
                        break


@somsiad.client.command(aliases=['ogłośnasucho', 'oglosnasucho'])
@discord.ext.commands.cooldown(1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user)
@discord.ext.commands.is_owner()
async def dry_announce(ctx, *args):
    """Makes an announcement only on the server where it was invoked."""
    announcement = ' '.join(args)

    embed = discord.Embed(
        title='Ogłoszenie somsiedzkie',
        description=announcement,
        color=somsiad.color
    )

    if ctx.guild.system_channel is not None and ctx.guild.system_channel.permissions_for(ctx.me).send_messages:
        await ctx.guild.system_channel.send(embed=embed)
    else:
        for channel in ctx.guild.text_channels:
            if channel.permissions_for(ctx.me).send_messages:
                await channel.send(embed=embed)
                break
