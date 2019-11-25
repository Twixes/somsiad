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
import discord
from core import somsiad
from configuration import configuration
from defusedxml import ElementTree


@somsiad.command(aliases=['gr', 'książka', 'ksiazka', 'buk', 'book', 'buch'])
@discord.ext.commands.cooldown(
    1,
    configuration['command_cooldown_per_user_in_seconds']
    if float(configuration['command_cooldown_per_user_in_seconds']) > 1.0 else 1.0
)
@discord.ext.commands.guild_only()
async def goodreads(ctx, *, query):
    """Goodreads search. Responds with for the most popular books matching the query."""
    FOOTER_TEXT = 'goodreads'
    FOOTER_ICON_URL = 'https://www.goodreads.com/favicon.ico'

    url = 'https://www.goodreads.com/search/index.xml'
    params = {
        'q': query,
        'key': configuration['goodreads_key']
    }
    headers = {'User-Agent': somsiad.USER_AGENT}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                tree = ElementTree.fromstring(await response.text())
                node = tree.find('.//total-results')
                if node.text == '0':
                    embed = discord.Embed(
                        title=f':slight_frown: Brak wyników dla zapytania "{query}"',
                        color=somsiad.COLOR
                    )
                else:
                    books = []
                    counter = 0
                    for element in tree.findall('.//work'):
                        books.append({})
                        for work in element.findall('*'):
                            if work.tag == 'id':
                                books[counter]['book_id'] = work.text
                            if work.tag == 'ratings_count':
                                books[counter]['ratings_count'] = work.text
                            if work.tag == 'average_rating':
                                books[counter]['average_rating'] = work.text

                            for best_book in work.findall('*'):
                                if best_book.tag == 'id':
                                    books[counter]['id'] = best_book.text
                                if best_book.tag == 'title':
                                    books[counter]['title'] = best_book.text
                                if best_book.tag == 'image_url':
                                    books[counter]['image_url'] = best_book.text

                                for author in best_book.findall('*'):
                                    if author.tag == 'name':
                                        books[counter]['author'] = author.text
                        counter += 1

                    template_url = 'https://www.goodreads.com/book/show/'
                    main_url = template_url + books[0]['id']
                    main_url = main_url.replace(' ', '%20').replace('(', '%28').replace(')', '%29')
                    embed = discord.Embed(title=f'{books[0]["title"]}', url=main_url, color=somsiad.COLOR)
                    embed.set_author(name=books[0]["author"])
                    embed.add_field(name='Ocena', value=f'{locale.str(float(books[0]["average_rating"]))}/5')
                    embed.add_field(name='Liczba głosów', value=books[0]["ratings_count"])
                    embed.set_thumbnail(url=books[0]['image_url'])
                    if len(books) > 1:
                        sec_results = []
                        for i in books[1:4]:
                            sec_url = template_url + i['id']
                            sec_results.append(
                                f'• [{i["title"]}]({sec_url}) – {i["author"]} – '
                                f'{locale.str(float(i["average_rating"]))}/5'
                            )
                            sec_results_str = '\n'.join(sec_results)
                        embed.add_field(name='Pozostałe trafienia', value=sec_results_str, inline=False)
            else:
                embed = discord.Embed(
                    title=':warning: Nie można połączyć się z serwisem!', color=somsiad.COLOR)

    embed.set_footer(text=FOOTER_TEXT, icon_url=FOOTER_ICON_URL)
    await ctx.send(ctx.author.mention, embed=embed)


@goodreads.error
async def goodreads_error(ctx, error):
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        embed = discord.Embed(
            title=':warning: Nie podano szukanego hasła!',
            color=somsiad.COLOR
        )
        await ctx.send(ctx.author.mention, embed=embed)
