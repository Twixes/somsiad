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


async def wikipedia_search(ctx, args, language):
    """Returns the closest matching article from Wikipedia."""
    FOOTER_TEXT = 'Wikipedia'
    FOOTER_ICON_URL = ('https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Wikipedia%27s_W.svg/'
        '60px-Wikipedia%27s_W.svg.png')

    if not args:
        embed = discord.Embed(
            title=':warning: Błąd',
            description='Nie podano szukanego hasła!',
            color=somsiad.color
        )
    else:
        query = '_'.join(args)
        api_url = f'https://{language}.wikipedia.org/w/api.php'
        params = {
            'action': 'opensearch',
            'search': query,
            'limit': 30,
            'format': 'json'
        }
        headers = {'User-Agent': somsiad.user_agent}
        async with aiohttp.ClientSession() as session:
            # Use OpenSearch API first to get accurate page title of the result
            async with session.get(api_url, headers=headers, params=params) as request:
                if request.status == 200:
                    response_data = await request.json()
                    if not response_data[1]:
                        embed = discord.Embed(
                            title=':slight_frown: Niepowodzenie',
                            description=f'Nie znaleziono żadnego wyniku pasującego do hasła "{query}".',
                            color=somsiad.color
                        )
                    else:
                        # Use title retrieved from OpenSearch response
                        # as a search term in REST request
                        query = response_data[1][0]
                        search_url = f'https://{language}.wikipedia.org/api/rest_v1/page/summary/{query}'
                        async with session.get(search_url, headers=headers) as r:
                            if r.status == 200:
                                res = await r.json()

                                if res['type'] == 'disambiguation':
                                    # Use results from OpenSearch to create a list of links from disambiguation page
                                    title = f'"{res["title"]}" może odnosić się do:'
                                    url = res['content_urls']['desktop']['page']
                                    options_str_full = ''
                                    for i, option in enumerate(response_data[1][1:]):
                                        option_url = response_data[3][i+1]
                                        option_url = option_url.replace('(', '%28')
                                        option_url = option_url.replace(')', '%29')
                                        options_str = (f'• [{option}]({option_url})\n')
                                        if len(options_str_full) + len(options_str) <= 2048:
                                            options_str_full += options_str
                                    embed = discord.Embed(
                                        title=title,
                                        url=url,
                                        description=options_str_full,
                                        color=somsiad.color
                                    )

                                elif res['type'] == 'standard':
                                    title = res['title']
                                    # Reduce the length of summary to 400 chars
                                    if len(res['extract']) <= 400:
                                        summary = res['extract']
                                    else:
                                        summary = res['extract'][:400].rstrip() + '...'
                                    url = res['content_urls']['desktop']['page']
                                    embed = discord.Embed(
                                        title=title,
                                        url=url,
                                        description=summary,
                                        color=somsiad.color
                                    )
                                    if 'thumbnail' in res:
                                        thumbnail = res['thumbnail']['source']
                                        embed.set_thumbnail(url=thumbnail)
                            else:
                                embed = discord.Embed(
                                    title=':warning: Błąd',
                                    description='Nie udało się połączyć z serwisem!',
                                    color=somsiad.color
                                )
                else:
                    embed = discord.Embed(
                        title=':warning: Błąd',
                        description='Nie udało się połączyć z serwisem!',
                        color=somsiad.color
                    )

    embed.set_footer(text=FOOTER_TEXT, icon_url=FOOTER_ICON_URL)
    await ctx.send(ctx.author.mention, embed=embed)


@somsiad.client.command(aliases=['wikipl', 'wpl'])
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def wikipediapl(ctx, *args):
    """Polish version of wikipedia_search."""
    await wikipedia_search(ctx, args, 'pl')


@somsiad.client.command(aliases=['wikien', 'wen'])
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def wikipediaen(ctx, *args):
    """English version of wikipedia_search."""
    await wikipedia_search(ctx, args, 'en')
