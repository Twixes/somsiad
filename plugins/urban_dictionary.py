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
from core import somsiad
from utilities import text_snippet
from configuration import configuration


@somsiad.command(aliases=['urbandictionary', 'urban'])
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
)
async def urban_dictionary(ctx, *, query):
    """Returns Urban Dictionary word definition."""
    FOOTER_TEXT = 'Urban Dictionary'

    api_url = 'https://api.urbandictionary.com/v0/define'
    headers = {'User-Agent': somsiad.USER_AGENT}
    params = {'term': query}
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers, params=params) as r:
            if r.status == 200:
                resp = await r.json()
                bra_pat = re.compile(r'[\[\]]')
                if resp['list']:
                    top_def = resp['list'][0] # Get top definition
                    word = top_def['word']
                    definition = top_def['definition']
                    definition = bra_pat.sub(r'', definition)
                    definition = text_snippet(definition, 500)
                    link = top_def['permalink']
                    example = top_def['example']
                    example = bra_pat.sub(r'', example)
                    example = text_snippet(example, 400)
                    t_up = top_def['thumbs_up']
                    t_down = top_def['thumbs_down']
                    # Output results
                    embed = discord.Embed(
                        title=word,
                        url=link,
                        description=definition,
                        color=somsiad.COLOR
                    )
                    embed.add_field(name=':thumbsup:', value=t_up)
                    embed.add_field(name=':thumbsdown:', value=t_down)
                else:
                    embed = discord.Embed(
                        title=f':slight_frown: Brak wyników dla terminu "{query}"',
                        color=somsiad.COLOR
                    )
            else:
                embed = discord.Embed(
                    title=':warning: Nie można połączyć się z serwisem!',
                    color=somsiad.COLOR
                )
    embed.set_footer(text=FOOTER_TEXT)

    await somsiad.send(ctx, embed=embed)


@urban_dictionary.error
async def urban_dictionary_error(ctx, error):
    FOOTER_TEXT = 'Urban Dictionary'

    embed = discord.Embed(
        title=':warning: Musisz podać termin do sprawdzenia!',
        color=somsiad.COLOR
    )
    embed.set_footer(text=FOOTER_TEXT)

    await somsiad.send(ctx, embed=embed)
