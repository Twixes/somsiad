import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
from somsiad_helper import *


@client.command()
@commands.cooldown(1, conf['cooldown'], commands.BucketType.user)
@commands.guild_only()
async def ping(ctx):
    """Check if bot is working."""
    await ctx.send(":ping_pong: Pong!")

@client.command(aliases=['lennyface'])
@commands.cooldown(1, conf['cooldown'], commands.BucketType.user)
@commands.guild_only()
async def lenny(ctx):
    """Lenny face."""
    await ctx.send("( ͡° ͜ʖ ͡°)")

@client.command(aliases=['fix'])
@commands.cooldown(1, conf['cooldown'], commands.BucketType.user)
@commands.guild_only()
async def unflip(ctx):
    """Unflip tables."""
    await ctx.send("┬─┬ノ(ಠ_ಠノ)")

@client.command()
@commands.cooldown(1, conf['cooldown'], commands.BucketType.user)
@commands.guild_only()
async def flip(ctx):
    """Flip tables."""
    await ctx.send("(╯°□°）╯︵ ┻━┻")

@client.command()
@commands.cooldown(1, conf['cooldown'], commands.BucketType.user)
@commands.guild_only()
async def shrug(ctx):
    """Shrug."""
    await ctx.send("¯\_(ツ)_/¯")

@client.command(aliases=['r'])
@commands.cooldown(1, conf['cooldown'], commands.BucketType.user)
@commands.guild_only()
async def subreddit_name(ctx, arg):
    """Returns full URL for given subreddit name."""
    url = "https://reddit.com/r/{}".format(arg)
    await ctx.send(url)
