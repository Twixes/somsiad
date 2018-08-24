# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import logging
from discord.ext import commands
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from somsiad_helper import *


class YouTube:
    _youtube_client = None

    def __init__(self, developer_key):
        self._youtube_client = build('youtube', 'v3', developerKey=developer_key)

    def search(self, query, max_number_of_results=1, search_type='video'):
        try:
            # Call the search.list method to retrieve results matching the specified query term.
            search_response = self._youtube_client.search().list(
                q=query,
                part='id',
                maxResults=max_number_of_results,
                type=search_type
            ).execute()
            # Output results if there are any
            results = search_response.get('items')
            return results
        except HttpError as e:
            logging.error(e)
            return None


youtube = YouTube(somsiad.conf['google_key'])


@somsiad.client.command(aliases=['youtube', 'yt', 'tuba'])
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def youtube_search(ctx, *args):
    """Returns first matching result from YouTube."""
    if not args:
        await ctx.send(f'{ctx.author.mention}\nhttps://www.youtube.com/')

    else:
        query = ' '.join(args)

        result = youtube.search(query)

        if result:
            video_id = result[0]['id']['videoId']
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            await ctx.send(f'{ctx.author.mention}\n{video_url}')
        else:
            await ctx.send(f'{ctx.author.mention}\nBrak wyników dla zapytania **{query}**.')
