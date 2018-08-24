# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import aiohttp
import discord
from discord.ext import commands
from somsiad_helper import *


@somsiad.client.command(aliases=['gif'])
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def giphy(ctx, *args):
    """Giphy search. Responds with the first GIF matching the query."""
    FOOTER_TEXT = 'Giphy'
    FOOTER_ICON_URL = 'https://giphy.com/favicon.ico'
    if not args:
        embed = discord.Embed(
            title=':warning: Błąd',
            description='Nie podano szukanego hasła!',
            color=somsiad.color
        )
    else:
        query = ' '.join(args)
        query_url = (f'https://api.giphy.com/v1/gifs/search?api_key={somsiad.conf["giphy_key"]}&q={query}&limit=1'
            '&offset=0&rating=PG-13&lang=pl')
        headers = {'User-Agent': somsiad.user_agent}
        async with aiohttp.ClientSession() as session:
            async with session.get(query_url, headers=headers) as response:
                if response.status == 200:
                    response_data = await response.json()
                    response_data = response_data['data']
                    if response_data == []:
                        embed = discord.Embed(
                            title=':slight_frown: Niepowodzenie',
                            description=f'Nie znaleziono żadnego wyniku pasującego do zapytania "{query}".',
                            color=somsiad.color
                        )
                    else:
                        gif_url = response_data[0]['images']['original']['url']
                        embed = discord.Embed(
                            title=query,
                            color=somsiad.color
                        )
                        embed.set_image(url=gif_url)
                else:
                    embed = discord.Embed(
                        title=':warning: Błąd',
                        description='Nie można połączyć się z serwisem!',
                        color=somsiad.color
                    )
    embed.set_footer(text=FOOTER_TEXT, icon_url=FOOTER_ICON_URL)
    await ctx.send(ctx.author.mention, embed=embed)
