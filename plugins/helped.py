# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from discord.ext import commands
from somsiad_helper import *
from version import __version__


async def smart_add_reactions(server, channel, args, reactions):
    """Adds provided emojis to the specified user's last non-command message in the form of reactions.
        If no user was specified, adds emojis to the last non-command message sent by any non-bot user
        in the given channel."""
    was_message_found = False

    if not args:
        async for message in channel.history(limit=5):
            if (not was_message_found and not message.author.bot and
                    not message.content.startswith(somsiad.conf['command_prefix'])):
                for reaction in reactions:
                    await message.add_reaction(reaction)
                was_message_found = True

    else:
        async for message in channel.history(limit=10):
            if (not was_message_found and message.author == somsiad.get_fellow_server_member(server, args) and
                    not message.content.startswith(somsiad.conf['command_prefix'])):
                for reaction in reactions:
                    await message.add_reaction(reaction)
                was_message_found = True


@somsiad.client.command(aliases=['pomógł', 'pomogl'])
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def helped(ctx, *args):
    """Adds "POMOGL" with smart_add_reactions()."""
    reactions = ('🇵', '🇴', '🇲', '🅾', '🇬', '🇱')
    await smart_add_reactions(ctx.guild, ctx.channel, args, reactions)


@somsiad.client.command(aliases=['niepomógł', 'niepomogl'])
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def didnothelp(ctx, *args):
    """Adds "NIEPOMOGL" with smart_add_reactions()."""
    reactions = ('🇳', '🇮', '🇪', '🇵', '🇴', '🇲', '🅾', '🇬', '🇱')
    await smart_add_reactions(ctx.guild, ctx.channel, args, reactions)
