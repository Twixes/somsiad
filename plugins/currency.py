# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import re
import aiohttp
import discord
from discord.ext import commands
from somsiad_helper import *
from version import __version__


@somsiad.client.command(aliases=['exchange', 'kantor', 'kurs'])
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def currency(ctx, *args):
    """Provides (crypto)currency exchange rates."""
    FOOTER_TEXT = 'CryptoCompare.com (CC BY-NC 3.0)'
    FOOTER_ICON_URL = 'https://www.cryptocompare.com/media/20562/favicon.png'
    ERROR_NOTICE = ('Niewłaściwie skonstruowane zapytanie. Zapytanie musi mieć formę "X WALUTA1 w WALUTA2 '
        'WALUTA3 ...", gdzie X to wartość wyrażona w liczbach, a WALUTY to [kody '
        'walut ISO 4217](https://en.wikipedia.org/wiki/ISO_4217#Active_codes) lub kody '
        'kryptowalut. Wartość X oraz fragment WALUTA2 WALUTA3 są opcjonalne.')

    if not args:
        embed = discord.Embed(title=':warning: Błąd', description=f'Nie podano szukanego hasła!', color=somsiad.color)
    else:
        query = ' '.join(args)
        query_regex = re.compile(r'''
            (([0-9]*[.,])?[0-9]+)?      # optional number
            (\s)?                       # whitespace
            ([a-zA-Z]{2,4})             # 'initial' value
            (\s)?                       # whitespace
            (to|in|na|do|w)?            # optional preposition
            (((\s)?([a-zA-Z]{2,4}))*)   # optional 'target' value
        ''', re.VERBOSE)
        mo = query_regex.search(query)
        if mo is not None:
            if mo.group(1) is not None:
                num = mo.group(1)
                num = num.replace(',', '.')
                num = float(num)
            initial = mo.group(4).upper()
            if mo.group(7) != '':
                target = mo.group(7).upper().lstrip()
                target = target.replace(' ', ',')
            else:
                target = 'PLN,USD,EUR'
            headers = {'User-Agent': somsiad.user_agent}
            url_safe_user_agent = somsiad.user_agent.replace('/', '%2F')
            api_url = (f'https://min-api.cryptocompare.com/data/price?fsym={initial}&tsyms={target}'
                f'&extraParams={url_safe_user_agent}')
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        if 'Response' in response_data:
                            if response_data['Response'] == 'Error' and response_data['Type'] == 1:
                                embed = discord.Embed(
                                    title=':warning: Błąd', description=ERROR_NOTICE, color=somsiad.color)
                            else:
                                embed = discord.Embed(
                                    title=':warning: Błąd', description='Niewłaściwie skonstruowane zapytanie!',
                                    color=somsiad.color)
                        else:
                            if 'num' not in locals():
                                num = 1
                            currency_values = [(str(num * value) + ' ' + currency) for currency, value in
                                response_data.items()]
                            currency_values = '\n'.join(currency_values)
                            embed = discord.Embed(
                                title=f'{num} {initial}', description=currency_values, color=somsiad.color)
                    else:
                        embed = discord.Embed(
                            title=':warning: Błąd', description='Nie udało się połączyć z serwisem, CryptoCompare.com!',
                            color=somsiad.color)
        else:
            embed = discord.Embed(title=':warning: Błąd', description=ERROR_NOTICE, color=somsiad.color)
    embed.set_footer(text=FOOTER_TEXT, icon_url=FOOTER_ICON_URL)
    await ctx.send(embed=embed)
