# Copyright 2018-2020 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import aiohttp
import discord
from discord.ext import commands
from core import cooldown
from utilities import text_snippet
from configuration import configuration


class Wikipedia(commands.Cog):
    """Handles Wikipedia search."""
    FOOTER_TEXT = 'Wikipedia'
    FOOTER_ICON_URL = (
        'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Wikipedia%27s_W.svg/60px-Wikipedia%27s_W.svg.png'
    )

    class SearchResult:
        """Wikipedia search results."""
        __slots__ = 'language', 'status', 'title', 'url', 'articles'

        def __init__(self, language):
            self.language = language
            self.status = None
            self.title = None
            self.url = None
            self.articles = []

        def __str__(self):
            return self.title

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def link(language: str, path: str) -> str:
        """Generates a link to Wikipedia using the provided language and path."""
        return f'https://{language.lower()}.wikipedia.org/{path.strip("/")}'

    async def search(self, language: str, title: str):
        """Returns the closest matching article or articles from Wikipedia."""
        params = {
            'action': 'opensearch', 'search': title, 'limit': 25, 'format': 'json'
        }
        search_result = self.SearchResult(language)
        try:
            # use OpenSearch API first to get accurate page title of the result
            async with self.bot.session.get(
                    self.link(language, 'w/api.php'), headers=self.bot.HEADERS, params=params
            ) as title_request:
                search_result.status = title_request.status
                if title_request.status == 200:
                    title_data = await title_request.json()
                    if title_data[1]:
                        # use the title retrieved from the OpenSearch response as a search term in the REST request
                        query = title_data[1][0]
                        async with self.bot.session.get(
                                self.link(language, f'api/rest_v1/page/summary/{query}'), headers=self.bot.HEADERS
                        ) as article_request:
                            search_result.status = article_request.status
                            if article_request.status == 200:
                                article_data = await article_request.json()
                                search_result.title = article_data['title']
                                search_result.url = article_data['content_urls']['desktop']['page']
                                if article_data['type'] == 'disambiguation':
                                    # use results from OpenSearch to create a list of links from disambiguation page
                                    for i, option in enumerate(title_data[1][1:]):
                                        search_result.articles.append({
                                            'title': option,
                                            'summary': None,
                                            'url': title_data[3][i+1].replace('(', '%28').replace(')', '%29'),
                                            'thumbnail_url': None
                                        })
                                elif article_data['type'] == 'standard':
                                    if len(article_data['extract']) > 400:
                                        summary = text_snippet(article_data['extract'], 400)
                                    else:
                                        summary = article_data['extract']
                                    thumbnail_url = (
                                        article_data['thumbnail']['source'] if 'thumbnail' in article_data else None
                                    )
                                    search_result.articles.append({
                                        'title': article_data['title'],
                                        'summary': summary,
                                        'url': article_data['content_urls']['desktop']['page'],
                                        'thumbnail_url': thumbnail_url
                                    })
        except aiohttp.client_exceptions.ClientConnectorError:
            pass
        return search_result

    async def embed_search_result(self, language: str, title: str) -> discord.Embed:
        """Generates an embed presenting the closest matching article or articles from Wikipedia."""
        search_result = await self.search(language, title)
        if search_result.status is None:
            embed = self.bot.generate_embed(
                '⚠️', f'Nie istnieje wersja językowa Wikipedii o kodzie "{language.upper()}"'
            )
        elif search_result.status == 200:
            number_of_articles = len(search_result.articles)
            if number_of_articles > 1:
                disambiguation = []
                for article in search_result.articles:
                    disambiguation.append(f'• [{article["title"]}]({article["url"]})')
                embed = self.bot.generate_embed(
                    '❓', f'Hasło "{search_result.title}" może odnosić się do:', '\n'.join(disambiguation),
                    url=search_result.url
                )
            elif number_of_articles == 1:
                embed = self.bot.generate_embed(
                    None, search_result.articles[0]['title'], search_result.articles[0]['summary'],
                    url=search_result.articles[0]['url']
                )
                if search_result.articles[0]['thumbnail_url'] is not None:
                    embed.set_thumbnail(url=search_result.articles[0]['thumbnail_url'])
            else:
                embed = self.bot.generate_embed('🙁', f'Brak wyników dla hasła "{title}"')
        else:
            embed = self.bot.generate_embed('⚠️', 'Nie udało się połączyć z Wikipedią')
        embed.set_footer(
            text=self.FOOTER_TEXT if search_result.status is None else f'{self.FOOTER_TEXT} {language.upper()}',
            icon_url=self.FOOTER_ICON_URL
        )
        return embed

    @commands.command(aliases=['wiki', 'w'])
    @cooldown()
    async def wikipedia(self, ctx, language, *, title = 'Wikipedia'):
        """The Wikipedia search command."""
        embed = await self.embed_search_result(language, title)
        await self.bot.send(ctx, embed=embed)

    @wikipedia.error
    async def wikipedia_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            embed = self.bot.generate_embed('⚠️', 'Nie podano wersji językowej Wikipedii')
            embed.set_footer(text=self.FOOTER_TEXT, icon_url=self.FOOTER_ICON_URL)
            await self.bot.send(ctx, embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Wikipedia(bot))
