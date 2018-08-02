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
import wikipedia
import logging
from somsiad_helper import *

async def wiki_search(ctx, args, lang):
    '''Returns the closest matching article from Wikipedia'''
    if len(args) == 0:
        await ctx.send(':warning: Musisz podać parametr wyszukiwania, {}.'.format(ctx.author.mention))
    else:
        wikipedia.set_lang(lang)
        query = ' '.join(args)
        search_results = wikipedia.search(query)
        if len(search_results) < 1:
            await ctx.send(':warning: Nie znalazłem żadnego wyniku pasującego do twojego zapytania, {}.'.format(
                ctx.author.mention))
        else:
            try:
                page = wikipedia.page(search_results[0], auto_suggest = True, redirect = True)
                em = discord.Embed(title='Wikipedia', colour=0xffffff)
                # Fetch image from Wikipedia's infobox for thumbnail
                thumb_api_url = ('http://en.wikipedia.org/w/api.php?action=query&titles={}'.format(page.title) +
                    '&prop=pageimages&format=json&pithumbsize=500')
                async with aiohttp.ClientSession() as session:
                    async with session.get(thumb_api_url) as r:
                        if r.status == 200:
                            res = await r.json()
                            try:
                                thumb_url = list(res['query']['pages'].values())
                                thumb_url = thumb_url[0]['thumbnail']['source']
                                em.set_thumbnail(url=thumb_url)
                            except:
                                pass    # If error occurs, don't include the thumbnail
                em.add_field(name='Pojęcie: ', value=page.title, inline=False)
                # wikipedia.py summary function detects sentences using dots
                # Allow abbreviations so that sentences are not unnecessarily cut in half
                i = 1   # Initial value for sentence counter
                with open(os.path.join(bot_dir, 'data', 'wiki_abbrevations.txt')) as f:
                    abbreviations = tuple([line.strip() for line in f.readlines()])
                while True:
                    summary = wikipedia.summary(page.title, sentences=i)
                    if summary.endswith(abbreviations):
                        i += 1  # Sentence counter
                    else:
                        break
                # limit to 800 chars to prevent hitting discord message length limit of 2000 chars
                if len(summary) > 800:
                    summary = summary[:800] + '...' # Reduce lenght of output
                em.add_field(name='Definicja: ', value=summary, inline=False)
                em.add_field(name='Link: ', value=page.url, inline=False)
                await ctx.send(embed=em)
            # Return possible options if no article matching user query was found
            except wikipedia.exceptions.HTTPTimeoutError as e:
                await ctx.send('{} '.format(ctx.author.mention) +
                    ':warning: Wikipedia: Przekroczono limit czasu połączenia.')
            except wikipedia.exceptions.DisambiguationError as e:
                option_str = ''
                for option in e.options:
                    option_str += '- ' + option + '\n'
                await ctx.send('{} '.format(ctx.author.mention) + '\nTermin *{}* może dotyczyć:\n'.format(query) +
                    option_str)
            except Exception as e:
                logging.error(e)

@client.command(aliases=['w', 'wikipedia'])
@commands.cooldown(1, conf['user_command_cooldown'], commands.BucketType.user)
@commands.guild_only()
async def wiki(ctx, *args):
    '''Polish version of wiki_search'''
    lang = 'pl'
    await wiki_search(ctx, args, lang)

@client.command(aliases=['wen', 'wikipediaen'])
@commands.cooldown(1, conf['user_command_cooldown'], commands.BucketType.user)
@commands.guild_only()
async def wikien(ctx, *args):
    '''English version of wiki_search'''
    lang = 'en'
    await wiki_search(ctx, args, lang)
