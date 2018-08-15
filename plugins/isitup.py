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

@client.command(aliases=['isup', 'up'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def isitup(ctx, *args):
    """Returns information about website status."""
    if len(args) == 0:
        await ctx.send(f':warning: Musisz podać parametr wyszukiwania, {ctx.author.mention}.')
    else:
        query = ' '.join(args)
        url = f'https://isitup.org/{query}.json'
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
                        description = (f'Strona [{res["domain"]}](http://{res["domain"]}) jest dostępna. '
                            f'Z IP [{res["response_ip"]}](http://{res["response_ip"]}) otrzymano kod odpowiedzi '
                            f'[{res["response_code"]}]({res_code}) w czasie {int(res_time)} ms.')
                    # Website offline
                    elif res['status_code'] == 2:
                        description = (f'Wygląda na to, że strona [{res["domain"]}](http://{res["domain"]}) '
                            'jest niedostępna!')
                    # Wrong URL
                    elif res['status_code'] == 3:
                        description = ('Do wykonania testu potrzebny jest poprawny adres URL. Spróbuj ponownie.')
                    embed = discord.Embed(title='Is it up?', description=description, color=brand_color)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f':warning: Nie można połączyć się z serwisem isitup.org, {ctx.author.mention}')
