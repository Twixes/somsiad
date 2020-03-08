# Copyright 2018-2020 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Optional, List, Dict
from defusedxml import ElementTree
from discord.ext import commands
from core import cooldown
from configuration import configuration


class Goodreads(commands.Cog):
    API_SEARCH_URL = 'https://www.goodreads.com/search/index.xml'
    FOOTER_TEXT = 'goodreads'
    FOOTER_ICON_URL = 'https://www.goodreads.com/favicon.ico'

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def resource_url(self, resource_type: str, resource_id: str) -> str:
        return f'https://www.goodreads.com/{resource_type}/show/{resource_id}'

    async def fetch_books(self, query: str) -> Optional[List[Dict[str, str]]]:
        books = None
        params = {
            'q': query,
            'key': configuration['goodreads_key']
        }
        async with self.bot.session.get(self.API_SEARCH_URL, headers=self.bot.HEADERS, params=params) as response:
            if response.status == 200:
                books = []
                results_text = await response.text()
                results_tree = ElementTree.fromstring(results_text)
                total_results = results_tree.find('.//total-results')
                if total_results.text != '0':
                    for element in results_tree.findall('.//work'):
                        books.append({})
                        for work in element.findall('*'):
                            if work.tag == 'id':
                                books[-1]['book_id'] = work.text
                            if work.tag == 'ratings_count':
                                books[-1]['ratings_count'] = work.text
                            if work.tag == 'average_rating':
                                books[-1]['average_rating'] = work.text
                            for best_book in work.findall('*'):
                                if best_book.tag == 'id':
                                    books[-1]['id'] = best_book.text
                                if best_book.tag == 'title':
                                    books[-1]['title'] = best_book.text
                                if best_book.tag == 'image_url':
                                    books[-1]['image_url'] = best_book.text
                                for author in best_book.findall('*'):
                                    if author.tag == 'name':
                                        books[-1]['author_name'] = author.text
                                    if author.tag == 'id':
                                        books[-1]['author_id'] = author.text
        return books

    @commands.command(aliases=['gr', 'książka', 'ksiazka', 'buk', 'book', 'buch'])
    @cooldown()
    async def goodreads(self, ctx, *, query):
        """Goodreads search. Responds with for the most popular books matching the query."""
        async with ctx.typing():
            books = await self.fetch_books(query)
            if books is None:
                embed = self.bot.generate_embed('⚠️', 'Nie udało się połączyć z serwisem')
            elif not books:
                embed = self.bot.generate_embed('🙁', f'Brak wyników dla zapytania "{query}"')
            else:
                embed = self.bot.generate_embed(
                    '📕', books[0]['title'], url=self.resource_url('book', books[0]['id'])
                )
                embed.set_author(name=books[0]['author_name'], url=self.resource_url('author', books[0]['author_id']))
                embed.add_field(name='Ocena', value=f'{float(books[0]["average_rating"]):n} / 5')
                embed.add_field(name='Liczba głosów', value=f'{int(books[0]["ratings_count"]):n}')
                embed.set_thumbnail(url=books[0]['image_url'])
                if len(books) > 1:
                    other_hit_parts = (
                        f'• [{other_hit["title"]}]({self.resource_url("book", other_hit["id"])}) – '
                        f'[{other_hit["author_name"]}]({self.resource_url("author", other_hit["author_id"])}) – '
                        f'{float(other_hit["average_rating"]):n} / 5'
                        for other_hit in books[1:4]
                    )
                    embed.add_field(name='Inne trafienia', value='\n'.join(other_hit_parts), inline=False)

            embed.set_footer(text=self.FOOTER_TEXT, icon_url=self.FOOTER_ICON_URL)
            await self.bot.send(ctx, embed=embed)

    @goodreads.error
    async def goodreads_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = self.bot.generate_embed('⚠️', 'Nie podano szukanego hasła')
            await self.bot.send(ctx, embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Goodreads(bot))
