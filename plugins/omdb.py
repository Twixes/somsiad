# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import locale
import aiohttp
import re
import discord
from core import somsiad
from utilities import TextFormatter
from configuration import configuration


class OMDb:
    """Handles OMDb API integration."""
    FOOTER_TEXT = 'OMDb (CC BY-NC 4.0)'

    @staticmethod
    def smart_add_info_field_to_embed(embed: discord.Embed, name: str, res: list, key: str, *, inline: bool = True):
        if key in res:
            if res[key] != 'N/A':
                embed.add_field(name=name, value=res[key], inline=inline)


@somsiad.command(aliases=['film'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.default
)
@discord.ext.commands.guild_only()
async def omdb(ctx, *args):
    """OMDb search. Responds with the most popular movies and TV series matching the query."""
    if (
            not args or (
                len(args) == 1 and (
                    args[0].lower() in ('film', 'tv', 'serial') or
                    re.match(r's\d\de\d\d', args[0].lower())
                )
            ) or (
                len(args) == 2 and
                args[0].lower() in ('tv', 'serial') and
                re.match(r's\d\de\d\d', args[1].lower())
            )
    ):
        embed = discord.Embed(
            title=':warning: Nie podano tytułu szukanej produkcji!', color=somsiad.COLOR
        )
    else:
        if re.match(r's\d\de\d\d', args[1].lower() if args[0].lower() in ('tv', 'serial') else args[0].lower()):
            if args[0].lower() in ('tv', 'serial'):
                args = args[1:]

            if len(args) == (2 if args[0].lower() in ('tv', 'serial') else 1):
                embed = discord.Embed(
                    title=':warning: Nie podano tytułu szukanej produkcji!', color=somsiad.COLOR
                )
            else:
                query = ' '.join(args[1:])
                series_season_episode = args[0].lower()
                series_season_episode = series_season_episode.lstrip('s')
                series_season, series_episode = series_season_episode.split('e')
                params = {
                    'apikey': configuration['omdb_key'], 't': query, 'Season': series_season, 'Episode': series_episode
                }
        elif args[0].lower() == 'film':
            query = ' '.join(args[1:])
            params = {'apikey': configuration['omdb_key'], 't': query, 'type': 'movie'}
        elif args[0].lower() in ('tv', 'serial'):
            query = ' '.join(args[1:])
            params = {'apikey': configuration['omdb_key'], 't': query, 'type': 'series'}
        else:
            query = ' '.join(args)
            params = {'apikey': configuration['omdb_key'], 't': query}

        headers = {'User-Agent': somsiad.USER_AGENT}
        URL = 'http://www.omdbapi.com/'
        BASIC_INFO = ['Rated', 'Runtime', 'Released', 'Country']

        async with aiohttp.ClientSession() as session:
            async with session.get(URL, headers=headers, params=params) as r:
                if r.status == 200:
                    res = await r.json()
                    if res['Response'] == 'True':
                        if res['Type'] in ('movie', 'series', 'episode'):
                            if 'Year' in res:
                                if res['Year'] != 'N/A':
                                    title = f'{res["Title"]} ({res["Year"]})'
                                else:
                                    title = res['Title']

                            mess_part1 = []
                            for i in BASIC_INFO:
                                if i in res:
                                    if res[i] != 'N/A':
                                        mess_part1.append(f'{res[i]}')
                            mess_part1 = ' | '.join(mess_part1)

                            if 'imdbID' in res:
                                main_url = 'https://www.imdb.com/title/' + res['imdbID']
                                embed = discord.Embed(
                                    title=title, url=main_url, description=mess_part1, color=somsiad.COLOR
                                )
                            else:
                                embed = discord.Embed(title=title, description=mess_part1, color=somsiad.COLOR)

                            OMDb.smart_add_info_field_to_embed(embed, 'Gatunek', res, 'Genre')

                            if 'imdbRating' in res:
                                if res['imdbRating'] != 'N/A':
                                    imdb_rating = locale.str(float(res['imdbRating']))
                                    imdb_votes = float(res["imdbVotes"].replace(',', ''))
                                    imdb_votes_string = (
                                        TextFormatter.word_number_variant(imdb_votes, 'głos', 'głosy', 'głosów')
                                    )
                                    if 'imdbVotes' in res:
                                        if res['imdbVotes'] != 'N/A':
                                            msg = f'{imdb_rating}/10 ({imdb_votes_string})'
                                    embed.add_field(name='Ocena na IMDb', value=msg)

                            OMDb.smart_add_info_field_to_embed(embed, 'Liczba sezonów', res, 'totalSeasons')

                            if 'Ratings' in res:
                                for i in res['Ratings']:
                                    if i['Source'] == 'Rotten Tomatoes':
                                        embed.add_field(
                                            name='Ocena na Rotten Tomatoes',
                                            value=i['Value']
                                        )

                            OMDb.smart_add_info_field_to_embed(embed, 'Metascore', res, 'Metascore')
                            OMDb.smart_add_info_field_to_embed(embed, 'Fabuła', res, 'Plot', inline=False)
                            OMDb.smart_add_info_field_to_embed(embed, 'Produkcja', res, 'Production')

                            if res['Type'] == 'movie':
                                if 'Director' in res:
                                    if res['Director'] != 'N/A':
                                        embed.add_field(name='Reżyseria', value=res['Director'], inline=False)
                                if 'Writer' in res:
                                    if res['Writer'] != 'N/A':
                                        embed.add_field(name='Scenariusz', value=res['Writer'], inline=False)

                            elif res['Type'] == 'series':
                                if 'Writer' in res:
                                    if res['Writer'] != 'N/A':
                                        embed.add_field(name='Twórcy', value=res['Writer'], inline=False)

                            OMDb.smart_add_info_field_to_embed(embed, 'Występują', res, 'Actors', inline=False)
                            OMDb.smart_add_info_field_to_embed(embed, 'Nagrody', res, 'Awards', inline=False)

                            if 'BoxOffice' in res:
                                if res['BoxOffice'] != 'N/A':
                                    if res['BoxOffice'].startswith('&pound;'):
                                        box_office = res['BoxOffice'].lstrip('&pound;')
                                        box_office = '£' + box_office
                                    else:
                                        box_office = res['BoxOffice']
                                    embed.add_field(name='Box office', value=box_office)

                        if 'Poster' in res:
                            if res['Poster'] != 'N/A':
                                embed.set_thumbnail(url=res['Poster'])
                    elif res['Response'] == 'False':
                        embed = discord.Embed(
                            title=f':slight_frown: Brak wyników dla tytułu "{query}"',
                            color=somsiad.COLOR
                        )
                else:
                    embed = discord.Embed(
                        title=':warning: Nie udało się połączyć z OMDb!',
                        color=somsiad.COLOR
                    )
    embed.set_footer(text=OMDb.FOOTER_TEXT)
    await ctx.send(ctx.author.mention, embed=embed)
