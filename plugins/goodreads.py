# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from discord.ext import commands
import aiohttp
from somsiad_helper import *
from version import __version__
import xml.etree.ElementTree as ET


@client.command(aliases=['gr'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def goodreads(ctx, *args):
    '''Goodreads search. Search for the most popular books for the given query.'''
    em = discord.Embed(colour=brand_color)
    if len(args) == 0:
        em.add_field(name='goodreads',
                     value=f':warning: **Błąd**\nNie podano szukanego hasła!')
        await ctx.send(embed=em)
    else:
        query = ' '.join(args)
        url = 'https://www.goodreads.com/search/index.xml'
        params = {'q': query, 'key': conf['goodreads_key']}
        headers = {'User-Agent': 'Somsiad {}'.format(__version__)}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as r:
                if r.status == 200:
                    tree = ET.fromstring(await r.text())
                    node = tree.find('.//total-results')
                    if node.text == '0':
                        em.add_field(name='goodreads', value=':slight_frown: **Niepowodzenie**\n' +
                                     f'Nie znaleziono żadnego wyniku pasującego do hasła "{query}".',
                                     inline=False)
                        await ctx.send(embed=em)
                    else:
                        books = []
                        counter = 0
                        for elem in tree.findall('.//work'):
                            books.append({})
                            for work in elem.findall('*'):
                                if work.tag == 'id':
                                    books[counter]['book_id'] = work.text
                                if work.tag == 'ratings_count':
                                    books[counter]['ratings_count'] = work.text
                                if work.tag == 'average_rating':
                                    books[counter]['average_rating'] = work.text

                                for best_book in work.findall('*'):
                                    if best_book.tag == 'title':
                                        books[counter]['title'] = best_book.text
                                    if best_book.tag == 'image_url':
                                        books[counter]['image_url'] = best_book.text

                                    for author in best_book.findall('*'):
                                        if author.tag == 'name':
                                            books[counter]['author'] = author.text
                            counter += 1

                        template_url = 'https://www.goodreads.com/book/title?id='
                        main_url = template_url + books[0]['title']
                        main_url = main_url.replace(' ', '%20')
                        main_url = main_url.replace('(', '%28')
                        main_url = main_url.replace(')', '%29')
                        em.add_field(name='goodreads',
                                     value=f"**[{books[0]['title']}]({main_url})**\n" +
                                     f"**Autor:** {books[0]['author']}\n" +
                                     f"**Ocena:** {books[0]['average_rating']}/5\n**" +
                                     f"Liczba głosów:** {books[0]['ratings_count']}",
                                     inline=False)
                        em.set_thumbnail(url=books[0]['image_url'])
                        if len(books) > 1:
                            sec_results = []
                            for i in books[1:5]:
                                sec_url = template_url + i['title']
                                sec_url = sec_url.replace(' ', '%20')
                                sec_url = sec_url.replace('(', '%28')
                                sec_url = sec_url.replace(')', '%29')
                                sec_results.append(f"• [{i['title']}]({sec_url}) - {i['author']} " +
                                                   f"({i['average_rating']}/5)")
                                sec_results_str = '\n'.join(sec_results)
                            em.add_field(name='Pozostałe trafienia:', value=sec_results_str, inline=False)
                        await ctx.send(embed=em)
                else:
                    em.add_field(name='goodreads', value=':warning: **Błąd**\nNie można połączyć się z serwisem!',
                                 inline=False)
                    await ctx.send(embed=em)
