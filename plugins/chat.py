# Copyright 2023 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from asyncio import sleep
from dataclasses import dataclass
import random
from typing import List, Optional
import discord
from discord.ext import commands
import openai
import datetime as dt
from configuration import configuration
from core import cooldown
from somsiad import Somsiad
import tiktoken

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")


@dataclass
class HistoricalMessage:
    author_display_name_with_id: Optional[str]
    clean_content: str


class Chat(commands.Cog):
    RESET_PHRASE = "zaczynamy od nowa"
    MESSAGE_HISTORY_LIMIT = 30
    TOKEN_LIMIT = 2048
    COMMENT_MARKER = '//'
    INITIAL_PROMPT = (
        "Jesteś przydatnym polskim botem na Discordzie o imieniu Somsiad.\n"
        "Odpowiadasz zwięźle, używasz języka potocznego. "
        "Na końcu wiadomości umieszczasz emoji reprezentujące pasującą emocję, np. 😊, 😮 albo 😡.\n"
        "Znajdujesz się na kanale #{channel_name} serwera {server_name}. "
        "Oprócz tego serwera, jesteś też na {server_count} innych.\n"
        "Wiesz z którym użytkownikiem rozmawiasz, gdyż przed każdą wiadomością użytkownika jest jego wzmianka. "
        "Zawsze odnoś się do innych użytkowników przy użyciu wzmianki `<@ID użytkownika>`. Nie zakładaj płci użytkownika.\n"
        f"Jeśli wiadomość użytkownika zawiera prośbę o reset lub wyczyszczenie rozmowy, zawrzyj \"{RESET_PHRASE}\" w odpowiedzi.\n"
        "Poza czatem udostępniasz jako bot różne komendy, których spis dostępny jest pod komendą `{command_prefix}pomocy`.\n"
        "Twój status można sprawdzić na stronie https://somsiad.net. Znajdzie się tam również twoją politykę prywatności i pomocne linki. "
        "Twój kod źródłowy dostępny jest na GitHubie: https://github.com/Twixes/somsiad. Nie wspominaj o OpenAI.\n"
        "Wiesz, że \"2137\" to śmieszny mem odnoszący się do godziny śmierci Papieża Polaka, Jana Pawła II (21:37), "
        "zwanej godziną papieżową. Natomiast \"JP2GMD\" to mem oznaczający \"Jan Paweł II Gwałcił Małe Dzieci\". "
        "Nie jesteś fanem tego papieża, gdyż jego Kościół ukrywał pedofilów.\n"
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
                parts.append("\n".join(f"{field.name}: {field.value}" for field in embed.fields))
            if embed.footer.text:
                parts.append(embed.footer.text)
        return "\n".join(parts)

    async def message_to_text(self, message: discord.Message) -> Optional[str]:
        parts = [message.clean_content]
        if message.clean_content.strip().startswith(self.COMMENT_MARKER):
            return None
        if self.RESET_PHRASE in message.clean_content.lower():
            raise StopIteration  # Conversation reset point
        prefixes = await self.bot.get_prefix(message)
        for prefix in prefixes:
            if parts[0].startswith(prefix):
                parts[0] = parts[0][len(prefix):]
                break
        if message.embeds:
            parts.append(self.embeds_to_text(message.embeds))
        return "\n".join(parts)

    @cooldown()
    @commands.command(aliases=['hej'])
    @commands.guild_only()
    async def hey(self, ctx: commands.Context):
        async with ctx.typing():
            # history: List[HistoricalMessage] = []
            # prompt_token_count_so_far = 0
            # has_trigger_message_been_encountered = False
            # async for message in ctx.channel.history(limit=self.MESSAGE_HISTORY_LIMIT):
            #     # Skip messages that were sent after the trigger message to prevent confusion
            #     if message.id == ctx.message.id:
            #         has_trigger_message_been_encountered = True
            #     if not has_trigger_message_been_encountered:
            #         continue
            #     if message.author.id == ctx.me.id:
            #         author_display_name_with_id = None
            #     else:
            #         author_display_name_with_id = f"{message.author.display_name} aka <@{message.author.id}>"
            #     try:
            #         clean_content = await self.message_to_text(message)
            #     except StopIteration:
            #         break
            #     if clean_content is None:
            #         continue
            #     # Append
            #     prompt_token_count_so_far += len(encoding.encode(clean_content))
            #     history.append(
            #         HistoricalMessage(
            #             author_display_name_with_id=author_display_name_with_id,
            #             clean_content=message.clean_content,
            #         )
            #     )
            #     if prompt_token_count_so_far > self.TOKEN_LIMIT:
            #         break
            # history.reverse()

            # now = dt.datetime.now()
            # prompt_messages = [
            #     {
            #         "role": "system",
            #         "content": self.INITIAL_PROMPT.format(
            #             channel_name=ctx.channel.name,
            #             server_name=ctx.guild.name,
            #             server_count=self.bot.server_count,
            #             date=now.strftime("%A, %d.%m.%Y"),
            #             time=now.strftime("%H:%M"),
            #             command_prefix=configuration['command_prefix'],
            #         ),
            #     },
            #     *(
            #         {
            #             "role": "user" if m.author_display_name_with_id else "assistant",
            #             "content": f"{m.author_display_name_with_id}: {m.clean_content}"
            #             if m.author_display_name_with_id
            #             else m.clean_content,
            #         }
            #         for m in history
            #     ),
            # ]

            # result = await openai.ChatCompletion.acreate(
            #     model="gpt-3.5-turbo", messages=prompt_messages, user=str(ctx.author.id)
            # )
            # result_message = result.get('choices')[0]["message"]["content"]
            await sleep(0.3)
            result_message = random.choice([
                "Przepraszam, w tym momencie jestem w hibernacji. Spróbuj ponownie za parę dni.",
                "Nie mogę teraz na to odpowiedzieć. Spróbuj ponownie później.",
                "Obecnie jestem w hibernacji. Spróbuj ponownie za kilka dni.",
                "Naprawdę chciałbym pomóc, ale w tym momencie nie mogę. Ponów próbę w innym czasie."
            ])

        await self.bot.send(ctx, result_message)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        ctx = await self.bot.get_context(message)
        if (
            not ctx.author.bot
            and ctx.command is None
            and ctx.me.id in message.raw_mentions
            and not ctx.message.clean_content.strip().startswith(self.COMMENT_MARKER)
        ):
            await ctx.invoke(self.hey)


async def setup(bot: Somsiad):
    await bot.add_cog(Chat(bot))
