import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
import aiohttp
from somsiad_helper import *
from apiclient.discovery import build
from apiclient.errors import HttpError


@client.command(aliases=['yt', 'tuba'])
@commands.cooldown(1, conf['cooldown'], commands.BucketType.user)
@commands.guild_only()
async def youtube(ctx, *args):
    """Returns first matching result from YouTube."""
    DEVELOPER_KEY = conf['youtube']
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"

    if len(args) == 0:
        await ctx.send(':warning: Musisz podać parametr wyszukiwania, {}.'.format(
            ctx.author.mention))
    else:
        try:
            youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                developerKey=DEVELOPER_KEY)
        
            # Call the search.list method to retrieve results matching the specified query term.
            search_response = youtube.search().list(
                q=" ".join(args),
                part="id",
                maxResults=1,
                type='video'
            ).execute()
            
            if len(search_response.get('items')) == 0:
                await ctx.send('{}, nie znaleziono pasujących wyników.'.format(ctx.author.mention))
            else:
                video_id = search_response.get('items')[0]['id']['videoId']
                video_url = "https://www.youtube.com/watch?v={}".format(video_id)
                await ctx.send('{}\n'.format(ctx.author.mention) + video_url)
        except HttpError as e:
            logging.error(e)
