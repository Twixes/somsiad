# Copyright 2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Optional
import datetime as dt
import discord
from discord.ext import commands
from core import Help, cooldown
from configuration import configuration
from utilities import word_number_form, calculate_age, human_amount_of_time


class TMDb(commands.Cog):
    GROUP = Help.Command(
        'tmdb', (),
        'Komendy związane z informacjami o produkcjach i ludziach ze światów kina i telewizji. '
        'Użyj <?zapytania> zamiast <?podkomendy>, by otrzymać najlepiej pasujący film/serial/osobę.'
    )
    COMMANDS = (
        Help.Command(('film', 'kino'), 'zapytanie', 'Zwraca najlepiej pasujący do <zapytania> film.'),
        Help.Command(
            ('serial', 'seria', 'telewizja', 'tv'), 'zapytanie', 'Zwraca najlepiej pasujący do <zapytania> serial.'
        ),
        Help.Command('osoba', 'zapytanie', 'Zwraca najlepiej pasującą do <zapytania> osobę.')
    )
    HELP = Help(
        COMMANDS, '🎬', group=GROUP, footer_text='TMDb',
        footer_icon_url='https://www.themoviedb.org/assets/2/v4/logos/'
        '208x226-stacked-green-9484383bd9853615c113f020def5cbe27f6d08a84ff834f41371f223ebad4a3c.png'
    )
    PROFESSIONS = {
        'Acting': '🎭', 'Art': '🎨', 'Camera': '🎥', 'Costume': '👗', 'Creator': '🧠', 'Crew': '🔧', 'Directing': '🎬',
        'Editing': '✂️', 'Lighting': '💡', 'Production': '📈', 'Sound': '🎙', 'Visual Effects': '🎇', 'Writing': '🖋'
    }

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_result_and_generate_embed(self, query: str, media_type: Optional[str] = None) -> discord.Embed:
        params = {'api_key': configuration['tmdb_key'], 'query': query, 'language': 'pl-PL', 'region': 'PL'}
        search_url = f'https://api.themoviedb.org/3/search/{media_type or "multi"}'
        async with self.bot.session.get(search_url, headers=self.bot.HEADERS, params=params) as request:
            if request.status != 200:
                embed = self.bot.generate_embed('⚠️', f'Nie udało się połączyć z serwisem')
            else:
                response = await request.json()
                if not response['total_results']:
                    embed = self.bot.generate_embed('🙁', f'Brak wyników dla zapytania "{query}"')
                else:
                    search_result = response['results'][0]
                    media_type = media_type or search_result['media_type']
                    async with self.bot.session.get(
                        f'https://api.themoviedb.org/3/{media_type}/{search_result["id"]}',
                        headers=self.bot.HEADERS, params=params
                    ) as request:
                        if request.status != 200:
                            embed = self.bot.generate_embed('⚠️', f'Nie udało się połączyć z serwisem')
                        else:
                            full_result = await request.json()
                            full_result.update(search_result)
                            if media_type == 'person':
                                embed = self.generate_person_embed(full_result)
                            elif media_type == 'movie':
                                embed = self.generate_movie_embed(full_result)
                            elif media_type == 'tv':
                                embed = self.generate_tv_embed(full_result)
        embed.set_footer(
            text='TMDb',
            icon_url='https://www.themoviedb.org/assets/2/v4/logos/'
            '208x226-stacked-green-9484383bd9853615c113f020def5cbe27f6d08a84ff834f41371f223ebad4a3c.png'
        )
        return embed

    def generate_person_embed(self, result: dict) -> discord.Embed:
        is_female = result['gender'] == 1
        today = dt.date.today()
        birth_date = dt.datetime.strptime(result['birthday'], '%Y-%m-%d').date() if result['birthday'] else None
        death_date = dt.datetime.strptime(result['deathday'], '%Y-%m-%d').date() if result['deathday'] else None
        if birth_date is not None and (birth_date.month, birth_date.day) == (today.month, today.day):
            emoji = '🎂'
        else:
            emoji = self.PROFESSIONS.get(result['known_for_department']) or ('👩' if is_female else '👨')
        embed = self.bot.generate_embed(emoji, result['name'], url=f'https://www.themoviedb.org/person/{result["id"]}')
        embed.add_field(name='Data urodzenia', value=birth_date.strftime('%-d %B %Y'))
        if death_date is not None:
            embed.add_field(name='Data śmierci', value=death_date.strftime('%-d %B %Y'))
        embed.add_field(name='Wiek', value=calculate_age(birth_date, death_date))
        known_for_parts = (
            f'[📺 {production["name"]} ({production["first_air_date"][:4]})]'
            f'(https://www.themoviedb.org/tv/{production["id"]})'
            if production['media_type'] == 'tv' else
            f'[🎞 {production["title"]} ({production["release_date"][:4]})]'
            f'(https://www.themoviedb.org/movie/{production["id"]})'
            for production in result['known_for']
        )
        if result['biography']:
            embed.add_field(name='Biografia', value=result['biography'], inline=False)
        embed.add_field(
            name='Znana z' if is_female else 'Znany z', value='\n'.join(known_for_parts), inline=False
        )
        if result['profile_path']:
            embed.set_thumbnail(url=f'https://image.tmdb.org/t/p/w342{result["profile_path"]}')
        if result['known_for'] and result['known_for'][0].get('backdrop_path'):
            embed.set_image(url=f'https://image.tmdb.org/t/p/w780{result["known_for"][0]["backdrop_path"]}')
        return embed

    def generate_movie_embed(self, result: dict) -> discord.Embed:
        release_date = dt.datetime.strptime(result['release_date'], '%Y-%m-%d').date()
        embed = self.bot.generate_embed(
            '🎞', f'{result["title"]} ({result["release_date"][:4]})', result.get('tagline'),
            url=f'https://www.themoviedb.org/movie/{result["id"]}'
        )
        if result.get('original_title') != result['title']:
            embed.add_field(name='Tytuł oryginalny', value=result['original_title'], inline=False)
        embed.add_field(name='Średnia ocen', value=f'{result["vote_average"]:n} / 10')
        embed.add_field(name='Głosów', value=f'{result["vote_count"]:n}')
        embed.add_field(name='Data premiery', value=release_date.strftime('%-d %B %Y'))
        if result['runtime']:
            embed.add_field(name='Długość', value=human_amount_of_time(result['runtime'] * 60))
        if result['budget']:
            embed.add_field(name='Budżet', value=f'${result["budget"]:n}')
        if result['revenue']:
            embed.add_field(name='Przychody', value=f'${result["revenue"]:n}')
        if result['genres']:
            genre_parts = (
                f'[{genre["name"]}](https://www.themoviedb.org/genre/{genre["id"]})' for genre in result['genres']
            )
            embed.add_field(name='Gatunki' if len(result['genres']) > 1 else 'Gatunek', value=' / '.join((genre_parts)))
        if result['overview']:
            embed.add_field(name='Opis', value=result['overview'], inline=False)
        if result.get('poster_path'):
            embed.set_thumbnail(url=f'https://image.tmdb.org/t/p/w342{result["poster_path"]}')
        if result.get('backdrop_path'):
            embed.set_image(url=f'https://image.tmdb.org/t/p/w780{result["backdrop_path"]}')
        return embed

    def generate_tv_embed(self, result: dict) -> discord.Embed:
        first_air_date = dt.datetime.strptime(result['first_air_date'], '%Y-%m-%d').date()
        last_air_date = dt.datetime.strptime(result['last_air_date'], '%Y-%m-%d').date()
        air_years_range = str(first_air_date.year)
        if result['in_production']:
            air_years_range += '–'
        elif first_air_date.year != last_air_date.year:
            air_years_range += f'–{last_air_date.year}'
        embed = self.bot.generate_embed(
            '📺', f'{result["name"]} ({air_years_range})', url=f'https://www.themoviedb.org/tv/{result["id"]}'
        )
        if result.get('original_name') != result['name']:
            embed.add_field(name='Tytuł oryginalny', value=result['original_name'], inline=False)
        embed.add_field(name='Średnia ocen', value=f'{result["vote_average"]:n} / 10')
        embed.add_field(name='Głosów', value=f'{result["vote_count"]:n}')
        embed.add_field(
            name='Data premiery pierwszego odcinka', value=first_air_date.strftime('%-d %B %Y'), inline=False
        )
        if last_air_date != first_air_date:
            embed.add_field(
                name=f'Data premiery ostatniego odcinka', value=last_air_date.strftime('%-d %B %Y'), inline=False
            )
        if result['networks']:
            network_parts = (
                f'[{network["name"]}](https://www.themoviedb.org/network/{network["id"]})'
                for network in result['networks']
            )
            embed.add_field(name='Sieci' if len(result['networks']) > 1 else 'Sieć', value=', '.join((network_parts)))
        if result['created_by']:
            author_parts = (
                f'[{author["name"]}](https://www.themoviedb.org/person/{author["id"]})'
                for author in result['created_by']
            )
            if len(result['created_by']) > 1:
                are_all_authors_female = all((author.get('gender') == 1 for author in result['created_by']))
                created_by_field_name = 'Autorki' if are_all_authors_female else 'Autorzy'
            else:
                created_by_field_name = 'Autorka' if result['created_by'][0].get('gender') == 1 else 'Autor'
            embed.add_field(name=created_by_field_name, value=', '.join(author_parts))
        if result['genres']:
            genre_parts = (
                f'[{genre["name"]}](https://www.themoviedb.org/genre/{genre["id"]})' for genre in result['genres']
            )
            embed.add_field(name='Gatunki' if len(result['genres']) > 1 else 'Gatunek', value=' / '.join((genre_parts)))
        season_parts = []
        for season in result['seasons']:
            if season['season_number'] > 0:
                if season["air_date"]:
                    air_date_presentation = dt.datetime.strptime(season['air_date'], '%Y-%m-%d').strftime('%-d %B %Y')
                else:
                    air_date_presentation = 'TBD'
                season_parts.append(
                    f'[{season["season_number"]}. '
                    f'{word_number_form(season["episode_count"] or "?", "odcinek", "odcinki", "odcinków")} '
                    f'(premiera {air_date_presentation})]'
                    f'(https://www.themoviedb.org/tv/{result["id"]}/season/{season["season_number"]})'
                )
        embed.add_field(name='Sezony', value='\n'.join(season_parts), inline=False)
        if result['overview']:
            embed.add_field(name='Opis', value=result['overview'], inline=False)
        if result.get('poster_path'):
            embed.set_thumbnail(url=f'https://image.tmdb.org/t/p/w342{result["poster_path"]}')
        if result.get('backdrop_path'):
            embed.set_image(url=f'https://image.tmdb.org/t/p/w780{result["backdrop_path"]}')
        return embed

    @commands.group(invoke_without_command=True)
    @cooldown()
    async def tmdb(self, ctx, *, query):
        """Responds with the most popular movie/series/person matching the query."""
        async with ctx.typing():
            embed = await self.fetch_result_and_generate_embed(query)
            await self.bot.send(ctx, embed=embed)

    @tmdb.error
    async def tmdb_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await self.bot.send(ctx, embeds=self.HELP.embeds)

    @tmdb.command(aliases=['film', 'kino'])
    @cooldown()
    async def movie(self, ctx, *, query):
        """Responds with the most popular movie matching the query."""
        async with ctx.typing():
            embed = await self.fetch_result_and_generate_embed(query, 'movie')
            await self.bot.send(ctx, embed=embed)

    @commands.command(aliases=['movie', 'film', 'kino'])
    @cooldown()
    async def movie_unbound(self, ctx, *, query):
        """Responds with the most popular movie matching the query."""
        await ctx.invoke(self.movie, query=query)

    @tmdb.command(aliases=['serial', 'seria', 'telewizja'])
    @cooldown()
    async def tv(self, ctx, *, query):
        """Responds with the most popular TV series matching the query."""
        async with ctx.typing():
            embed = await self.fetch_result_and_generate_embed(query, 'tv')
            await self.bot.send(ctx, embed=embed)

    @commands.command(aliases=['tv', 'serial', 'seria', 'telewizja'])
    @cooldown()
    async def tv_unbound(self, ctx, *, query):
        """Responds with the most popular TV series matching the query."""
        await ctx.invoke(self.tv, query=query)

    @tmdb.command(aliases=['osoba'])
    @cooldown()
    async def person(self, ctx, *, query):
        """Responds with the most popular person matching the query."""
        async with ctx.typing():
            embed = await self.fetch_result_and_generate_embed(query, 'person')
            await self.bot.send(ctx, embed=embed)

    @commands.command(aliases=['person', 'osoba'])
    @cooldown()
    async def person_unbound(self, ctx, *, query):
        """Responds with the most popular person matching the query."""
        await ctx.invoke(self.person, query=query)


def setup(bot: commands.Bot):
    bot.add_cog(TMDb(bot))
