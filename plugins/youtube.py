# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import logging
import discord
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from core import somsiad
from configuration import configuration


class YouTube:
    FOOTER_TEXT = 'YouTube'
    FOOTER_ICON_URL = (
        'https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/'
        'YouTube_full-color_icon_%282017%29.svg/60px-YouTube_full-color_icon_%282017%29.svg.png'
    )

    _youtube_client = None

    def __init__(self, developer_key):
        self._youtube_client = build('youtube', 'v3', developerKey=developer_key)

    def search(self, query, max_number_of_results=1, search_type='video'):
        try:
            # Call the search.list method to retrieve results matching the specified query term.
            search_response = self._youtube_client.search().list(
                q=query,
                part='snippet',
                maxResults=max_number_of_results,
                type=search_type
            ).execute()
            # Output results if there are any
            results = search_response.get('items')
            return results
        except HttpError as e:
            logging.error(e)
            return None


youtube = YouTube(configuration['google_key'])


@somsiad.command(aliases=['youtube', 'yt', 'tuba'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def youtube_search(ctx, *, query = ''):
    """Returns first matching result from YouTube."""
    result = youtube.search(query)

    if result:
        video_id = result[0]['id']['videoId']
        video_url = f'https://www.youtube.com/watch?v={video_id}'
        await ctx.send(f'{ctx.author.mention}\n{video_url}')
    else:
        embed = discord.Embed(
            title=f':slight_frown: Brak wyników dla zapytania "{query}"',
            color=somsiad.COLOR
        )
        embed.set_footer(icon_url=YouTube.FOOTER_ICON_URL, text=YouTube.FOOTER_TEXT)
        await ctx.send(ctx.author.mention, embed=embed)


@somsiad.group(invoke_without_command=True, case_insensitive=True)
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def alexa(ctx):
    pass


@alexa.command(aliases=['play'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def alexa_play(ctx):
    await youtube_search.invoke(ctx)
