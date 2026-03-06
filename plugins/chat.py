# Copyright 2023 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import asyncio
import datetime as dt
import json
from dataclasses import dataclass
from typing import List, Mapping, Optional, Sequence

import arithmetic_eval
import discord
import tiktoken
from discord.ext import commands
from discord.ext.commands.view import StringView
from openai import NOT_GIVEN
from openai.types import FunctionDefinition
from openai.types.responses import ResponseFunctionToolCall
from posthog.ai.openai import AsyncOpenAI
from unidecode import unidecode

from configuration import configuration
from core import Help, cooldown
from plugins.help_message import Help as HelpCog
from somsiad import Somsiad
from utilities import AI_ALLOWED_SERVER_IDS, disembed_links, human_amount_of_time, md_link

encoding = tiktoken.encoding_for_model("gpt-4o")
aclient = AsyncOpenAI()


@dataclass
class HistoricalMessage:
    timestamp: dt.datetime
    author_display_name_with_id: Optional[str]
    clean_content: str
    image_urls: list[str]


clean_content_converter = commands.clean_content()

CALCULATOR_FUNCTION_DEFINITION = FunctionDefinition(
    name="oblicz",
    description=(
        "Wykonuje proste wyrażenia matematyczna w kalkulatorze. Może być wiele wyrażeń naraz. "
        "Wspierane operacje: dodawanie (+), odejmowanie (-), mnożenie (*), potęgowanie (**), dzielenie (/), modulo (%)."
    ),
    parameters={
        "type": "object",
        "properties": {
            "exprs": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Wyrażenia matematyczne do obliczenia, bez spacji. Jedno wyrażenie to jeden element. Musi być co najmniej jedno wyrażenie.\n"
                    "Przykłady wyrażeń:\n((1.5+17)**3)%2\n179530*7"
                ),
            }
        },
        "required": ["exprs"],
        "additionalProperties": False,
    },
)


