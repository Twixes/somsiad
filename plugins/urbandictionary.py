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

@client.command(aliases=['urban'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def urbandictionary(ctx, *args):
    '''Returns word definitions from Urban Dictionary'''
    if len(args) == 0:
        await ctx.send(f':warning: Musisz podać parametr wyszukiwania, {ctx.author.mention}.')
    else:
        query = '+'.join(args)
        url = f'https://api.urbandictionary.com/v0/define?term={query}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status == 200:
                    resp = await r.json()
                    bra_pat = re.compile(r'[\[\]]')
                    if resp['list']:
                        top_def = resp['list'][0] # Get top definition
                        word = top_def['word']
                        definition = top_def['definition']
                        definition = bra_pat.sub(r'', definition)
                        if len(definition) > 500:
                            definition = definition[:500] + '...' # Reduce output lenght
                        link = top_def['permalink']
                        example = top_def['example']
                        example = bra_pat.sub(r'', example)
                        if len(example) > 400:
                            example = example[:400] + '...' # Reduce output lenght
                        t_up = top_def['thumbs_up']
                        t_down = top_def['thumbs_down']
                        # Output results
                        em = discord.Embed(title='Urban Dictionary', color=brand_color)
                        em.add_field(name='Słowo:', value=word, inline=False)
                        em.add_field(name='Definicja:', value=definition, inline=False)
                        em.add_field(name='Przykład(y):', value=example, inline=False)
                        em.add_field(name='Głosy:', value=f':thumbsup: {str(t_up)} | :thumbsdown: {str(t_down)}')
                        em.add_field(name='Link:', value=link, inline=False)
                        await ctx.send(embed=em)
                    else:
                        await ctx.send(f'{ctx.author.mention}, nie znaleziono pasujących wyników.')
                else:
                    await ctx.send(':warning: Nie można połączyć się z serwisem Urban Dictionary, '
                        f'{ctx.author.mention}')
