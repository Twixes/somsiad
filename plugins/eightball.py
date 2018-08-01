import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
import random
import os
from somsiad_helper import *


@client.command(aliases=['8ball', '8-ball', '8'])
@commands.cooldown(1, conf['cooldown'], commands.BucketType.user)
@commands.guild_only()
async def eightball(ctx, *args):
    """Returns an 8-Ball answer."""
    with open(os.path.join(bot_dir, 'data', 'eightball_answers.txt')) as f:
        responses = [line.strip() for line in f.readlines() if not line.strip().startswith('#')]
    
    response = random.choice(responses)
    await ctx.send('{} '.format(ctx.author.mention) + "\n:8ball: " + response)
