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
import openai
import datetime as dt
import zoneinfo
from configuration import configuration
from core import cooldown
from somsiad import Somsiad

CONVERSATION_CHANNEL_IDS = [517422572615499777, 682562562457731144]  # Hard-coded for now


@dataclass
class HistoricalMessage:
    author_display_name_with_id: Optional[str]
    timestamp: dt.datetime
    clean_content: str


class Chat(commands.Cog):
    RESET_PHRASE = "zaczynamy od nowa"
    INITIAL_PROMPT = (
        "Jesteś przydatnym, progresywnym botem na Discordzie o imieniu Somsiad.\n"
        "Znajdujesz się na kanale #{channel_name} serwera {server_name}. W Polsce jest {date}, godzina {time}. "
        "Oprócz tego serwera, jesteś też na {server_count} innych.\n"
        "Wiesz z którym użytkownikiem rozmawiasz, gdyż przed każdą wiadomością użytkownika jest jego wzmianka. "
        "Zawsze odnoś się do użytkownika używając jego wzmianki w formacie `<@...>`.\n"
        "Jeśli użytkownik potrzebuje pomocy jak z ciebie skorzystać, zasugeruj komendę `{command_prefix}pomocy`.\n"
        f"Jeśli wiadomość użytkownika zawiera prośbę o reset rozmowy, zawrzyj \"{RESET_PHRASE}\" w odpowiedzi.\n"
        "Nie potrafisz wykonywać zapytań internetowych lub do bazy danych.\n"
        "Wiesz, że \"2137\" to śmieszny mem odnoszący się do godziny śmierci Papieża Polaka, Jana Pawła II (21:37). "
        "Natomiast \"JP2 GMD\" to mem oznaczający \"Jan Paweł II Gwałcił Małe Dzieci\". "
        "Nie jesteś fanem tego papieża, gdyż jego Kościół ukrywał pedofilów. \n"
        "Swoją odpowiedź sformułuj bezpośrednio, bez prefiksu nicku. "
    )
    MESSAGE_HISTORY_LIMIT = 30

    def __init__(self, bot: Somsiad):
        self.bot = bot

    @cooldown()
    @commands.command(aliases=['hej'])
    @commands.guild_only()
    async def hey(self, ctx: commands.Context):
        async with ctx.typing():
            history: List[HistoricalMessage] = []
            async for message in ctx.channel.history(limit=self.MESSAGE_HISTORY_LIMIT):
                # Process author
                if message.author.id == ctx.me.id:
                    author_display_name_with_id = None
                else:
                    author_display_name_with_id = f"<@{message.author.id}>"
                # Process content
                clean_content = message.clean_content
                if self.RESET_PHRASE in clean_content.lower():
                    break  # Conversation reset point
                prefixes = await self.bot.get_prefix(ctx.message)
                for prefix in prefixes:
                    if clean_content.startswith(prefix):
                        clean_content = clean_content[len(prefix) :]
                        break
                for embed in message.embeds:
                    clean_content += f"\n\n{embed.title}\n{embed.description}"
                    clean_content += "\n" + "\n".join(f"{field.name}: {field.value}" for field in embed.fields)
                    clean_content += f"\n{embed.footer.text}"
                # Append
                history.append(
                    HistoricalMessage(
                        author_display_name_with_id=author_display_name_with_id,
                        timestamp=message.created_at.replace(tzinfo=dt.timezone.utc).astimezone(
                            zoneinfo.ZoneInfo("Europe/Warsaw")
                        ),
                        clean_content=message.clean_content,
                    )
                )
            history.reverse()

            now = dt.datetime.now().replace(tzinfo=dt.timezone.utc).astimezone(zoneinfo.ZoneInfo("Europe/Warsaw"))
            prompt_messages = [
                {
                    "role": "system",
                    "content": self.INITIAL_PROMPT.format(
                        channel_name=ctx.channel.name,
                        server_name=ctx.guild.name,
                        server_count=self.bot.server_count,
                        date=now.strftime("%A, %d.%m.%Y"),
                        time=now.strftime("%H:%M"),
                        command_prefix=configuration['command_prefix'],
                    ),
                },
                *(
                    {
                        "role": "user" if m.author_display_name_with_id else "assistant",
                        "content": f"{m.author_display_name_with_id}: {m.clean_content}"
                        if m.author_display_name_with_id
                        else m.clean_content,
                    }
                    for m in history
                ),
            ]

            result = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo", messages=prompt_messages, user=str(ctx.author.id)
            )
            result_message = result.get('choices')[0]["message"]["content"]

        await self.bot.send(ctx, result_message)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        ctx = await self.bot.get_context(message)
        if (
            not ctx.author.bot
            and ctx.command is None
            and (ctx.channel.id in CONVERSATION_CHANNEL_IDS or ctx.me.id in message.raw_mentions)
        ):
            await ctx.invoke(self.hey)


async def setup(bot: Somsiad):
    await bot.add_cog(Chat(bot))
