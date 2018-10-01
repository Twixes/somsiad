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

async def smart_add_reactions(ctx, args, reactions):
    """Adds provided emojis to the specified user's last non-command message in the form of reactions.
    If no user was specified, adds emojis to the last non-command message sent by any non-bot user
    in the given channel.
    """
    was_message_found = False

    if not args:
        async for message in ctx.history(limit=5):
            if (
                not was_message_found
                and not message.content.startswith(somsiad.conf['command_prefix'])
            ):
                for reaction in reactions:
                    await message.add_reaction(reaction)
                was_message_found = True

    else:
        async for message in ctx.history(limit=10):
            if (
                not was_message_found
                and message.author == await somsiad.member_converter.convert(ctx, ' '.join(args))
                and not message.content.startswith(somsiad.conf['command_prefix'])
            ):
                for reaction in reactions:
                    await message.add_reaction(reaction)
                was_message_found = True


@somsiad.bot.command(aliases=['pomógł', 'pomogl'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def helped(ctx, *args):
    """Adds "POMOGL" with smart_add_reactions()."""
    reactions = ['🇵', '🇴', '🇲', '🅾', '🇬', '🇱']
    for emoji in ctx.guild.emojis:
        if emoji.name == 'regional_indicator_oo':
            reactions[3] = emoji
        if emoji.name == 'regional_indicator_el':
            reactions[5] = emoji
    await smart_add_reactions(ctx, args, reactions)


@somsiad.bot.command(aliases=['niepomógł', 'niepomogl'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def didnothelp(ctx, *args):
    """Adds "NIEPOMOGL" with smart_add_reactions()."""
    reactions = ['🇳', '🇮', '🇪', '🇵', '🇴', '🇲', '🅾', '🇬', '🇱']
    for emoji in ctx.guild.emojis:
        if emoji.name == 'regional_indicator_oo':
            reactions[6] = emoji
        if emoji.name == 'regional_indicator_el':
            reactions[8] = emoji
    await smart_add_reactions(ctx, args, reactions)
