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
from somsiad import somsiad


@somsiad.client.command(aliases=['gif'])
@discord.ext.commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], discord.ext.commands.BucketType.user)
@discord.ext.commands.guild_only()
async def giphy(ctx, *args):
    """Giphy search. Responds with the first GIF matching the query."""
    FOOTER_TEXT = 'Giphy'

    if not args:
        embed = discord.Embed(
            title=':warning: Błąd',
            description='Nie podano szukanego hasła!',
            color=somsiad.color
        )
    else:
        query = ' '.join(args)
        api_search_url = 'https://api.giphy.com/v1/gifs/search'
        headers = {'User-Agent': somsiad.user_agent}
        params = {
            'api_key': somsiad.conf["giphy_key"],
            'q': query,
            'limit': 1,
            'offset': 0,
            'rating': 'PG-13'
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(api_search_url, headers=headers, params=params) as response:
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

    embed.set_footer(text=FOOTER_TEXT)
    await ctx.send(ctx.author.mention, embed=embed)
