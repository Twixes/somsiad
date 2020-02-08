# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from difflib import SequenceMatcher
import aiohttp
import discord
from core import somsiad
from configuration import configuration
from plugins.youtube import youtube


class LastFM:
    """Handles Wikipedia search."""
    FOOTER_TEXT = 'Last.fm'
    FOOTER_ICON_URL = 'https://www.last.fm/static/images/lastfm_avatar_twitter.png'
    API_URL = 'https://ws.audioscrobbler.com/2.0/'
    headers = {'User-Agent': somsiad.USER_AGENT}

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_user_info(self, user: str):
        """Returns the closest matching article or articles from Wikipedia."""
        params = {
            'api_key': self.api_key,
            'format': 'json',
            'method': 'user.getInfo',
            'user': user
        }

        try:
            async with aiohttp.ClientSession() as session:
                # Use OpenSearch API first to get accurate page title of the result
                async with session.get(self.API_URL, headers=self.headers, params=params) as request:
                    if request.status == 200:
                        user_info = await request.json()
                        if 'error' in user_info:
                            return None
                        else:
                            return user_info['user']
                    else:
                        return None
        except aiohttp.client_exceptions.ClientConnectorError:
            return None

    async def get_user_recent_tracks(self, user: str, limit: int = 1):
        """Returns the closest matching article or articles from Wikipedia."""
        params = {
            'api_key': self.api_key,
            'format': 'json',
            'method': 'user.getRecentTracks',
            'user': user,
            'limit': limit
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.API_URL, headers=self.headers, params=params) as request:
                    if request.status == 200:
                        user_recent_tracks = await request.json()
                        if 'error' in user_recent_tracks:
                            return None
                        else:
                            return user_recent_tracks['recenttracks']['track']
                    else:
                        return None
        except aiohttp.client_exceptions.ClientConnectorError:
            return None


last_fm_api = LastFM(configuration['last_fm_key'])


@somsiad.group(aliases=['lastfm', 'last', 'fm', 'lfm'], invoke_without_command=True, case_insensitive=True)
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def last_fm(ctx, *, user):
    user_info = await last_fm_api.get_user_info(user)
    if user_info is None:
        raise discord.ext.commands.BadArgument
    else:
        user_recent_tracks = await last_fm_api.get_user_recent_tracks(user)
        if user_recent_tracks:
            current_state_emoji = (
                ':arrow_forward:' if '@attr' in user_recent_tracks[0] and user_recent_tracks[0]['@attr']['nowplaying']
                else ':stop_button:'
            )
            embed = discord.Embed(
                title=f'{current_state_emoji} {user_recent_tracks[0]["name"]}',
                url=user_recent_tracks[0]['url'],
                color=somsiad.COLOR
            )
            embed.set_thumbnail(url=user_recent_tracks[0]['image'][2]['#text'])
            embed.add_field(
                name='W wykonaniu',
                value=f'[{user_recent_tracks[0]["artist"]["#text"]}](https://www.last.fm/music/'
                f'{user_recent_tracks[0]["artist"]["#text"].replace(" ", "+").replace("/", "%2F")})'
            )
            if user_recent_tracks[0]["album"]["#text"] != '':
                embed.add_field(
                    name='Z albumu',
                    value=f'[{user_recent_tracks[0]["album"]["#text"]}](https://www.last.fm/music/'
                    f'{user_recent_tracks[0]["artist"]["#text"].replace(" ", "+").replace("/", "%2F")}/'
                    f'{user_recent_tracks[0]["album"]["#text"].replace(" ", "+").replace("/", "%2F")})'
                )

            # Search for the song on YouTube
            youtube_search_query = f'{user_recent_tracks[0]["name"]} {user_recent_tracks[0]["artist"]["#text"]}'
            youtube_search_result = youtube.search(youtube_search_query)
            # Add a link to a YouTube video if a match was found
            if (
                    youtube_search_result and
                    SequenceMatcher(
                        None, youtube_search_query, youtube_search_result[0]['snippet']['title']
                    ).ratio() > 0.25
            ):
                video_id = youtube_search_result[0]['id']['videoId']
                video_thumbnail_url = youtube_search_result[0]['snippet']['thumbnails']['medium']['url']
                embed.add_field(
                    name='Posłuchaj na YouTube', value=f'https://www.youtube.com/watch?v={video_id}', inline=False
                )
                embed.set_image(url=video_thumbnail_url)
        else:
            embed = discord.Embed(
                title=f':question: Brak ostatnio słuchanego utworu',
                color=somsiad.COLOR
            )
        embed.set_author(
            name=user_info['name'],
            url=f'https://www.last.fm/user/{user_info["name"]}',
            icon_url=user_info['image'][0]['#text']
        )
    embed.set_footer(
        text=LastFM.FOOTER_TEXT,
        icon_url=LastFM.FOOTER_ICON_URL
    )
    await somsiad.send(ctx, embed=embed)


@last_fm.error
async def last_fm_error(ctx, error):
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        embed = discord.Embed(
            title=':warning: Nie podano użytkownika Last.fm!',
            color=somsiad.COLOR
        )
        embed.set_footer(
            text=LastFM.FOOTER_TEXT,
            icon_url=LastFM.FOOTER_ICON_URL
        )
        await somsiad.send(ctx, embed=embed)
    elif isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Nie znaleziono takiego użytkownika Last.fm!',
            color=somsiad.COLOR
        )
        embed.set_footer(
            text=LastFM.FOOTER_TEXT,
            icon_url=LastFM.FOOTER_ICON_URL
        )
        await somsiad.send(ctx, embed=embed)
