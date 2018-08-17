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
        if query.startswith(('krypto', 'crypto')):
            queryRegex = re.compile(r'''
                                    (krypto|crypto)             # subcommand
                                    (\s)+                       # whitespace
                                    (([0-9]*[.,])?[0-9]+)?      # optional number
                                    (\s)?                       # whitespace
                                    ([a-zA-Z]{2,4})             # 'fr' value
                                    (\s)?                       # whitespace
                                    (to|in|na|do|w)?            # optional preposition
                                    (((\s)?([a-zA-Z]{2,4}))*)   # optional 'to' value
                                    ''', re.VERBOSE)
            mo = queryRegex.search(query)
            if mo != None:
                if mo.group(3) != None:
                    num = mo.group(3)
                    num = num.replace(',', '.')
                    num = float(num)
                fr = mo.group(6).upper()
                if mo.group(9) != '':
                    to = mo.group(9).upper().lstrip()
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
                                        value='Niewłaściwie skonstruowane zapytanie. Zapytanie musi mieć formę ' +
                                            '"krypto X COIN1 w COIN2 COIN3 ...", gdzie "X" to wartość wyrażona ' +
                                            'w liczbach, a "COIN1" itd. to kody kryptowalut. Wartość "X" oraz ' +
                                            'fragment "w COIN2 COIN3 ..." są opcjonalne.',
                                        inline=False)
                                else:
                                    embed.add_field(name=':warning: Błąd', value='Niewłaściwie skonstruowane zapytanie.',
                                        inline=False)
                            else:
                                if not 'num' in locals():
                                    num = 1
                                currency_values = [(str(num * v) + ' ' + k)
                                    for k, v in res.items()]
                                currency_values = '\n'.join(currency_values)
                                
                                embed.add_field(name=f'{num:.2f} {fr}', value=currency_values, inline=False)
                                embed.set_footer(
                                    text='Dane z CryptoCompare.com (CC BY-NC 3.0)')
                            await ctx.send(embed=embed)
                        else:
                            embed.add_field(name=':warning: Błąd', value='Nie można połączyć się z serwisem.', 
                                inline=False)
                            await ctx.send(embed=embed)
            else:
                embed.add_field(name=':warning: Błąd', 
                    value='Niewłaściwie skonstruowane zapytanie. Zapytanie musi mieć formę ' +
                        '"krypto X COIN1 w COIN2 COIN3 ...", gdzie "X" to wartość wyrażona ' +
                        'w liczbach, a "COIN1" itd. to kody kryptowalut. Wartość "X" oraz ' +
                        'fragment "w COIN2 COIN3 ..." są opcjonalne.',
                        inline=False)
                await ctx.send(embed=embed)
        else:
            queryRegex = re.compile(r'''
                (([0-9]*[.,])?[0-9]+)?  # optional number
                (\s)?                   # whitespace
                ([a-zA-Z]{3}){1}        # 'fr' 3 char value
                (\s)?                   # whitespace
                (to|in|na|do|w)?        # optional preposition
                (\s)?                   # whitespace
                ([a-zA-Z]{3}){1}        # 'to' 3 char value
                ''', re.VERBOSE)
    
            mo = queryRegex.search(query)
            if mo != None:
                if mo.group(1) != None:
                    num = mo.group(1)
                    num = num.replace(',', '.')
                    num = float(num)
                fr = mo.group(4).upper()
                to = mo.group(8).upper()
                # Check locally if provided values are correct currency codes
                # to reduce the amount of API calls
                with open(os.path.join(bot_dir, 'data', 'currency_codes.txt')) as f:
                    ccod = [line.strip() for line in f.readlines() if not line.strip().startswith('#')]
                if all(value in ccod for value in (fr, to)):
                    url = f'https://free.currencyconverterapi.com/api/v6/convert?q={fr}_{to}&compact=y'
                    headers = {"User-Agent": f'Somsiad {__version__}'}
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers) as r:
                            if r.status == 200:
                                res = await r.json()
                                currency_value = res[fr + '_' + to]['val']
                                if 'num' in locals():
                                    currency_value = currency_value * num
                                else:
                                    num = 1
                                currency_value = f'{currency_value:.2f}'
    
                                embed.add_field(name=f'{num:.2f} {fr}', value=f'{currency_value} {to}',
                                    inline=False)
                                await ctx.send(embed=embed)
                            else:
                                embed.add_field(name=':warning: Błąd', value='Nie można połączyć się z serwisem.',
                                    inline=False)
                                await ctx.send(embed=embed)
                else:
                    embed.add_field(name=':warning: Błąd',
                        value='Niewłaściwie skonstruowane zapytanie. Zapytanie musi mieć formę "X WALUTA1 WALUTA2", ' +
                            'gdzie "WALUTA1" i "WALUTA2" to trzyliterowe kody, zgodne z ' +
                            '[ISO 4217](https://en.wikipedia.org/wiki/ISO_4217#Active_codes), ' +
                            'a "X" to wartość wyrażona w liczbach, którą można pominąć.', inline=False)
                    await ctx.send(embed=embed)
    
            else:
                embed.add_field(name=':warning: Błąd',
                    value='Niewłaściwie skonstruowane zapytanie. Zapytanie musi mieć format "X WALUTA1 WALUTA2", ' +
                        'gdzie "WALUTA1" i "WALUTA2" to trzyliterowe kody, zgodne z ' +
                        '[ISO 4217](https://en.wikipedia.org/wiki/ISO_4217#Active_codes), ' +
                        'a "X" to wartość wyrażona w liczbach, którą można pominąć.', inline=False)
                await ctx.send(embed=embed)
    
