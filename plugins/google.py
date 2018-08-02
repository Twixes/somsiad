# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from discord.ext import commands
import aiohttp
from somsiad_helper import *

@client.command(aliases=['g', 'gugiel'])
@commands.cooldown(1, conf['user_command_cooldown'], commands.BucketType.user)
@commands.guild_only()
async def google(ctx, *args):
    '''Returns first matching result from Google. Uses DuckDuckGo Instant Answer API - https://duckduckgo.com/api'''
    if len(args) == 0:
        await ctx.send(':warning: Musisz podać parametr wyszukiwania, {}.'.format(ctx.author.mention))
    else:
        query = '+'.join(args)
        url = 'https://api.duckduckgo.com/?q=!fl {}&t=somsiad_discord_bot&format=json'.format(query)
        headers = {'User-Agent': 'python-duckduckgo'} # pass headers to allow redirection
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as r:
                if r.status == 200:
                    await ctx.send('{} '.format(ctx.author.mention) +
                        '\n :globe_with_meridians: ' + str(r.url) +
                        '\n`Wyniki za pośrednictwem DuckDuckGo` :duck:')
                else:
                    await ctx.send(':warning: Nie można połączyć się z DuckDuckGo, {}'.format(ctx.author.mention))
