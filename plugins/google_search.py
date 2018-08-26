# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from googleapiclient.discovery import build
from somsiad import somsiad


class GoogleCSE:
    _google_cse = None
    _google_cse_id = None

    class SearchResultRetrievalFailure(Exception):
        """Raised when search results could not be retrieved from Google."""
        pass

    def __init__(self, developer_key, google_cse_id):
        self._google_cse = build('customsearch', 'v1', developerKey=developer_key)
        self._google_cse_id = google_cse_id

    def search(self, query, language, number_of_results=1, safe='active', search_type=None):
        """Returns first {number_of_results} result(s) from Google."""
        try:
            results = self._google_cse.cse().list(
                q=query,
                cx=self._google_cse_id,
                hl=language,
                num=number_of_results,
                safe=safe,
                searchType=search_type
            ).execute()

            if int(results['searchInformation']['totalResults']) == 0:
                return []
            else:
                return results['items']
        except self.SearchResultRetrievalFailure:
            somsiad.logger.warning('Could not retrieve search results from Google!')
            return None


google_cse = GoogleCSE(somsiad.conf['google_key'], somsiad.conf['google_custom_search_engine_id'])


@somsiad.client.command(aliases=['g', 'gugiel'])
@discord.ext.commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], discord.ext.commands.BucketType.user)
@discord.ext.commands.guild_only()
async def google(ctx, *args):
    """Returns first matching website from Google using the provided Custom Search Engine."""
    FOOTER_TEXT = 'Google'
    FOOTER_ICON_URL = 'https://www.google.com/favicon.ico'

    if not args:
        embed = discord.Embed(
            title=':warning: Błąd',
            description='Nie podano szukanego hasła!',
            color=somsiad.color
        )
    else:
        query = ' '.join(args)
        results = google_cse.search(query, 'pl')
        if results is None:
            embed = discord.Embed(
                title=':warning: Błąd',
                description=f'Nie udało się połączyć z serwerem wyszukiwania.',
                color=somsiad.color
            )
        elif results == []:
            embed = discord.Embed(
                title=':slight_frown: Niepowodzenie',
                description=f'Brak wyników dla zapytania "{query}".',
                color=somsiad.color
            )
        else:
            result = results[0]
            site_protocol = result['link'].split('://')[0]
            embed = discord.Embed(
                title=result['title'],
                url=result['link'],
                description=result['snippet'],
                color=somsiad.color
            )
            embed.set_author(
                name=result['displayLink'],
                url=f'{site_protocol}://{result["displayLink"]}'
            )
            embed.set_image(
                url=result['pagemap']['cse_image'][0]['src']
            )

    embed.set_footer(text=FOOTER_TEXT, icon_url=FOOTER_ICON_URL)
    await ctx.send(ctx.author.mention, embed=embed)


@somsiad.client.command(aliases=['googleimage', 'gi', 'i'])
@discord.ext.commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], discord.ext.commands.BucketType.user)
@discord.ext.commands.guild_only()
async def google_image(ctx, *args):
    """Returns first matching image from Google using the provided Custom Search Engine."""
    FOOTER_TEXT = 'Google'
    FOOTER_ICON_URL = 'https://www.google.com/favicon.ico'

    if not args:
        embed = discord.Embed(
            title=':warning: Błąd',
            description='Nie podano szukanego hasła!',
            color=somsiad.color
        )
    else:
        query = ' '.join(args)
        results = google_cse.search(query, 'pl', search_type='image')
        if results == None:
            embed = discord.Embed(
                title=':warning: Błąd',
                description=f'Nie udało się połączyć z serwerem wyszukiwania.',
                color=somsiad.color
            )
        elif results == []:
            embed = discord.Embed(
                title=':slight_frown: Niepowodzenie',
                description=f'Brak wyników dla zapytania "{query}".',
                color=somsiad.color
            )
        else:
            result = results[0]
            site_protocol = result['link'].split('://')[0]
            embed = discord.Embed(
                title=result['title'],
                url=result['image']['contextLink'],
                color=somsiad.color
            )
            embed.set_author(
                name=result['displayLink'],
                url=f'{site_protocol}://{result["displayLink"]}'
            )
            embed.set_image(
                url=result['link']
            )

    embed.set_footer(text=FOOTER_TEXT, icon_url=FOOTER_ICON_URL)
    await ctx.send(ctx.author.mention, embed=embed)
