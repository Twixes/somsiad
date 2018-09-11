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


@somsiad.client.command(aliases=['wejdź'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.is_owner()
async def enter(ctx, *args):
    """Generates an invite to the provided server."""
    server_name = ' '.join(args)
    invite = None
    for server in somsiad.client.guilds:
        if server.name == server_name:
            for channel in server.channels:
                if (
                        not isinstance(channel, discord.CategoryChannel)
                        and server.me.permissions_in(channel).create_instant_invite
                ):
                    invite = await channel.create_invite(max_uses=1)
                    break
            break

    if invite is not None:
        await ctx.send(invite.url)


@somsiad.client.command(aliases=['ogłośglobalnie', 'oglosglobalnie'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.is_owner()
async def announce_globally(ctx, *args):
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


@somsiad.client.command(aliases=['ogłoślokalnie', 'ogloslokalnie'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.is_owner()
async def announce_locally(ctx, *args):
    """Makes an announcement only on the server where the command was invoked."""
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


@somsiad.client.command(aliases=['zatrzymaj'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.is_owner()
async def stop(ctx):
    """Shuts down the bot."""
    embed = discord.Embed(
        title=':stop_button: Zatrzymywanie bota...',
        color=somsiad.color
    )
    await ctx.send(embed=embed)
    await somsiad.client.close()
    exit()
