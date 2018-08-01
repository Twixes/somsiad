import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
import aiohttp
import re
from somsiad_helper import *


@client.command(aliases=['u', 'urban'])
@commands.cooldown(1, conf['cooldown'], commands.BucketType.user)
@commands.guild_only()
async def urban_dict(ctx, *args):
    """Returns word definitions from Urban Dictionary"""
    if len(args) == 0:
        await ctx.send(':warning: Musisz podać parametr wyszukiwania, {}.'.format(
            ctx.author.mention))
    else:
        query = "+".join(args)
        url = "https://api.urbandictionary.com/v0/define?term={}".format(query)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status == 200:
                    resp = await r.json()
                    bra_pat = re.compile(r'[\[\]]')
                    top_def = resp['list'][0]   # Get top definition
                    word = top_def['word']
                    definition = top_def['definition']
                    definition = bra_pat.sub(r'', definition)
                    if len(definition) > 500:
                        definition = definition[:500] + "..." # Reduce output lenght
                    link = top_def['permalink']
                    example = top_def['example']
                    example = bra_pat.sub(r'', example)
                    if len(example) > 400:
                        example = example[:400] + "..." # Reduce output lenght
                    t_up = top_def['thumbs_up']
                    t_down = top_def['thumbs_down']
                    
                    em = discord.Embed(title='Urban Dictionary', colour=0xefff00)
                    em.add_field(name="Słowo:", value=word, inline=False)
                    em.add_field(name="Definicja:", value=definition, inline=False)
                    em.add_field(name="Przykład(y):", value=example, inline=False)
                    em.add_field(name="Głosy:", value=":thumbsup: " + str(t_up) + " | " + 
                        ":thumbsdown: " + str(t_down))
                    em.add_field(name="Link:", value=link, inline=False)
                    await ctx.send(embed=em)
                else:
                    await ctx.send(":warning: " +
                        "Nie można połączyć się z serwisem Urban Dictionary, " +
                        "{}".format(ctx.author.mention))
