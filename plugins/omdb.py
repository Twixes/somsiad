# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
import aiohttp
import re
from somsiad import somsiad


def add_non_empty(embed, res, key, name, is_inline):
    if key in res:
        if res[key] != 'N/A':
            embed.add_field(name=name, value=res[key], inline=is_inline)


@somsiad.client.command(aliases=['film', 'movie', 'imdb'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.default
)
@discord.ext.commands.guild_only()
async def omdb(ctx, *args):
    """OMDb search. Responds with the most popular movies and TV series matching the query."""
    FOOTER_TEXT = '📷 OMDb API (CC BY-NC 4.0)'
    if not args or (len(args) == 1 and args[0].lower() in ('tv', 'm')):
            embed = discord.Embed(
                title=':warning: Błąd', description='Nie podano szukanego hasła!', color=somsiad.color
            )
            embed.set_footer(text=FOOTER_TEXT)
            await ctx.send(embed=embed)
    else:
        if re.match(r's\d\de\d\d', args[0].lower()):
            if len(args) == 1:
                embed = discord.Embed(
                    title=':warning: Błąd', description='Nie podano szukanego hasła!', color=somsiad.color
                )
                embed.set_footer(text=FOOTER_TEXT)
                await ctx.send(embed=embed)
                return
            query = ' '.join(args[1:])
            series_season_episode = args[0].lower()
            series_season_episode = series_season_episode.lstrip('s')
            series_season, series_episode = series_season_episode.split('e')
            params = {
                'apikey': somsiad.conf['omdb_key'], 't': query, 'Season': series_season, 'Episode': series_episode
            }
        elif args[0].lower() == 'm':
            query = ' '.join(args[1:])
            params = {'apikey': somsiad.conf['omdb_key'], 't': query, 'type': 'movie'}
        elif args[0].lower() == 'tv':
            query = ' '.join(args[1:])
            params = {'apikey': somsiad.conf['omdb_key'], 't': query, 'type': 'series'}
        else:
            query = ' '.join(args)
            params = {'apikey': somsiad.conf['omdb_key'], 't': query}

        headers = {'User-Agent': somsiad.user_agent}
        url = 'http://www.omdbapi.com/'
        basic_info = ['Rated', 'Runtime', 'Released', 'Country']

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as r:
                if r.status == 200:
                    res = await r.json()
                    if res['Response'] == 'True':
                        if res['Type'] in ('movie', 'series', 'episode'):
                            if 'Year' in res:
                                if res['Year'] != 'N/A':
                                    title = f'{res["Title"]} ({res["Year"]})'
                                else:
                                    title = f'{res["Title"]}'

                            mess_part1 = []
                            for i in basic_info:
                                if i in res:
                                    if res[i] != 'N/A':
                                        mess_part1.append(f'{res[i]}')
                            mess_part1 = ' | '.join(mess_part1)

                            if 'imdbID' in res:
                                main_url = 'https://www.imdb.com/title/' + res['imdbID']
                                embed = discord.Embed(
                                    title=title, url=main_url, description=mess_part1, color=somsiad.color
                                )
                            else:
                                embed = discord.Embed(title=title, description=mess_part1, color=somsiad.color)

                            if 'seriesID' in res:
                                if 'seriesID' != 'N/A':
                                    series_url = 'https://www.imdb.com/title/' + res['seriesID']
                                    embed.add_field(
                                        name='Strona serialu w serwisie IMDb', value=series_url, inline=False
                                    )

                            add_non_empty(embed, res, 'Genre', 'Gatunek', True)
                            add_non_empty(embed, res, 'totalSeasons', 'Liczba sezonów', True)
                            add_non_empty(embed, res, 'Season', 'Sezon', True)
                            add_non_empty(embed, res, 'Episode', 'Odcinek', True)

                            if 'imdbRating' in res:
                                if res['imdbRating'] != 'N/A':
                                    msg = res['imdbRating'] + '/10'
                                    if 'imdbVotes' in res:
                                        if res['imdbVotes'] != 'N/A':
                                            msg += f' *({res["imdbVotes"]})*'
                                    embed.add_field(name='IMDb', value=msg, inline=True)

                            add_non_empty(embed, res, 'Metascore', 'Metascore', True)

                            if 'Ratings' in res:
                                for i in res['Ratings']:
                                    if i['Source'] == 'Rotten Tomatoes':
                                        embed.add_field(name='Rotten Tomatoes', value=i['Value'], inline=True)

                            add_non_empty(embed, res, 'Plot', 'Fabuła', False)

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

                            add_non_empty(embed, res, 'Actors', 'Aktorzy', False)
                            add_non_empty(embed, res, 'Awards', 'Nagrody', False)

                            if 'BoxOffice' in res:
                                if res['BoxOffice'] != 'N/A':
                                    if res['BoxOffice'].startswith('&pound;'):
                                        box_office = res['BoxOffice'].lstrip('&pound;')
                                        box_office = '£' + box_office
                                    else:
                                        box_office = res['BoxOffice']
                                    embed.add_field(name='Box Office', value=box_office, inline=True)

                            add_non_empty(embed, res, 'Production', 'Produkcja', True)

                        if 'Poster' in res:
                            if res['Poster'] != 'N/A':
                                embed.set_thumbnail(url=res['Poster'])
                        embed.set_footer(text=FOOTER_TEXT)
                        await ctx.send(embed=embed)
                    elif res['Response'] == 'False':
                        embed = discord.Embed(
                            title=':slight_frown: Niepowodzenie',
                            description=f'Nie znaleziono żadnego wyniku pasującego do zapytania "{query}".',
                            color=somsiad.color
                        )
                        embed.set_footer(text=FOOTER_TEXT)
                        await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title=':warning: Błąd', description='Nie można połączyć się z serwisem.', color=somsiad.color
                    )
                    embed.set_footer(text=FOOTER_TEXT)
                    await ctx.send(embed=embed)
