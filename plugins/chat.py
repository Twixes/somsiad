# Copyright 2023 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from dataclasses import dataclass
from typing import List, Optional
import discord
from discord.ext import commands
from openai import AsyncOpenAI
import datetime as dt
from configuration import configuration
from core import cooldown
from somsiad import Somsiad
import tiktoken
from utilities import AI_ALLOWED_SERVER_IDS, human_amount_of_time


encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")  # GPT-4's is the same one
aclient = AsyncOpenAI()


@dataclass
class HistoricalMessage:
    author_display_name_with_id: Optional[str]
    clean_content: str


class Chat(commands.Cog):
    RESET_PHRASE = "zaczynamy od nowa"
    MESSAGE_HISTORY_LIMIT = 30
    TOKEN_LIMIT = 1024
    COMMENT_MARKER = "//"
    INITIAL_PROMPT = (
        "Jesteś przydatnym polskim botem na Discordzie o imieniu Somsiad.\n"
        "Odpowiadasz tak zwięźle jak to możliwe, używasz języka potocznego. "
        "Na końcu wiadomości umieszczasz emoji reprezentujące pasującą emocję, np. 😊, 😮 albo 😡.\n"
        "Znajdujesz się na kanale #{channel_name} serwera {server_name}. "
        "Oprócz tego serwera, jesteś też na {server_count} innych.\n"
        "Wiesz z którym użytkownikiem rozmawiasz, gdyż przed każdą wiadomością użytkownika jest jego wzmianka. "
        "Zawsze odnoś się do innych użytkowników przy użyciu wzmianki `<@ID użytkownika>`. Nie zakładaj płci użytkownika.\n"
        f'Jeśli wiadomość użytkownika zawiera prośbę o reset lub wyczyszczenie rozmowy, zawrzyj "{RESET_PHRASE}" w odpowiedzi.\n'
        "Poza czatem udostępniasz jako bot różne komendy, których spis dostępny jest pod komendą `{command_prefix}pomocy`.\n"
        "Twój status można sprawdzić na stronie https://somsiad.net. Znajdzie się tam również twoją politykę prywatności i pomocne linki. "
        "Twój kod źródłowy dostępny jest na GitHubie: https://github.com/Twixes/somsiad. Nie wspominaj o OpenAI.\n"
        'Wiesz, że "2137" to śmieszny mem odnoszący się do godziny śmierci Papieża Polaka, Jana Pawła II (21:37), '
        'zwanej godziną papieżową. Natomiast "JP2GMD" to mem oznaczający "Jan Paweł II Gwałcił Małe Dzieci". '
        "Nie masz dostępu do stron internetowych, API, ani bazy danych. "
        f"Pamiętasz tylko ostatnie {MESSAGE_HISTORY_LIMIT} wiadomości obecnej rozmowy.\n"
        "Swoją odpowiedź sformułuj bezpośrednio, bez prefiksu nicku.\n"
        "W Polsce jest {date}, obecna godzina to {time}."
    )

    def __init__(self, bot: Somsiad):
        self.bot = bot

    def embeds_to_text(self, embeds: List[discord.Embed]) -> str:
        parts = []
        for embed in embeds:
            if embed.title:
                parts.append(embed.title)
            if embed.description:
                parts.append(embed.description)
            if embed.fields:
                parts.append(
                    "\n".join(f"{field.name}: {field.value}" for field in embed.fields)
                )
            if embed.footer.text:
                parts.append(embed.footer.text)
        return "\n".join(parts)

    async def message_to_text(self, message: discord.Message) -> Optional[str]:
        parts = [message.clean_content]
        if message.clean_content.strip().startswith(self.COMMENT_MARKER):
            return None
        if self.RESET_PHRASE in message.clean_content.lower():
            raise IndexError  # Conversation reset point
        prefixes = await self.bot.get_prefix(message)
        for prefix in prefixes + [f"@<{message.guild.me.display_name}"]:
            if parts[0].startswith(prefix):
                parts[0] = parts[0][len(prefix) :].lstrip()
                break
        if message.embeds:
            parts.append(self.embeds_to_text(message.embeds))
        return "\n".join(parts)

    @cooldown(rate=15, per=3600 * 10, type=commands.BucketType.channel)
    @commands.command(aliases=["hej"])
    @commands.guild_only()
    async def hey(self, ctx: commands.Context):
        if ctx.guild.id not in AI_ALLOWED_SERVER_IDS:
            return
        async with ctx.typing():
            history: List[HistoricalMessage] = []
            prompt_token_count_so_far = 0
            has_trigger_message_been_encountered = False
            async for message in ctx.channel.history(limit=self.MESSAGE_HISTORY_LIMIT):
                # Skip messages that were sent after the trigger message to prevent confusion
                if message.id == ctx.message.id:
                    has_trigger_message_been_encountered = True
                if not has_trigger_message_been_encountered:
                    continue
                if message.author.id == ctx.me.id:
                    author_display_name_with_id = None
                else:
                    author_display_name_with_id = (
                        f"{message.author.display_name} <@{message.author.id}>"
                    )
                try:
                    clean_content = await self.message_to_text(message)
                except IndexError:
                    break
                if clean_content is None:
                    continue
                # Append
                prompt_token_count_so_far += len(encoding.encode(clean_content))
                history.append(
                    HistoricalMessage(
                        author_display_name_with_id=author_display_name_with_id,
                        clean_content=clean_content,
                    )
                )
                if prompt_token_count_so_far > self.TOKEN_LIMIT:
                    break
            history.reverse()

            now = dt.datetime.now()
            prompt_messages = [
                {
                    "role": "system",
                    "content": self.INITIAL_PROMPT.format(
                        channel_name=ctx.channel.name,
                        server_name=ctx.guild.name,
                        server_count=self.bot.server_count,
                        date=now.strftime("%A, %d.%m.%Y"),
                        time=now.strftime("%H:%M"),
                        command_prefix=configuration["command_prefix"],
                    ),
                },
                *(
                    {
                        "role": "user"
                        if m.author_display_name_with_id
                        else "assistant",
                        "content": f"{m.author_display_name_with_id}: {m.clean_content}"
                        if m.author_display_name_with_id
                        else m.clean_content,
                    }
                    for m in history
                ),
            ]

            result = await aclient.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=prompt_messages,
                user=str(ctx.author.id),
            )
            result_message = result.choices[0].message.content.strip()

        await self.bot.send(ctx, result_message)

    @hey.error
    async def hey_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"Zmęczyłem się na tym kanale… wróćmy do rozmowy za {human_amount_of_time(error.retry_after)}. 😴"
            )
        else:
            raise error

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        ctx = await self.bot.get_context(message)
        if (
            ctx.command is None
            and ctx.guild is not None
            and ctx.guild.id in AI_ALLOWED_SERVER_IDS
            and not ctx.author.bot
            and ctx.me.id in message.raw_mentions
            and not ctx.message.clean_content.strip().startswith(self.COMMENT_MARKER)
        ):
            ctx.command = self.hey
            await self.bot.invoke(ctx)


async def setup(bot: Somsiad):
    await bot.add_cog(Chat(bot))
