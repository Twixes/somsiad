# Copyright 2018-2019 ondondil & Twixes

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
from somsiad import somsiad


@somsiad.bot.command(aliases=['exchange', 'kantor', 'kurs'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def currency(ctx, *, query):
    """Provides (crypto)currency exchange rates."""
    FOOTER_TEXT = 'CryptoCompare.com (CC BY-NC 3.0)'
    FOOTER_ICON_URL = 'https://www.cryptocompare.com/media/20562/favicon.png'

    query_regex = re.compile(r'''
        (([0-9]*[.,])?[0-9]+)?      # optional number
        (\s)?                       # whitespace
        ([a-zA-Z]{2,4})             # 'initial' value
        (\s)?                       # whitespace
        (to|in|na|do|w)?            # optional preposition
        (((\s)?([a-zA-Z]{2,4}))*)   # optional 'target' value
    ''', re.VERBOSE)
    mo = query_regex.search(query)
    num = 1
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
        api_url = 'https://min-api.cryptocompare.com/data/price'
        headers = {'User-Agent': somsiad.user_agent}
        params = {
            'fsym': initial,
            'tsyms': target,
            'extraParams': somsiad.user_agent
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=headers, params=params) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if 'Response' in response_data:
                        # if response_data['Response'] == 'Error' and response_data['Type'] == 1: <- what is this for?
                        embed = discord.Embed(
                            title=':warning: Niewłaściwie skonstruowane zapytanie!',
                            description='Zapytanie musi mieć formę "X WALUTA1 w WALUTA2 WALUTA3 ...", '
                            'gdzie X to wartość wyrażona w liczbach, a WALUTY to [kody walut ISO 4217]'
                            '(https://en.wikipedia.org/wiki/ISO_4217#Active_codes) lub kody kryptowalut. '
                            'Wartość X oraz fragment WALUTA2 WALUTA3 są opcjonalne.',
                            color=somsiad.color
                        )
                    else:
                        currency_values = [
                            f'{str(num * value)} {currency}' for currency, value in response_data.items()
                        ]
                        currency_values = '\n'.join(currency_values)
                        embed = discord.Embed(
                            title=f'{num} {initial}',
                            description=currency_values,
                            color=somsiad.color
                        )
                else:
                    embed = discord.Embed(
                        title=':warning: Nie udało się połączyć z serwerem przelicznika walut!',
                        color=somsiad.color
                    )
    else:
        embed = discord.Embed(
            title=':warning: Niewłaściwie skonstruowane zapytanie!',
            description='Zapytanie musi mieć formę "X WALUTA1 w WALUTA2 WALUTA3 ...", '
            'gdzie X to wartość wyrażona w liczbach, a WALUTY to [kody walut ISO 4217]'
            '(https://en.wikipedia.org/wiki/ISO_4217#Active_codes) lub kody kryptowalut. '
            'Wartość X oraz fragment WALUTA2 WALUTA3 są opcjonalne.',
            color=somsiad.color
        )

    embed.set_footer(text=FOOTER_TEXT, icon_url=FOOTER_ICON_URL)
    await ctx.send(ctx.author.mention, embed=embed)


@currency.error
async def currency_error(ctx, error):
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        embed = discord.Embed(title=':warning: Błąd', description=f'Nie podano szukanego hasła!', color=somsiad.color)
        await ctx.send(ctx.author.mention, embed=embed)
