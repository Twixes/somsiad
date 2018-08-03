# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from discord.ext import commands
import random
import os
from somsiad_helper import *

@client.command(aliases=['8ball', '8-ball', '8'])
@commands.cooldown(1, conf['user_command_cooldown'], commands.BucketType.user)
@commands.guild_only()
async def eightball(ctx, *args):
    '''Returns an 8-Ball answer.'''
    with open(os.path.join(bot_dir, 'data', 'eightball_answers.txt')) as f:
        responses = [line.strip() for line in f.readlines() if not line.strip().startswith('#')]
    response = random.choice(responses)
    await ctx.send(f'{ctx.author.mention}\n:8ball: {response}')
