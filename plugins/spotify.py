# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from difflib import SequenceMatcher
import discord
from somsiad import somsiad
from utilities import TextFormatter
from plugins.youtube import youtube


@somsiad.bot.command(aliases=['kanał', 'kanal'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def spotify(ctx, member: discord.Member = None):
    """Shares the song currently played on Spotify by the provided user (or if not provided, by the invoking user)."""
    if member is None:
        member = ctx.author

    spotify_activity = None
    for activity in member.activities:
        if isinstance(activity, discord.activity.Spotify):
            spotify_activity = activity
            break

    if spotify_activity is None:
        embed = discord.Embed(
            title=':stop_button: W tym momencie '
            f'{"nie słuchasz" if member == ctx.author else f"{member.display_name} nie słucha"} niczego na Spotify',
            color=somsiad.color
        )
    else:
        embed = discord.Embed(
            title=f':arrow_forward: {member.activity.title}',
            url=f'https://open.spotify.com/go?uri=spotify:track:{member.activity.track_id}',
            color=somsiad.color
        )
        embed.set_thumbnail(url=member.activity.album_cover_url)
        embed.add_field(name='W wykonaniu', value=', '.join(member.activity.artists))
        embed.add_field(name='Z albumu', value=member.activity.album)
        embed.add_field(
            name='Długość', value=TextFormatter.human_readable_time(member.activity.duration.total_seconds())
        )

        # Search for the song on YouTube
        youtube_search_query = f'{member.activity.title} {" ".join(member.activity.artists)}'
        youtube_search_result = youtube.search(youtube_search_query)
        # Add a link to a YouTube video if a match was found
        if (
                youtube_search_result and
                SequenceMatcher(None, youtube_search_query, youtube_search_result[0]['snippet']['title']).ratio() > 0.25
        ):
            video_id = youtube_search_result[0]['id']['videoId']
            video_thumbnail_url = youtube_search_result[0]['snippet']['thumbnails']['medium']['url']
            embed.add_field(
                name='Posłuchaj na YouTube', value=f'https://www.youtube.com/watch?v={video_id}', inline=False
            )
            embed.set_image(url=video_thumbnail_url)

        embed.set_footer(
            text='Spotify',
            icon_url='https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/'
            'Spotify_logo_without_text.svg/60px-Spotify_logo_without_text.svg.png'
        )

    await ctx.send(f'{ctx.author.mention}', embed=embed)
