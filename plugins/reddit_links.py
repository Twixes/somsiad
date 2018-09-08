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


@somsiad.client.command(aliases=['r', 'sub'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def subreddit(ctx, *args):
    """Responds with the URL of the given subreddit."""
    if not args:
        url = 'https://reddit.com/r/all'
    else:
        url = f'https://reddit.com/r/{"".join(args)}'
    await ctx.send(f'{ctx.author.mention}\n{url}')


@somsiad.client.command(aliases=['u'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def reddit_user(ctx, *args):
    """Responds with the URL of the given Reddit user."""
    if not args:
        url = f'https://reddit.com/u/{somsiad.conf["reddit_username"]}'
    else:
        url = f'https://reddit.com/u/{"".join(args)}'
    await ctx.send(f'{ctx.author.mention}\n{url}')
