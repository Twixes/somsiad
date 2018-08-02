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
from somsiad_helper import *

@client.command(aliases=['i', 'img'])
@commands.cooldown(1, conf['cooldown'], commands.BucketType.user)
@commands.guild_only()
async def image_search(ctx, *args):
    '''Returns first matching image result from Qwant.'''
    if len(args) == 0:
        await ctx.send(':warning: Musisz podać parametr wyszukiwania, {}.'.format(ctx.author.mention))
    else:
        query_1 = ' '.join(args)
        query = '+'.join(args)
        url = 'https://api.qwant.com/api/search/ia?q={}&t=all'.format(query)
        usr_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0'
        headers = {'User-Agent': usr_agent}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as r:
                if r.status == 200:
                    res = await r.json()
                    if res['data']['result']['items']:
                        res_short = res['data']['result']['items'][0]['data'][0]
                        # Qwant API is unofficial and undocumented. Following code may be buggy.
                        # This is best I came up with.
                        try:
                            img_url = res_short['images'][0]['media']
                            if not img_url.startswith('http'):
                                img_url = res_short['media']
                        except KeyError:
                            try:
                                img_url = res_short['images'][0]['url']
                            except KeyError:
                                img_url = res_short['media']
                        em = discord.Embed(title='Wynik wyszukiwania obrazu dla zapytania: ' + '{}'.format(query_1),
                            description=img_url, colour=0x008000)
                        em.set_image(url=img_url)
                        await ctx.send('{}\n'.format(ctx.author.mention), embed=em)
                    else:
                        await ctx.send('{}, nie znaleziono pasujących wyników.'.format(ctx.author.mention))
                else:
                    await ctx.send(':warning: Nie można połączyć się z serwisem Qwant, {}'.format(ctx.author.mention))
