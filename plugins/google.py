# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from discord.ext import commands
from googleapiclient.discovery import build
from somsiad_helper import *

google_client = build('customsearch', 'v1', developerKey=conf['google_key'])

@client.command(aliases=['g', 'gugiel'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def google(ctx, *args):
    """Returns first matching result from Google using the provided Custom Search Engine."""
    if len(args) == 0:
        await ctx.send(f'{ctx.author.mention}\nhttps://www.google.com/')
    else:
        query = ' '.join(args)
        result = google_client.cse().list(q=query, cx=conf['google_custom_search_engine_id'], hl='pl',
            num=1, fields='items/link,searchInformation/totalResults').execute()
        if int(result['searchInformation']['totalResults']) == 0:
            await ctx.send(f'{ctx.author.mention}\nBrak wyników dla zapytania **{query}**.')
        else:
            await ctx.send(f'{ctx.author.mention}\n{result["items"][0]["link"]}')

@client.command(aliases=['gi'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def googleimage(ctx, *args):
    """Returns first matching result from Google using the provided Custom Search Engine."""
    if len(args) == 0:
        await ctx.send(f'{ctx.author.mention}\nhttps://www.google.com/')
    else:
        query = ' '.join(args)
        result = google_client.cse().list(q=query, cx=conf['google_custom_search_engine_id'], hl='pl',
            num=1, searchType='image', fields='items/link,searchInformation/totalResults').execute()
        if int(result['searchInformation']['totalResults']) == 0:
            await ctx.send(f'{ctx.author.mention}\nBrak wyników dla zapytania **{query}**.')
        else:
            await ctx.send(f'{ctx.author.mention}\n{result["items"][0]["link"]}')
