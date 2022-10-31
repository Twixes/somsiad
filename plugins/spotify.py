# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from difflib import SequenceMatcher
from somsiad import Somsiad, SomsiadMixin
from typing import cast
from sentry_sdk import capture_exception
import discord
from discord.ext import commands

from core import cooldown
from utilities import human_amount_of_time


class Spotify(commands.Cog, SomsiadMixin):
    FOOTER_TEXT = 'Spotify'
    FOOTER_ICON_URL = (
        'https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/'
        'Spotify_logo_without_text.svg/60px-Spotify_logo_without_text.svg.png'
    )

    @cooldown()
    @commands.command()
    @commands.guild_only()
    async def spotify(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        spotify_activity = cast(
            discord.Spotify,
            discord.utils.find(lambda activity: isinstance(activity, discord.Spotify), member.activities),
        )
        if spotify_activity is None:
            address = 'nie słuchasz' if member == ctx.author else f'{member.display_name} nie słucha'
            embed = self.bot.generate_embed('⏹', f'W tym momencie {address} niczego na Spotify')
        else:
            embed = self.bot.generate_embed(
                '▶️',
                spotify_activity.title,
                url=f'https://open.spotify.com/go?uri=spotify:track:{spotify_activity.track_id}',
            )
            embed.set_thumbnail(url=spotify_activity.album_cover_url)
            embed.add_field(name='W wykonaniu', value=', '.join(spotify_activity.artists))
            embed.add_field(name='Z albumu', value=spotify_activity.album)
            embed.add_field(name='Długość', value=human_amount_of_time(spotify_activity.duration.total_seconds()))
            # search for the song on YouTube
            youtube_search_query = f'{spotify_activity.title} {" ".join(spotify_activity.artists)}'
            try:
                youtube_search_result = self.bot.youtube_client.search(youtube_search_query)
            except:
                capture_exception()
            else:
                # add a link to a YouTube video if a match was found
                if (
                    youtube_search_result is not None
                    and SequenceMatcher(None, youtube_search_query, youtube_search_result.title).ratio() > 0.25
                ):
                    embed.add_field(name='Posłuchaj na YouTube', value=youtube_search_result.url, inline=False)
                    embed.set_image(url=youtube_search_result.thumbnail_url)
            embed.set_footer(text=self.FOOTER_TEXT, icon_url=self.FOOTER_ICON_URL)
        await self.bot.send(ctx, embed=embed)


async def setup(bot: Somsiad):
    await bot.add_cog(Spotify(bot))
