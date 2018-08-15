# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from discord.ext import commands
import aiohttp
from somsiad_helper import *
from version import __version__

@client.command(aliases=['i', 'img'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def image_search(ctx, *args):
    '''Returns first matching image result from Qwant.'''
    if len(args) == 0:
        await ctx.send(f':warning: Musisz podać parametr wyszukiwania, {ctx.author.mention}.')
    else:
        query_1 = ' '.join(args)
        query = '+'.join(args)
        url = f'https://api.qwant.com/api/search/ia?q={query}&t=all'
        user_agent = f'SomsiadBot/{__version__}'
        headers = {'User-Agent': user_agent}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as r:
                if r.status == 200:
                    res = await r.json()
                    if res['data']['result']['items']:
                        res_short = res['data']['result']['items'][0]['data'][0]
                        # Qwant API is unofficial and undocumented
                        # The following code may be buggy
                        try:
                            img_url = res_short['images'][0]['media']
                            if not img_url.startswith('http'):
                                img_url = res_short['media']
                        except KeyError:
                            try:
                                img_url = res_short['images'][0]['url']
                            except KeyError:
                                img_url = res_short['media']
                        embed = discord.Embed(title=f'Wynik wyszukiwania obrazu dla zapytania: {query_1}',
                            description=img_url, color=brand_color)
                        embed.set_image(url=img_url)
                        await ctx.send(f'{ctx.author.mention}\n', embed=embed)
                    else:
                        await ctx.send(f'{ctx.author.mention}, nie znaleziono pasujących wyników.')
                else:
                    await ctx.send(f':warning: Nie można połączyć się z serwisem Qwant, {ctx.author.mention}')
