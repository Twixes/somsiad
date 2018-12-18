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


@somsiad.bot.command(aliases=['r', 'sub'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def subreddit(ctx, *, subreddit=None):
    """Responds with the URL of the given subreddit."""
    if subreddit is None:
        url = 'https://old.reddit.com/r/all'
    else:
        url = f'https://old.reddit.com/r/{subreddit.replace(" ", "_")}'
    await ctx.send(f'{ctx.author.mention}\n{url}')


@somsiad.bot.command(aliases=['u'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def reddit_user(ctx, *, username=None):
    """Responds with the URL of the given Reddit user."""
    if username is None:
        url = f'https://old.reddit.com/u/{somsiad.conf["reddit_username"]}'
    else:
        url = f'https://old.reddit.com/u/{username.replace(" ", "_")}'
    await ctx.send(f'{ctx.author.mention}\n{url}')
