# Copyright 2018-2020 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from discord.ext import commands
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from core import cooldown
from configuration import configuration


class Google(commands.Cog):
    FOOTER_TEXT = 'Google'
    FOOTER_ICON_URL = 'https://www.google.com/favicon.ico'

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cse = build('customsearch', 'v1', developerKey=configuration['google_key']).cse()

    async def search(
        self, query: str, *,
        language: str = 'pl', number_of_results: int = 1, safe: str = 'active', search_type: str = None
    ) -> list:
        try:
            query = self.cse.list(
                q=query, cx=configuration['google_custom_search_engine_id'], hl=language, num=number_of_results,
                safe=safe, searchType=search_type
            )
            results = await self.bot.loop.run_in_executor(None, query.execute)
            return [] if results['searchInformation']['totalResults'] == '0' else results['items']
        except HttpError:
            return None

    @commands.command(aliases=['g', 'gugiel'])
    @cooldown()
    @commands.guild_only()
    async def google(self, ctx, *, query='bot somsiad'):
        """Returns first matching website from Google using the provided Custom Search Engine."""
        results = await self.search(query)
        if results is None:
            embed = self.bot.generate_embed(
                '⚠️', 'Nie udało się połączyć z serwerem wyszukiwania',
                'Możliwe, że wyczerpał się dzienny limit wyszukiwań.'
            )
        elif results == []:
            embed = self.bot.generate_embed('🙁', f'Brak wyników dla zapytania "{query}"')
        else:
            result = results[0]
            site_protocol = result['link'].split('://')[0]
            embed = self.bot.generate_embed(None, result['title'], result['snippet'], url=result['link'])
            embed.set_author(
                name=result['displayLink'],
                url=f'{site_protocol}://{result["displayLink"]}'
            )
            try:
                embed.set_image(
                    url=result['pagemap']['cse_image'][0]['src']
                )
            except KeyError:
                pass
        embed.set_footer(text=self.FOOTER_TEXT, icon_url=self.FOOTER_ICON_URL)
        await self.bot.send(ctx, embed=embed)

    @commands.command(aliases=['googleimage', 'gi', 'i'])
    @cooldown()
    @commands.guild_only()
    async def google_image(self, ctx, *, query='bot somsiad'):
        """Returns first matching image from Google using the provided Custom Search Engine."""
        results = await self.search(query, search_type='image')
        if results is None:
            embed = self.bot.generate_embed(
                '⚠️', 'Nie udało się połączyć z serwerem wyszukiwania',
                'Możliwe, że wyczerpał się dzienny limit wyszukiwań.'
            )
        elif results == []:
            embed = self.bot.generate_embed('🙁', f'Brak wyników dla zapytania "{query}"')
        else:
            result = results[0]
            site_protocol = result['link'].split('://')[0]
            embed = self.bot.generate_embed(None, result['title'], url=result['image']['contextLink'])
            embed.set_author(
                name=result['displayLink'],
                url=f'{site_protocol}://{result["displayLink"]}'
            )
            embed.set_image(
                url=result['link']
            )
        embed.set_footer(text=self.FOOTER_TEXT, icon_url=self.FOOTER_ICON_URL)
        await self.bot.send(ctx, embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Google(bot))
