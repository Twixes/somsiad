import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
import aiohttp
from somsiad_helper import *


@client.command(aliases=['g'])
@commands.cooldown(1, 1, commands.BucketType.user)
@commands.guild_only()
async def g_search(ctx, *args):
    """Returns first matching result from Google. 
    Uses DuckDuckGo Instant Answer API - https://duckduckgo.com/api"""
    if len(args) == 0:
        await ctx.send(':warning: Musisz podać parametr wyszukiwania, {}.'.format(
            ctx.author.mention))
    else:
        query = "+".join(args)
        url = "https://api.duckduckgo.com/?q=!fl {}&t=somsiad_discord_bot&format=json".format(
            query)
        headers = {'User-Agent': 'python-duckduckgo'} # pass headers to allow redirection
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as r:    
                if r.status == 200:
                    await ctx.send('{}, '.format(ctx.author.mention) +
                        "\n :globe_with_meridians: " + str(r.url) +
                        "\n`Wyniki za pośrednictwem DuckDuckGo` :duck:")
                else:
                    await ctx.send(":warning: " +
                        "Nie można połączyć się z serwisem DuckDuckGo, " +
                        "{}".format(ctx.author.mention))
