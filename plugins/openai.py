# Copyright 2021 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import sqlalchemy
from core import cooldown, has_permissions
import string
import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast
import random
from utilities import human_datetime
import discord
from discord.ext import commands
import data
from configuration import configuration
from somsiad import Somsiad


@dataclass
class Completion:
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]


class Chat(data.ServerRelated, data.ChannelSpecific, data.Base):
    lang = data.Column(data.String, nullable=False)

class OpenAI(commands.Cog):
    bot: Somsiad
    convos: Dict[int, str]

    def __init__(self, bot: Somsiad):
        self.bot = bot
        self.convos = {}


    async def fetch_completion(self, prompt: str, *, engine_id: str = "davinci", max_tokens: Optional[int] = None, temperature: Optional[float] = None, top_p: Optional[float] = None, n: Optional[int] = None, stop: Optional[str] = None, presence_penalty: Optional[float] = None, frequency_penalty: Optional[float] = None, best_of: Optional[int] = None) -> Optional[Completion]:
        url = f"https://api.openai.com/v1/engines/{engine_id}/completions"
        headers = {"Authorization": f"Bearer {configuration['openai_api_key']}"}
        data = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "n": n,
            "stop": stop,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "best_of": best_of,
        }
        data = {k: v for k, v in data.items() if v is not None}
        response = await self.bot.session.post(url, json=data, headers=headers)
        if response.status != 200:
            raise Exception(f"OpenAI API request returned an error: {response.status} {await response.text()}")
        response_parsed = await response.json()
        return Completion(**response_parsed)

    async def fetch_completed_answer(self, *, prompt: str, user: str, channel_id: int, lang: str) -> str:
        if self.convos.get(channel_id):
            convo = self.convos[channel_id]
        elif lang == 'en':
            convo = f"It's {human_datetime(dt.datetime.now(), days_difference=False)}. You are bot Somsiad made by Twixes. You're chatting with person {user}:"
        else:
            convo = f'Jest {human_datetime(dt.datetime.now(), days_difference=False)}. Jesteś bot o imieniu Somsiad stworzonym przez Twixesa. Rozmawiasz z osobą {user}:'
        convo += f'\n\n{user}: {prompt}\n'

        result = ''
        while not result or result == prompt:
            completion = await self.fetch_completion(convo, max_tokens=80, temperature=0.9, top_p=0.9, frequency_penalty=0.5, presence_penalty=0.5)
            result: str = completion.choices[0]["text"]
            result = result.strip()
            colon_index = result.find(': ')
            if colon_index >= 0:
                result = result[colon_index+1:]
            result = result.split('\n')[0].strip(string.whitespace + '-–')

        self.convos[channel_id] = f'{convo}\nSomsiad: {result}'

        return result

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if cast(discord.User, message.author).bot:
            return
        with data.session() as session:
            chat: Optional[Chat] = session.query(Chat).get(message.channel.id)
        if chat is None:
            return
        message_text = cast(str, message.clean_content)
        if not message_text:
            return
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return
        with cast(discord.TextChannel, message.channel).typing():
            completed_answer = await self.fetch_completed_answer(prompt=message_text, user=message.author.display_name, channel_id=message.channel.id, lang=chat.lang)
        await self.bot.send(ctx, completed_answer)

    @commands.group(aliases=['rozmowa', 'rozmawiaj'], invoke_without_command=True, case_insensitive=True)
    @has_permissions(manage_channels=True)
    async def chat(self, ctx):
        pass

    @chat.command(aliases=['start', 'rozpocznij', 'zacznij'])
    @cooldown()
    @commands.guild_only()
    @has_permissions(manage_channels=True)
    async def chat_start(self, ctx: commands.Context, lang: str = 'pl'):
        try:
            with data.session(commit=True) as session:
                chat = Chat(server_id=ctx.guild.id, channel_id=ctx.channel.id, lang=lang)
                session.add(chat)
        except sqlalchemy.exc.IntegrityError:
            pass
        await cast(discord.Message, ctx.message).add_reaction('✅')

    @chat.command(aliases=['stop', 'end', 'zakończ', 'zakoncz', 'skończ', 'skoncz', 'przerwij'])
    @cooldown()
    @commands.guild_only()
    @has_permissions(manage_channels=True)
    async def chat_stop(self, ctx: commands.Context):
        try:
            with data.session(commit=True) as session:
                session.query(Chat).filter_by(channel_id=ctx.channel.id).delete()
        except sqlalchemy.exc.IntegrityError:
            pass
        self.convos[ctx.channel.id] = ''
        await cast(discord.Message, ctx.message).add_reaction('✅')

    @chat.command(aliases=['reset', 'zresetuj'])
    @cooldown()
    @commands.guild_only()
    @has_permissions(manage_channels=True)
    async def chat_reset(self, ctx: commands.Context):
        self.convos[ctx.channel.id] = ''
        await cast(discord.Message, ctx.message).add_reaction('✅')


def setup(bot: Somsiad):
    if configuration.get('openai_api_key') is not None:
        bot.add_cog(OpenAI(bot))
