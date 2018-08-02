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

@client.command(aliases=['isup'])
@commands.cooldown(1, conf['cooldown'], commands.BucketType.user)
@commands.guild_only()
async def isitup(ctx, *args):
    '''Returns information about website status.'''
    if len(args) == 0:
        await ctx.send(':warning: Musisz podać parametr wyszukiwania, {}.'.format(ctx.author.mention))
    else:
        query = ' '.join(args)
        url = 'https://isitup.org/{}.json'.format(query)
        response_code_urls = {
            1:'https://pl.wikipedia.org/wiki/Kod_odpowiedzi_HTTP#Kody_informacyjne',
            2:'https://pl.wikipedia.org/wiki/Kod_odpowiedzi_HTTP#Kody_powodzenia',
            3:'https://pl.wikipedia.org/wiki/Kod_odpowiedzi_HTTP#Kody_przekierowania',
            4:'https://pl.wikipedia.org/wiki/Kod_odpowiedzi_HTTP#Kody_błędu_aplikacji_klienta',
            5:'https://pl.wikipedia.org/wiki/Kod_odpowiedzi_HTTP#Kody_błędu_serwera_HTTP'}
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status == 200:
                    res = await r.json()
                    # Website online
                    if res['status_code'] == 1:
                        res_code = response_code_urls[int(str(res['response_code'])[0])]
                        res_time = res['response_time'] * 1000
                        description = ('Strona [{}](http://{}) jest dostępna.'.format(res['domain'], res['domain']) +
                            ' Z IP [{}](http://{})'.format(res['response_ip'], res['response_ip']) +
                            ' otrzymano kod odpowiedzi [{}]({})'.format(res['response_code'], res_code) +
                            ' w czasie {} ms.'.format(int(res_time)))
                    # Website offline
                    elif res['status_code'] == 2:
                        description = ('Wygląda na to, że strona [{}](http://{}) jest niedostępna!'.format(
                            res['domain'], res['domain']))
                    # Wrong URL
                    elif res['status_code'] == 3:
                        description = ('Do wykonania testu potrzebny jest poprawny adres URL. Spróbuj ponownie.')
                    em = discord.Embed(title='Is It Up?', description=description, colour=0x336699)
                    await ctx.send(embed=em)
                else:
                    await ctx.send(':warning: Nie można połączyć się z serwisem isitup.org, {}'.format(
                        ctx.author.mention))
