import discord
from discord.ext import commands
import aiohttp
import re
from somsiad_helper import *

@client.command(aliases=['exchange', 'kantor', 'kurs'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def currency(ctx, *args):
    '''Provides currency exchange rates'''
    em = discord.Embed(title='Kantor', color=brand_color)
    if len(args) == 0:
        em.add_field(name=':warning: Błąd', value=f'Musisz podać parametr wyszukiwania, {ctx.author.mention}.')
        await ctx.send(embed=em)
    else:
        query = ' '.join(args)

        queryRegex = re.compile(r'''
            (([0-9]*[.,])?[0-9]+)?  # optional number
            (\s)?                   # optional whitespace
            ([a-zA-Z]{3}){1}        # 'fr' 3 char value
            (\s)?                   # optional whitespace
            (to|in|na|do|w)?        # optional conjuction
            (\s)?                   # optional whitespace
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
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as r:
                        if r.status == 200:
                            res = await r.json()
                            currency_value = res[fr + '_' + to]['val']
                            if 'num' in locals():
                                currency_value = currency_value * num
                            else:
                                num = 1
                            currency_value = f'{currency_value:.2f}'

                            em.add_field(name=f'{num:.2f} {fr}', value=f'{currency_value} {to}',
                                inline=False)
                            await ctx.send(embed=em)
                        else:
                            em.add_field(name=':warning: Błąd', value='Nie można połączyć się z serwisem.',
                                inline=False)
                            await ctx.send(embed=em)
            else:
                em.add_field(name=':warning: Błąd',
                    value='Niewłaściwie skonstruowane zapytanie. Zapytanie musi mieć formę "X WALUTA1 w WALUTA2", ' +
                        'gdzie "WALUTA1" i "WALUTA2" to trzyliterowe kody, zgodne z ' +
                        '[ISO 4217](https://en.wikipedia.org/wiki/ISO_4217Active_codes), ' +
                        'a "X" to wartość wyrażona w liczbach, którą można pominąć.', inline=False)
                await ctx.send(embed=em)

        else:
            em.add_field(name=':warning: Błąd',
                value='Niewłaściwie skonstruowane zapytanie. Zapytanie musi mieć format "X WALUTA1 w WALUTA2", ' +
                    'gdzie "WALUTA1" i "WALUTA2" to trzyliterowe kody, zgodne z ' +
                    '[ISO 4217](https://en.wikipedia.org/wiki/ISO_4217Active_codes), ' +
                    'a "X" to wartość wyrażona w liczbach, którą można pominąć.', inline=False)
            await ctx.send(embed=em)
