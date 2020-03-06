# Copyright 2018-2020 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import datetime as dt
import urllib.parse
from discord.ext import commands
from core import cooldown
from utilities import text_snippet


class UrbanDictionary(commands.Cog):
    FOOTER_TEXT = 'Urban Dictionary'
    API_URL = 'https://api.urbandictionary.com/v0/define'

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def expand_links(self, string: str) -> str:
        current_link = ''
        new_string = ''
        inside_link = False
        for character in string:
            if not inside_link and character == '[':
                inside_link = True
                new_string += '['
            elif inside_link and character == ']':
                quoted_current_link = urllib.parse.quote_plus(current_link)
                new_string += f'](https://www.urbandictionary.com/define.php?term={quoted_current_link})'
                inside_link = False
                current_link = ''
            else:
                if inside_link:
                    current_link += character
                new_string += character
        return new_string

    @commands.command(aliases=['urbandictionary', 'urban', 'ud'])
    @cooldown()
    async def urban_dictionary(self, ctx, *, query):
        """Returns Urban Dictionary word definition."""
        params = {'term': query}
        async with self.bot.session.get(self.API_URL, headers=self.bot.HEADERS, params=params) as request:
            if request.status == 200:
                response = await request.json()
                if response['list']:
                    result = response['list'][0] # get top definition
                    definition = self.expand_links(text_snippet(result['definition'], 500))
                    embed = self.bot.generate_embed(
                        None, result['word'], definition, url=result['permalink'],
                        timestamp=dt.datetime.fromisoformat(result['written_on'][:-1])
                    )
                    embed.add_field(name='👍', value=f'{result["thumbs_up"]:n}')
                    embed.add_field(name='👎', value=f'{result["thumbs_down"]:n}')
                else:
                    embed = self.bot.generate_embed('🙁', f'Brak wyników dla terminu "{query}"')
            else:
                embed = self.bot.generate_embed('⚠️', 'Nie udało się połączyć z serwisem')
        embed.set_footer(text=self.FOOTER_TEXT)
        await self.bot.send(ctx, embed=embed)

    @urban_dictionary.error
    async def urban_dictionary_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = self.bot.generate_embed('⚠️', 'Musisz podać termin do sprawdzenia')
            embed.set_footer(text=self.FOOTER_TEXT)
            await self.bot.send(ctx, embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(UrbanDictionary(bot))
