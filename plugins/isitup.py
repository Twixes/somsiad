# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import aiohttp
import discord
from core import somsiad
from configuration import configuration


@somsiad.command()
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def isitup(ctx, *, query):
    """Returns information about website status."""
    FOOTER_TEXT = 'Is it up?'

    url = f'https://isitup.org/{query}.json'
    RESPONSE_CODE_WIKIPEDIA_URLS = {
        1:'https://pl.wikipedia.org/wiki/Kod_odpowiedzi_HTTP#Kody_informacyjne',
        2:'https://pl.wikipedia.org/wiki/Kod_odpowiedzi_HTTP#Kody_powodzenia',
        3:'https://pl.wikipedia.org/wiki/Kod_odpowiedzi_HTTP#Kody_przekierowania',
        4:'https://pl.wikipedia.org/wiki/Kod_odpowiedzi_HTTP#Kody_błędu_aplikacji_klienta',
        5:'https://pl.wikipedia.org/wiki/Kod_odpowiedzi_HTTP#Kody_błędu_serwera_HTTP'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status == 200:
                res = await r.json()
                # Website online
                if res['status_code'] == 1:
                    res_code_wikipedia_url = RESPONSE_CODE_WIKIPEDIA_URLS[int(str(res['response_code'])[0])]
                    res_time = res['response_time'] * 1000
                    embed = discord.Embed(
                        title=f':white_check_mark: Strona {res["domain"]} jest dostępna',
                        url=f'http://{res["domain"]}',
                        description=f'Z IP [{res["response_ip"]}](http://{res["response_ip"]}) otrzymano '
                        f'kod odpowiedzi [{res["response_code"]}]({res_code_wikipedia_url}) '
                        f'w czasie {int(res_time)} ms.',
                        color=somsiad.COLOR
                    )
                # Website offline
                elif res['status_code'] == 2:
                    embed = discord.Embed(
                        title=f':red_circle: Strona {res["domain"]} jest niedostępna',
                        url=f'http://{res["domain"]}',
                        color=somsiad.COLOR
                    )
                # Wrong URL
                elif res['status_code'] == 3:
                    embed = discord.Embed(
                        title=':warning: Podany adres jest niepoprawny!',
                        color=somsiad.COLOR
                    )
            else:
                embed = discord.Embed(
                    title=':warning: Nie udało się połączyć z serwerem sprawdzania statusu stron!',
                    color=somsiad.COLOR
                )

    embed.set_footer(text=FOOTER_TEXT)
    await somsiad.send(ctx, embed=embed)


@isitup.error
async def isitup_error(ctx, error):
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        embed = discord.Embed(
            title=f':warning: Nie podano adresu strony do sprawdzenia!',
            color=somsiad.COLOR
        )
        await somsiad.send(ctx, embed=embed)
