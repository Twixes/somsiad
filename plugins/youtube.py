# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
import aiohttp
import logging
from somsiad_helper import *
from apiclient.discovery import build
from apiclient.errors import HttpError

@client.command(aliases=['yt', 'tuba'])
@commands.cooldown(1, conf['cooldown'], commands.BucketType.user)
@commands.guild_only()
async def youtube(ctx, *args):
    """Returns first matching result from YouTube."""
    DEVELOPER_KEY = conf['youtube']
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"
    if len(args) == 0:
        await ctx.send(':warning: Musisz podać parametr wyszukiwania, {}.'.format(ctx.author.mention))
    else:
        try:
            youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
            # Call the search.list method to retrieve results matching the specified query term.
            search_response = youtube.search().list(
                q=" ".join(args),
                part="id",
                maxResults=1,
                type='video'
            ).execute()
            # Output results
            if len(search_response.get('items')) == 0:
                await ctx.send('{}, nie znaleziono pasujących wyników.'.format(ctx.author.mention))
            else:
                video_id = search_response.get('items')[0]['id']['videoId']
                video_url = "https://www.youtube.com/watch?v={}".format(video_id)
                await ctx.send('{}\n'.format(ctx.author.mention) + video_url)
        except HttpError as e:
            logging.error(e)
