# Copyright 2021 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, cast

import aiohttp
import discord
from discord.ext import commands

from configuration import configuration
from somsiad import Somsiad, SomsiadMixin

from .reactions import React


@dataclass
class Tweet:
    id: str
    text: str
    attachments: Optional[Dict[str, Any]]


class Twitter(commands.Cog, SomsiadMixin):
    TWEET_URL_REGEX = re.compile(r'https?:\/\/(?:(?:m|www)\.)?twitter\.com\/\w+\/status\/(\d+)\b', flags=re.IGNORECASE)

    async def fetch_tweet_with_attachments(self, tweet_id: str) -> Optional[Tweet]:
        url = f"https://api.twitter.com/2/tweets?ids={tweet_id}&tweet.fields=attachments"
        headers = {"Authorization": f"Bearer {configuration['twitter_bearer_token']}"}
        response = await self.bot.session.get(url, headers=headers)
        if response.status != 200:
            raise Exception(f"Twitter API request returned an error: {response.status} {await response.text()}")
        response_parsed = await response.json()
        if response_parsed.get('errors'):
            if any((error['title'] != 'Not Found Error' for error in response_parsed['errors'])):
                raise Exception(f"Twitter API request returned an error: {response_parsed}")
            return None
        raw_tweet = response_parsed['data'][0]
        return Tweet(id=raw_tweet['id'], text=raw_tweet['text'], attachments=raw_tweet.get('attachments'))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        matches = self.TWEET_URL_REGEX.finditer(message.content)
        for match in matches:
            tweet_id = match.group(1)
            tweet = await self.fetch_tweet_with_attachments(tweet_id)
            if tweet is not None and tweet.attachments and tweet.attachments.get('media_keys'):
                attachment_count = len(tweet.attachments['media_keys'])
                if attachment_count > 1:
                    await message.add_reaction(React.EMOJIS[0][str(attachment_count)])


async def setup(bot: Somsiad):
    if configuration.get('twitter_bearer_token') is not None:
        await bot.add_cog(Twitter(bot))