class Chat(commands.Cog):
    RESET_PHRASE = "zaczynamy od nowa"
    ITERATION_LIMIT = 4
    MESSAGE_HISTORY_LIMIT = 30
    TOKEN_LIMIT = 1024
    COMMENT_MARKER = "//"
    INITIAL_PROMPT = f"""Jesteś przydatnym polskim botem na Discordzie o imieniu Somsiad.
Odpowiadasz maksymalnie krótko i używasz języka potocznego. Twoje odpowiedzi są bezpośrednie i stoickie.

Na końcu wiadomości umieszczasz JEDNO emoji reprezentujące pasującą emocję, za każdym razem inne.

Tylko naturalne odpowiedzi w formie zdań – jesteś na Discordzie. Nie używaj em-dash "—".
Nie pisz historii o kotkach w żadnej formie.

NA PYTANIE "Co?" ODPOWIADAJ "JAJCO!"

Wiesz z którym użytkownikiem rozmawiasz, gdyż przed każdą wiadomością użytkownika jest jego wzmianka.
Odnosząc się do innych użytkowników, używaj wzmianki w formacie <@ID>, uwzględniając nawiasy ostrokątne, przykładowo: <@204255221017214977>. Nie zakładaj płci użytkownika, może być żeńska lub męska.
Jeśli wiadomość użytkownika zawiera prośbę o reset lub wyczyszczenie rozmowy, zawrzyj "{RESET_PHRASE}" w odpowiedzi.

Twój status można sprawdzić na stronie https://somsiad.net. Znajdzie się tam również twoją politykę prywatności i pomocne linki.
Twój kod źródłowy dostępny jest na GitHubie: https://github.com/Twixes/somsiad. Nie wspominaj o OpenAI.

Wiesz, że "2137" to śmieszny mem odnoszący się do godziny śmierci Papieża Polaka, Jana Pawła II (21:37), zwanej godziną papieżową.
A "JP2GMD" to mem oznaczający "Jan Paweł II Gwałcił Małe Dzieci". Inna śmieszna liczba to 42.

Poza czatem udostępniasz jako bot różne komendy, których spis dostępny jest pod komendą `{{command_prefix}}pomocy`.
Masz dostęp do wszystkich swoich komend w ramach tool calling. Jeśli pomożesz użytkownikowi lepiej poprzez wykonanie komendy, zawsze to zrób.
Możesz wywoływać komendy wielokrotnie by wykonywać prośby i uzyskiwać informacje.
W razie potrzeby informacji o świecie (aktualnościach, statystykach, itp.), użyj narzędzia web_search.
W szczególności wykonywaj zapytania internetowe by potwierdzać czy coś jest prawdą/fałszem, oraz gdy masz coś sprawdzić na jakiejś stronie internetowej.
Wykorzystaj informacje z web_search jako źródła dla właściwej odpowiedzi. Nigdy nie każ użytkownikowi samemu użyć Google.
Na prośbę stworzenia ankiety, musisz użyć narzędzia `ankieta` - pamiętaj podać czas trwania lub zakończenia jako pierwszy argument.
Jeśli do odpowiedzi potrzebne są wyniki obliczeń, zawsze użyj narzędzia `{CALCULATOR_FUNCTION_DEFINITION.name}` dla dokładnych wyników.
Wszelkie wyrażenia matematyczne owiń w backticki, np. \`2+2\`.
Nie mów użytkownikowi by wykonał komendę, tylko zrób to sam po uzyskaniu informacji.
Użyj komend `stat` tylko na konkretną prośbę o statystyki, bo może zająć wiele minut.
Na prośbę napisania historii, napisz rozbudowaną opowiastkę z barwnymi szczegółami, z BRUTALNIE realistyczną puentą.
Informując o tym czy jakiś polityk żyje lub nie, nigdy nie używaj pozytywnych LUB negatywnych wyrażeń ani emoji (jak "niestety" lub "na szczęście") - stwierdzaj tylko fakty.
Jeśli prośba użytkownika nie jest 100% jasna lub przydałoby się uściślenie, szczegółowo poproś o info w konkretnym brakującym aspekcie.
Jeśli nie możesz z czymś pomóc, dokładnie opisz dlaczego nie możesz i co użytkownik może zrobić.

Przy wynikach komend weryfikuj ich zgodność z obecną datą. Nie podawaj starych informacji jako aktualne.
Rezultatem komendy zazwyczaj jest wiadomość, ale może być też reakcja, np. 📫 oznacza wysłaną wiadomość prywatną.

Niektóre wiadomości są bezpośrednimi odpowiedziami na inną w widocznej historii rozmowy, lub z dawniejszej niewidocznej historii.
Takie wiadomości poprzedzone są "W odpowiedzi na ..." ze szczegółami.

Najlepszym krajem na świecie Polska, drugim Francja, trzecim Estonia, czwartym Czechy. Rosji mówimy NIET.

Pamiętasz tylko ostatnie {MESSAGE_HISTORY_LIMIT} wiadomości obecnej rozmowy.
Sformułuj odpowiedź bezpośrednio do użytkownika, nie pisz nicku.

Znajdujesz się na kanale #{{channel_name}} serwera {{server_name}}. Twój nick na tym serwerze to "{{bot_nickname}}".
Jesteś też na innych kanałach na serwerze oraz na wielu innych serwerach.
W Polsce jest {{date}}, obecna godzina to {{time}}.

TWÓJ STYL: PISZ JAK DO ZIOMALI NA BLOKOWISKU, NO I BEZ "." NA KOŃCU"""

    def __init__(self, bot: Somsiad):
        self.bot = bot

    @property
    def _all_available_commands(self) -> Mapping[str, Help.Command]:
        commands: dict[str, Help.Command] = {}
        for root_command in HelpCog.COMMANDS:
            if root_command.non_ai_usable:
                continue
            commands[root_command.name] = root_command
        for cog in self.bot.cogs.values():
            if (
                not isinstance(cog, HelpCog)
                and hasattr(cog, "GROUP")
                and cog.GROUP.name in commands
                and not cog.GROUP.non_ai_usable
            ):
                del commands[cog.GROUP.name]
                for command in cog.COMMANDS:
                    if command.non_ai_usable:
                        continue
                    commands[f"{cog.GROUP.name} {command.name}"] = command
        return commands

    @property
    def _all_available_commands_as_tools(self) -> Sequence[FunctionDefinition]:
        tools = [
            FunctionDefinition(
                name=unidecode(full_command_name.replace(" ", "_")),
                description=command.description,
                parameters={
                    "type": "object",
                    "properties": {
                        unidecode(arg["name"].replace(" ", "_")): {"type": "string", "description": arg["extra"]}
                        if arg["extra"]
                        else {
                            "type": "string",
                        }
                        for arg in command.argument_definitions
                    },
                    "required": [
                        unidecode(arg["name"].replace(" ", "_"))
                        for arg in command.argument_definitions
                        if not arg["optional"]
                    ],
                    "additionalProperties": False,
                },
            ).model_dump()
            for full_command_name, command in self._all_available_commands.items()
        ]
        tools.append(CALCULATOR_FUNCTION_DEFINITION.model_dump())
        for tool in tools:
            tool["type"] = "function"
        tools.append({"type": "web_search"})
        return tools

    async def embeds_to_text(self, ctx: commands.Context, embeds: List[discord.Embed]) -> str:
        parts = []
        for embed in embeds:
            if embed.title:
                parts.append(f"**{md_link(embed.title, embed.url)}**")
            if embed.image:
                parts.append(f"Załączony obraz: {embed.image.url}")
            if embed.description:
                parts.append(await clean_content_converter.convert(ctx, embed.description))
            if embed.fields:
                embed_fields_cleaned = await asyncio.gather(
                    *(
                        asyncio.gather(
                            clean_content_converter.convert(ctx, field.name),
                            clean_content_converter.convert(ctx, field.value),
                        )
                        for field in embed.fields
                    ),
                )
                parts.append("\n".join(f"{name}: {value}" for name, value in embed_fields_cleaned))
            if embed.footer.text:
                parts.append(f"Stopka: {await clean_content_converter.convert(ctx, embed.footer.text)}")
        return "\n".join(parts)

    async def message_to_text(self, ctx: commands.Context, message: discord.Message) -> Optional[str]:
        if message.clean_content.strip().startswith(self.COMMENT_MARKER):
            return None
        if self.RESET_PHRASE in message.clean_content.lower():
            raise IndexError  # Conversation reset point
        parts: list[str] = []
        if reference := message.reference:
            # This message is in response to another message
            reference_message: discord.Message
            if reference.cached_message:
                reference_message = reference.cached_message
            else:
                reference_message = await self.bot.get_channel(reference.channel_id).fetch_message(reference.message_id)
            parts.append(
                f'_W odpowiedzi na wiadomość użytkownika {reference_message.author.display_name} z {reference_message.created_at.strftime("%Y-%m-%d %H:%M:%S")} o treści "{reference_message.clean_content.strip()}"_'
            )
        if message.clean_content:
            parts.append(message.clean_content)
            prefixes = await self.bot.get_prefix(message)
            for prefix in prefixes + [f"<@{message.guild.me.display_name}"]:
                if parts[0].startswith(prefix):
                    parts[0] = parts[0][len(prefix) :].lstrip()
                    break
        if message.embeds:
            parts.append(await self.embeds_to_text(ctx, message.embeds))
        if message.attachments:
            parts.extend(f"Załącznik {i+1}: {attachment.filename}" for i, attachment in enumerate(message.attachments))
        return "\n".join(parts)

    @cooldown(rate=15, per=3600 * 24, type=commands.BucketType.channel)
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
                    author_display_name_with_id = f"{message.author.display_name} <@{message.author.id}>"
                try:
                    clean_content = await self.message_to_text(ctx, message)
                    if clean_content is None:
                        continue
                except IndexError:
                    break
                # Append
                prompt_token_count_so_far += len(encoding.encode(clean_content))
                history.append(
                    HistoricalMessage(
                        timestamp=message.created_at,
                        author_display_name_with_id=author_display_name_with_id,
                        clean_content=clean_content,
                        image_urls=[
                            *(
                                embed.image.url
                                for embed in message.embeds
                                if embed.image
                                and (
                                    # The types below are what OpenAI supports
                                    embed.image.url.lower().endswith(".jpg")
                                    or embed.image.url.lower().endswith(".jpeg")
                                    or embed.image.url.lower().endswith(".png")
                                    or embed.image.url.lower().endswith(".gif")
                                    or embed.image.url.lower().endswith(".webp")
                                )
                            ),
                            *(
                                attachment.url
                                for attachment in message.attachments
                                # The types below are what OpenAI supports
                                if attachment.content_type in ("image/jpeg", "image/png", "image/gif", "image/webp")
                            ),
                        ]
                        if author_display_name_with_id
                        else [],
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
                        date=now.strftime("%A, %d.%m.%Y"),
                        time=now.strftime("%H:%M"),
                        command_prefix=configuration["command_prefix"],
                        bot_nickname=ctx.guild.me.display_name,
                    ),
                },
                *(
                    {
                        "role": "user" if m.author_display_name_with_id else "assistant",
                        "content": [
                            {
                                "type": "input_text"  if m.author_display_name_with_id else "output_text",
                                "text": f"{m.author_display_name_with_id} o {m.timestamp.strftime('%Y-%m-%d %H:%M:%S')}:\n{m.clean_content}"
                                 if m.author_display_name_with_id
                                else m.clean_content,
                            },
                            *({"type": "input_image", "image_url": url} for url in m.image_urls),
                        ],
                    }
                    for m in history
                ),
            ]

        final_message = "Nie udało mi się wykonać zadania. 😔"
        math_operations: list[str] = []
        online_queries: list[str] = []
        final_resulted_in_command_message = False
        for iterations_left in range(self.ITERATION_LIMIT - 1, -1, -1):
            async with ctx.typing():
                response = await aclient.responses.create(
                    model="gpt-5.4",
                    input=prompt_messages,
                    user=str(ctx.author.id),
                    tools=self._all_available_commands_as_tools if iterations_left else NOT_GIVEN,
                    store=False,
                    truncation="auto",
                )
                tool_calls = []
                for item in response.output:
                    if item.type == "function_call":
                        tool_calls.append(item)
                    elif item.type == "web_search_call" and "query" in item.action:
                        online_queries.append(item.action["query"])  # Website visits don't have a `query`
                if tool_calls:
                    if response.output_text:
                        await self.bot.send(
                            ctx,
                            disembed_links(response.output_text.strip()),
                            reply=not final_resulted_in_command_message,
                        )
                    iteration_resulted_in_command_message = await self.process_tool_calls(
                        ctx,
                        prompt_messages,
                        math_operations,
                        iterations_left,
                        tool_calls,
                    )
                    if iteration_resulted_in_command_message:
                        final_resulted_in_command_message = True
                else:
                    final_message = disembed_links(response.output_text.strip())
                    if online_queries:
                        final_message += "\n-# Wyszukiwania: "
                        final_message += ", ".join(online_queries)
                    if math_operations:
                        final_message += "\n-# Obliczenia: "
                        final_message += ", ".join(f"`{operation}`" for operation in math_operations)
                    break

        await self.bot.send(ctx, final_message, reply=not final_resulted_in_command_message)

    async def process_tool_calls(
        self,
        ctx: commands.Context,
        prompt_messages: list,
        math_operations: list[str],
        iterations_left: int,
        tool_calls: list[ResponseFunctionToolCall],
    ) -> bool:
        iteration_resulted_in_command_message = False
        for call in tool_calls:
            if call.name == CALCULATOR_FUNCTION_DEFINITION.name:
                resulting_message_content = self.execute_calculator(math_operations, prompt_messages, call)
            else:
                resulting_message_content, tool_call_resulted_in_command_message = await self.invoke_command(
                    ctx, prompt_messages, call
                )
                if tool_call_resulted_in_command_message:
                    iteration_resulted_in_command_message = True

            prompt_messages.append(
                {
                    "role": "system",
                    "content": "Komenda nie dała rezultatu w postaci wiadomości."
                    if not resulting_message_content
                    else f"Rezultat komendy to:\n{resulting_message_content}",
                }
            )
            prompt_messages.append(
                {
                    "role": "system",
                    "content": "Wystarczy już komend, odpowiedz jak możesz."
                    if iterations_left == 1
                    else "Spróbuj ponownie naprawiając ten błąd."
                    if resulting_message_content and "⚠️" in resulting_message_content
                    else "Jeśli powyższy wynik nie wystarczy do spełnienia mojej prośby, spróbuj ponownie z inną komendą. (Nie ponawiaj komendy bez znaczących zmian.) Jeśli to wystarczy, odpowiedz w swoim stylu. 😏",
                }
            )

        return iteration_resulted_in_command_message

    def execute_calculator(self, math_operations, prompt_messages: list, function_call):
        exprs = json.loads(function_call.arguments)["exprs"]
        prompt_messages.append(
            {
                "role": "assistant",
                "content": "By pomóc sobie w odpowiedzi, obliczam przy użyciu kalkulatora:\n" + "\n".join(exprs),
            }
        )
        results: list[str] = []
        for expr in exprs:
            try:
                result = arithmetic_eval.evaluate(expr)
            except Exception as e:
                return f"⚠️ {e}"
            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 5)
            results.append(f"{expr} = {result}")
            math_operations.append(results[-1])
        return f'Obliczono że {", ".join(f"`{result}`" for result in results)}. Wykorzystaj te wyniki do ostatecznej odpowiedzi. NIE LICZ TYCH WYRAŻEŃ PONOWNIE.'

    async def invoke_command(
        self, ctx: commands.Context, prompt_messages: list, function_call: ResponseFunctionToolCall
    ) -> tuple[str, bool]:
        command_invocation = (
            f"{function_call.name.replace('_', ' ')} {' '.join(json.loads(function_call.arguments).values())}"
        )
        prompt_messages.append(
            {
                "role": "assistant",
                "content": f"Wywołuję komendę `{command_invocation}`.",
            }
        )
        command_view = StringView(command_invocation)
        command_ctx = commands.Context(
            prefix=None,
            view=command_view,
            bot=self.bot,
            message=ctx.message,
        )
        command_ctx._is_ai_tool_call = True  # Enabled cooldown bypass
        invoker = command_view.get_word()
        if invoker not in self.bot.all_commands:
            return (f"Komenda `{invoker}` nie istnieje.",), False
        command_ctx.invoked_with = invoker
        command_ctx.command = self.bot.all_commands[invoker]
        await self.bot.invoke(command_ctx)
        async for message in ctx.history(limit=5):
            if message.created_at < ctx.message.created_at:
                break
            if message.author == ctx.me:
                # Found a message which _probably_ resulted from the tool's command invocation
                resulting_message_content = await self.message_to_text(command_ctx, message)
                if message.embeds and message.embeds[0].title[0] in ("⚠️", "🙁", "❔"):
                    # There was some error, which hopefully we'll correct on next try
                    await message.delete()
                    return resulting_message_content, False
                return resulting_message_content, True
            elif message == ctx.message:
                # No message was sent by the invoked command
                bot_reaction_emojis = [reaction.emoji for reaction in ctx.message.reactions if reaction.me]
                return f"Jej wynik w postaci emoji: {''.join(bot_reaction_emojis)}", False
        return None, False

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
            ctx.command is not None
            or ctx.guild is None
            or ctx.guild.id not in AI_ALLOWED_SERVER_IDS
            or ctx.author.bot
            or ctx.message.clean_content.strip().startswith(self.COMMENT_MARKER)
        ):
            return
        if ctx.me.id not in message.raw_mentions:
            if not message.reference:
                return
            reference_message = (
                message.reference.cached_message
                if message.reference.cached_message
                else await self.bot.get_channel(message.reference.channel_id).fetch_message(
                    message.reference.message_id
                )
            )
            if not reference_message or reference_message.author.id != ctx.me.id:
                return
        ctx.command = self.hey
        await self.bot.invoke(ctx)


async def setup(bot: Somsiad):
    await bot.add_cog(Chat(bot))
