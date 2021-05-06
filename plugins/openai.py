# Copyright 2021 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.
import os
import datetime as dt
import string
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast

import discord
import sqlalchemy
from discord.ext import commands

import data
from configuration import configuration
from core import cooldown, has_permissions
from somsiad import Somsiad
from utilities import human_datetime


@dataclass
class Completion:
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]


class Chat(data.ServerRelated, data.ChannelSpecific, data.Base):
    lang = data.Column(data.String, nullable=False)


def check_gpt_authorization(ctx: commands.Context):
    gpt_authorized_servers = os.getenv('GPT_AUTHORIZED_SERVERS')
    if not gpt_authorized_servers or ctx.guild.id not in map(int, gpt_authorized_servers.split(',')):
        raise commands.NotOwner()  # type: ignore
    return True

is_gpt_authorized = commands.check(check_gpt_authorization)

class OpenAI(commands.Cog):
    bot: Somsiad
    convos: Dict[int, List[str]]

    def __init__(self, bot: Somsiad):
        self.bot = bot
        self.convos = {}

    async def fetch_completion(
        self,
        prompt: str,
        *,
        engine_id: str = "davinci",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stop: Optional[str] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        best_of: Optional[int] = None,
    ) -> Optional[Completion]:
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
            convo = self.convos[channel_id][-6:]
        elif lang == 'en':
            convo = [f"It's {human_datetime(dt.datetime.now(), days_difference=False, time=False)}. You are bot Somsiad. You were made by Twixes. You're chatting on Discord with person {user}:", '']
        else:
            convo = [f'Jest {human_datetime(dt.datetime.now(), days_difference=False, time=False)}. Jesteś bot Somsiad. Stworzył cię Twixes. Rozmawiasz z osobą {user}:', '']
        convo_lines = [*convo, f'{user}: {prompt}\n',]

        result = ''
        while not result or result == prompt:
            completion = await self.fetch_completion(
                '\n'.join(convo_lines), max_tokens=120, temperature=0.9, top_p=0.9, frequency_penalty=0.9, presence_penalty=0.5
            )
            result: str = completion.choices[0]["text"]
            result = result.strip()
            somsiad_index = result.find('Somsiad:')
            if somsiad_index >= 0:
                result = result[somsiad_index + len('Somsiad:') + 1:]
            else:
                colon_index = result.find(': ')
                if colon_index >= 0:
                    result = result[colon_index + 1:]
            user_index = result.find(f'{user}:')
            if user_index >= 0:
                result = result[:user_index]
            result = result.split('\n')[0].strip(string.whitespace + '-–;.')
        self.convos[channel_id] = [*convo_lines, f'Somsiad: {result}\n',]
        return result

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if cast(discord.User, message.author).bot:
            return
        ctx = await self.bot.get_context(message)
        try:
            check_gpt_authorization(ctx)
        except:
            return
        message_text = cast(str, message.clean_content)
        if not message_text or message_text.startswith('//'):
            return
        with data.session() as session:
            chat: Optional[Chat] = session.query(Chat).get(message.channel.id)
        if chat is None:
            return
        if ctx.valid:
            return
        with cast(discord.TextChannel, message.channel).typing():
            completed_answer = await self.fetch_completed_answer(
                prompt=message_text, user=message.author.display_name, channel_id=message.channel.id, lang=chat.lang
            )
        await self.bot.send(ctx, completed_answer)

    @commands.group(aliases=['rozmowa', 'rozmawiaj'], invoke_without_command=True, case_insensitive=True)
    @cooldown()
    @is_gpt_authorized
    @commands.guild_only()
    async def chat(self, ctx, *, message_text: commands.clean_content(fix_channel_mentions=True) = ''):
        if not message_text or message_text.startswith('//'):
            return
        with data.session() as session:
            chat: Optional[Chat] = session.query(Chat).get(ctx.channel.id)
        lang = chat.lang if chat is not None else 'pl'
        with ctx.typing():
            completed_answer = await self.fetch_completed_answer(
                prompt=message_text, user=ctx.author.display_name, channel_id=ctx.channel.id, lang=lang
            )
        await self.bot.send(ctx, completed_answer)

    @chat.command(aliases=['start', 'rozpocznij', 'zacznij'])
    @cooldown()
    @is_gpt_authorized
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
    @is_gpt_authorized
    @commands.guild_only()
    @has_permissions(manage_channels=True)
    async def chat_stop(self, ctx: commands.Context):
        try:
            with data.session(commit=True) as session:
                session.query(Chat).filter_by(channel_id=ctx.channel.id).delete()
        except sqlalchemy.exc.IntegrityError:
            pass
        self.convos[ctx.channel.id] = []
        await cast(discord.Message, ctx.message).add_reaction('✅')

    @chat.command(aliases=['reset', 'zresetuj'])
    @cooldown()
    @is_gpt_authorized
    @commands.guild_only()
    async def chat_reset(self, ctx: commands.Context):
        self.convos[ctx.channel.id] = []
        await cast(discord.Message, ctx.message).add_reaction('✅')


def setup(bot: Somsiad):
    if configuration.get('openai_api_key') is not None:
        bot.add_cog(OpenAI(bot))
