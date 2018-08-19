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
import re
from somsiad_helper import *
from version import __version__


@client.command(aliases=['exchange', 'kantor', 'kurs'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def currency(ctx, *args):
    '''Provides currency exchange rates.'''
    embed = discord.Embed(title='Kantor', color=brand_color)
    if len(args) == 0:
        embed.add_field(name=':warning: Błąd', value=f'Musisz podać parametr wyszukiwania, {ctx.author.mention}.')
        await ctx.send(embed=embed)
    else:
        query = ' '.join(args)
        queryRegex = re.compile(r'''
                                (([0-9]*[.,])?[0-9]+)?      # optional number
                                (\s)?                       # whitespace
                                ([a-zA-Z]{2,4})             # 'fr' value
                                (\s)?                       # whitespace
                                (to|in|na|do|w)?            # optional preposition
                                (((\s)?([a-zA-Z]{2,4}))*)   # optional 'to' value
                                ''', re.VERBOSE)
        mo = queryRegex.search(query)
        if mo is not None:
            if mo.group(1) is not None:
                num = mo.group(1)
                num = num.replace(',', '.')
                num = float(num)
            fr = mo.group(4).upper()
            if mo.group(7) != '':
                to = mo.group(7).upper().lstrip()
                to = to.replace(' ', ',')
            else:
                to = 'USD,EUR,PLN'
            crypto_url = (f'https://min-api.cryptocompare.com/data/price?fsym={fr}&tsyms={to}' +
                          f'&extraParams=Somsiad{__version__}')
            headers = {'User-Agent': f'Somsiad {__version__}'}
            async with aiohttp.ClientSession() as session:
                async with session.get(crypto_url, headers=headers) as r:
                    if r.status == 200:
                        res = await r.json()
                        if 'Response' in res:
                            if res['Response'] == 'Error' and res['Type'] == 1:
                                embed.add_field(name=':warning: Błąd',
                                                value='Niewłaściwie skonstruowane zapytanie. Zapytanie musi mieć ' +
                                                'formę " X WALUTA1 w WALUTA2 WALUTA3 ...", gdzie "X" to wartość ' +
                                                'wyrażona w liczbach, a "WALUTA1" itd. to kody zgodne z [ISO 4217]' +
                                                '(https://en.wikipedia.org/wiki/ISO_4217#Active_codes) ' +
                                                'lub kody kryptowalut. Wartość "X" oraz fragment "w WALUTA2 WALUTA3' +
                                                ' ..." są opcjonalne.', inline=False)
                            else:
                                embed.add_field(name=':warning: Błąd', value='Niewłaściwie skonstruowane zapytanie.',
                                                inline=False)
                        else:
                            if 'num' not in locals():
                                num = 1
                            currency_values = [(str(num * v) + ' ' + k)
                                               for k, v in res.items()]
                            currency_values = '\n'.join(currency_values)
                            embed.add_field(name=f'{num:.2f} {fr}', value=currency_values, inline=False)
                            embed.set_footer(text='Dane z CryptoCompare.com (CC BY-NC 3.0)')
                        await ctx.send(embed=embed)
                    else:
                        embed.add_field(name=':warning: Błąd', value='Nie można połączyć się z serwisem.',
                                        inline=False)
                        await ctx.send(embed=embed)
        else:
            embed.add_field(name=':warning: Błąd',
                            value='Niewłaściwie skonstruowane zapytanie. Zapytanie musi mieć ' +
                            'formę " X WALUTA1 w WALUTA2 WALUTA3 ...", gdzie "X" to wartość ' +
                            'wyrażona w liczbach, a "WALUTA1" itd. to kody zgodne z [ISO 4217]' +
                            '(https://en.wikipedia.org/wiki/ISO_4217#Active_codes) ' +
                            'lub kody kryptowalut. Wartość "X" oraz fragment "w WALUTA2 WALUTA3' +
                            ' ..." są opcjonalne.', inline=False)
            await ctx.send(embed=embed)
