# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import aiohttp
import discord
from somsiad import somsiad
from utilities import TextFormatter


class Wikipedia:
    """Handles Wikipedia search."""
    FOOTER_TEXT = 'Wikipedia'
    FOOTER_ICON_URL = (
        'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Wikipedia%27s_W.svg/60px-Wikipedia%27s_W.svg.png'
    )
    headers = {'User-Agent': somsiad.USER_AGENT}

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

    @staticmethod
    def link(language: str, path: str) -> str:
        """Generates a link to Wikipedia using the provided language and path."""
        return f'https://{language}.wikipedia.org/{path.strip("/")}'

    @classmethod
    async def search(cls, language: str, title: str):
        """Returns the closest matching article or articles from Wikipedia."""
        params = {
            'action': 'opensearch',
            'search': title,
            'limit': 25,
            'format': 'json'
        }

        search_result = cls.SearchResult(language)
        try:
            async with aiohttp.ClientSession() as session:
                # Use OpenSearch API first to get accurate page title of the result
                async with session.get(
                        cls.link(language, 'w/api.php'), headers=cls.headers, params=params
                ) as title_request:
                    search_result.status = title_request.status

                    if title_request.status == 200:
                        title_data = await title_request.json()

                        if title_data[1]:
                            # Use the title retrieved from the OpenSearch response as a search term in the REST request
                            query = title_data[1][0]

                            async with session.get(
                                    cls.link(language, f'api/rest_v1/page/summary/{query}'), headers=cls.headers
                            ) as article_request:
                                search_result.status = article_request.status
                                if article_request.status == 200:
                                    article_data = await article_request.json()
                                    search_result.title = article_data["title"]
                                    search_result.url = article_data['content_urls']['desktop']['page']

                                    if article_data['type'] == 'disambiguation':
                                        # Use results from OpenSearch to create a list of links from disambiguation page
                                        for i, option in enumerate(title_data[1][1:]):
                                            article_url = title_data[3][i+1].replace('(', '%28').replace(')', '%29')
                                            search_result.articles.append({
                                                'title': option,
                                                'summary': None,
                                                'url': article_url,
                                                'thumbnail_url': None
                                                })

                                    elif article_data['type'] == 'standard':
                                        if len(article_data['extract']) > 400:
                                            summary = TextFormatter.limit_text_length(article_data['extract'], 400)
                                        else:
                                            summary =  article_data['extract']
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

    @classmethod
    async def embed_search_result(cls, language: str, title: str) -> discord.Embed:
        """Generates an embed presenting the closest matching article or articles from Wikipedia."""
        search_result = await cls.search(language, title)
        if search_result.status is None:
            embed = discord.Embed(
                title=f':warning: Nie istnieje wersja językowa Wikipedii o kodzie "{language.upper()}"!',
                color=somsiad.COLOR
            )
        elif search_result.status == 200:
            number_of_articles = len(search_result.articles)
            if number_of_articles > 1:
                disambiguation = []
                for article in search_result.articles:
                    disambiguation.append(f'• [{article["title"]}]({article["url"]})')
                embed = discord.Embed(
                    title=f'Hasło "{search_result.title}" może odnosić się do:',
                    url=search_result.url,
                    description='\n'.join(disambiguation),
                    color=somsiad.COLOR
                )
            elif number_of_articles == 1:
                embed = discord.Embed(
                    title=search_result.articles[0]['title'],
                    url=search_result.articles[0]['url'],
                    description=search_result.articles[0]['summary'],
                    color=somsiad.COLOR
                )
                if search_result.articles[0]['thumbnail_url'] is not None:
                    embed.set_thumbnail(url=search_result.articles[0]['thumbnail_url'])
            else:
                embed = discord.Embed(
                    title=f':slight_frown: Brak wyników dla hasła "{title}"',
                    color=somsiad.COLOR
                )

        else:
            embed = discord.Embed(
                title=':warning: Nie udało się połączyć z Wikipedią!',
                color=somsiad.COLOR
            )

        embed.set_footer(
            text=cls.FOOTER_TEXT if search_result.status is None else f'{cls.FOOTER_TEXT} {language.upper()}',
            icon_url=cls.FOOTER_ICON_URL
        )
        return embed


@somsiad.command(aliases=['wiki', 'w'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def wikipedia(ctx, language, *, title = 'Wikipedia'):
    """The Wikipedia search command."""
    embed = await Wikipedia.embed_search_result(language, title)
    await ctx.send(ctx.author.mention, embed=embed)

@wikipedia.error
async def wikipedia_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        embed = discord.Embed(
            title=':warning: Nie podano wersji językowej Wikipedii!',
            color=somsiad.COLOR
        )
        embed.set_footer(
            text=Wikipedia.FOOTER_TEXT,
            icon_url=Wikipedia.FOOTER_ICON_URL
        )

        await ctx.send(ctx.author.mention, embed=embed)
