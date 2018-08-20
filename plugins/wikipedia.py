# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import logging
import aiohttp
import discord
from discord.ext import commands
from somsiad_helper import *
from version import __version__

async def wikipedia_search(ctx, args, lang):
    """Returns the closest matching article from Wikipedia."""
    embed = discord.Embed(title="Wikipedia", color=brand_color)
    if len(args) == 0:
        embed.add_field(name=':warning: Błąd', value=f'Nie podano szukanego hasła!')
        await ctx.send(embed=embed)
    else:
        query = '_'.join(args)

        open_url = f'https://{lang}.wikipedia.org/w/api.php?action=opensearch&search={query}&limit=10&format=json'
        headers = {'User-Agent': user_agent}
        async with aiohttp.ClientSession() as session:
            # Use OpenSearch API first to get accurate page title of the result
            async with session.get(open_url, headers=headers) as r_open:
                if r_open.status == 200:
                    res_open = await r_open.json()
                    if len(res_open[1]) < 1:
                        embed.add_field(name=':slight_frown: Niepowodzenie',
                            value=f'Nie znaleziono żadnego wyniku pasującego do hasła "{query}".')
                        await ctx.send(embed=embed)
                    else:
                        # Use title retrieved from OpenSearch response
                        # as a search term in REST request
                        query = res_open[1][0]
                        search_url = f'https://{lang}.wikipedia.org/api/rest_v1/page/summary/{query}'
                        async with session.get(search_url, headers=headers) as r:
                            if r.status == 200:
                                res = await r.json()

                                if res['type'] == 'disambiguation':
                                    # Use results from OpenSearch to create a list of links from disambiguation page
                                    title = 'Hasło \"' + res['title'] + '\" może odnosić się do:'
                                    options_str_full = ''
                                    for i, option in enumerate(res_open[1][1:]):
                                        option_url = res_open[3][i+1]
                                        option_url = option_url.replace('(', '%28')
                                        option_url = option_url.replace(')', '%29')
                                        options_str = ('• [' + option + '](' + option_url + ')\n')
                                        options_str_full += options_str
                                    embed.add_field(name=title, value=options_str_full, inline=False)
                                    await ctx.send(embed=embed)

                                elif res['type'] == 'standard':
                                    title = res['title']
                                    # Reduce the length of summary to 400 chars
                                    if len(res['extract']) < 400:
                                        summary = res['extract']
                                    else:
                                        summary = res['extract'][:400].rstrip() + '...'
                                    url = res['content_urls']['desktop']['page']
                                    if 'thumbnail' in res:
                                        thumbnail = res['thumbnail']['source']
                                        embed.set_thumbnail(url=thumbnail)

                                    embed.add_field(name=title, value=summary, inline=False)
                                    embed.add_field(name='Pełny artykuł: ', value=url, inline=True)
                                    await ctx.send(embed=embed)
                            else:
                                embed.add_field(name=':warning: Błąd', value='Nie udało się połączyć z serwisem!')
                                await ctx.send(embed=embed)
                else:
                    embed.add_field(name=':warning: Błąd', value='Nie udało się połączyć z serwisem!')
                    await ctx.send(embed=embed)


@client.command(aliases=['wikipl', 'wpl'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def wikipediapl(ctx, *args):
    """Polish version of wikipedia_search."""
    lang = 'pl'
    await wikipedia_search(ctx, args, lang)

@client.command(aliases=['wikien', 'wen'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def wikipediaen(ctx, *args):
    """English version of wikipedia_search."""
    lang = 'en'
    await wikipedia_search(ctx, args, lang)
