# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from difflib import SequenceMatcher
from urllib.error import HTTPError

import aiohttp
from discord.ext import commands

from configuration import configuration
from core import cooldown


class LastFM(commands.Cog):
    FOOTER_TEXT = 'Last.fm'
    FOOTER_ICON_URL = 'https://www.last.fm/static/images/lastfm_avatar_twitter.png'
    API_URL = 'https://ws.audioscrobbler.com/2.0/'

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_user_info(self, user: str):
        params = {'api_key': configuration['last_fm_key'], 'format': 'json', 'method': 'user.getInfo', 'user': user}
        try:
            # use OpenSearch API first to get accurate page title of the result
            async with self.bot.session.get(self.API_URL, params=params) as request:
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
        params = {
            'api_key': configuration['last_fm_key'],
            'format': 'json',
            'method': 'user.getRecentTracks',
            'user': user,
            'limit': limit,
        }
        try:
            async with self.bot.session.get(self.API_URL, params=params) as request:
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

    @commands.group(aliases=['lastfm', 'last', 'fm', 'lfm'], invoke_without_command=True, case_insensitive=True)
    @cooldown()
    async def last_fm(self, ctx, *, user):
        async with ctx.typing():
            user_info = await self.get_user_info(user)
            if user_info is None:
                raise commands.BadArgument
            else:
                user_recent_tracks = await self.get_user_recent_tracks(user)
                if user_recent_tracks:
                    if '@attr' in user_recent_tracks[0] and user_recent_tracks[0]['@attr']['nowplaying']:
                        current_state_emoji = '▶️'
                    else:
                        current_state_emoji = '⏹'
                    embed = self.bot.generate_embed(
                        current_state_emoji, user_recent_tracks[0]['name'], url=user_recent_tracks[0]['url']
                    )
                    embed.set_thumbnail(url=user_recent_tracks[0]['image'][2]['#text'])
                    embed.add_field(
                        name='W wykonaniu',
                        value=f'[{user_recent_tracks[0]["artist"]["#text"]}](https://www.last.fm/music/'
                        f'{user_recent_tracks[0]["artist"]["#text"].replace(" ", "+").replace("/", "%2F")})',
                    )
                    if user_recent_tracks[0]["album"]["#text"] != '':
                        embed.add_field(
                            name='Z albumu',
                            value=f'[{user_recent_tracks[0]["album"]["#text"]}](https://www.last.fm/music/'
                            f'{user_recent_tracks[0]["artist"]["#text"].replace(" ", "+").replace("/", "%2F")}/'
                            f'{user_recent_tracks[0]["album"]["#text"].replace(" ", "+").replace("/", "%2F")})',
                        )
                    # search for the song on YouTube
                    youtube_search_query = f'{user_recent_tracks[0]["name"]} {user_recent_tracks[0]["artist"]["#text"]}'
                    try:
                        youtube_search_result = await self.bot.youtube_client.search(youtube_search_query)
                    except HTTPError:
                        pass
                    else:
                        # add a link to a YouTube video if a match was found
                        if (
                            youtube_search_result is not None
                            and SequenceMatcher(None, youtube_search_query, youtube_search_result.title).ratio() > 0.25
                        ):
                            embed.add_field(name='Posłuchaj na YouTube', value=youtube_search_result.url, inline=False)
                            embed.set_image(url=youtube_search_result.thumbnail_url)
                else:
                    embed = self.bot.generate_embed('❓', 'Brak ostatnio słuchanego utworu')
                embed.set_author(
                    name=user_info['name'],
                    url=f'https://www.last.fm/user/{user_info["name"]}',
                    icon_url=user_info['image'][0]['#text'],
                )
                embed.set_footer(text=self.FOOTER_TEXT, icon_url=self.FOOTER_ICON_URL)
            await self.bot.send(ctx, embed=embed)

    @last_fm.error
    async def last_fm_error(self, ctx, error):
        notice = None
        if isinstance(error, commands.MissingRequiredArgument):
            notice = 'Nie podano użytkownika Last.fm'
        elif isinstance(error, commands.BadArgument):
            notice = 'Nie znaleziono takiego użytkownika Last.fm'
        if notice is not None:
            embed = self.bot.generate_embed('⚠️', notice)
            embed.set_footer(text=self.FOOTER_TEXT, icon_url=self.FOOTER_ICON_URL)
            await self.bot.send(ctx, embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(LastFM(bot))
