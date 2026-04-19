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
import re
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

TEXT_ATTACHMENT_MAX_SIZE = 8000

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

DISCORD_TOOL_DEFINITIONS: dict[str, FunctionDefinition] = {
    "send_message_in_another_channel": FunctionDefinition(
        name="send_message_in_another_channel",
        description="Wysyła wiadomość na inny kanał tekstowy na tym serwerze Discord.",
        parameters={
            "type": "object",
            "properties": {
                "channel_name": {"type": "string", "description": "Nazwa kanału (bez #)"},
                "message": {"type": "string", "description": "Treść wiadomości do wysłania"},
            },
            "required": ["channel_name", "message"],
            "additionalProperties": False,
        },
    ),
    "read_history_of_another_channel": FunctionDefinition(
        name="read_history_of_another_channel",
        description="Czyta ostatnie wiadomości z innego kanału na tym serwerze Discord.",
        parameters={
            "type": "object",
            "properties": {
                "channel_name": {"type": "string", "description": "Nazwa kanału (bez #)"},
                "limit": {
                    "type": "integer",
                    "description": "Maksymalna liczba wiadomości do odczytania (domyślnie 20, max 50)",
                },
            },
            "required": ["channel_name"],
            "additionalProperties": False,
        },
    ),
    "search_messages": FunctionDefinition(
        name="search_messages",
        description="Szuka wiadomości zawierających podaną frazę na kanale na tym serwerze Discord.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Fraza do wyszukania w treści wiadomości"},
                "channel_name": {
                    "type": "string",
                    "description": "Nazwa kanału do przeszukania (bez #). Domyślnie bieżący kanał.",
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    ),
    "list_channels": FunctionDefinition(
        name="list_channels",
        description="Wyświetla listę wszystkich kanałów tekstowych na tym serwerze Discord z ich kategoriami i opisami.",
        parameters={
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    ),
    "list_members": FunctionDefinition(
        name="list_members",
        description="Wyświetla listę członków serwera Discord, opcjonalnie filtrując po roli.",
        parameters={
            "type": "object",
            "properties": {
                "role_name": {"type": "string", "description": "Nazwa roli do filtrowania (opcjonalnie)"},
            },
            "additionalProperties": False,
        },
    ),
    "get_channel_topic": FunctionDefinition(
        name="get_channel_topic",
        description="Sprawdza opis (topic) i kategorię kanału tekstowego na tym serwerze Discord.",
        parameters={
            "type": "object",
            "properties": {
                "channel_name": {"type": "string", "description": "Nazwa kanału (bez #)"},
            },
            "required": ["channel_name"],
            "additionalProperties": False,
        },
    ),
    "read_attachment": FunctionDefinition(
        name="read_attachment",
        description="Czyta zawartość załącznika z wiadomości na Discordzie (plik tekstowy, kod, JSON, obraz itp.) na podstawie jego URL.",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL załącznika z Discorda (z cdn.discordapp.com)"},
            },
            "required": ["url"],
            "additionalProperties": False,
        },
    ),
    "get_user_info": FunctionDefinition(
        name="get_user_info",
        description="Sprawdza informacje o użytkowniku na tym serwerze Discord: role, status, datę dołączenia, aktywność.",
        parameters={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Wzmianka użytkownika (np. <@123456>) lub jego numeryczne ID",
                },
            },
            "required": ["user_id"],
            "additionalProperties": False,
        },
    ),
}


class Chat(commands.Cog):
    RESET_PHRASE = "zaczynamy od nowa"
    ITERATION_LIMIT = 8
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

Masz bezpośredni dostęp do tego serwera Discord. Możesz czytać historię innych kanałów, szukać wiadomości, wysyłać wiadomości na inne kanały, przeglądać listę kanałów i członków, oraz sprawdzać informacje o użytkownikach i kanałach.
Korzystaj z narzędzi serwerowych gdy pytanie dotyczy serwera, kanałów, użytkowników, czy dyskusji na innych kanałach.
Możesz łączyć wiele narzędzi — np. przeczytać historię kanału i na jej podstawie wysłać podsumowanie na inny kanał.
Wiadomości zawierają metadane załączników (nazwa, typ, rozmiar, URL). Aby zobaczyć zawartość załącznika (tekst, kod, obraz), użyj narzędzia read_attachment z jego URL.

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
        for tool_def in DISCORD_TOOL_DEFINITIONS.values():
            tools.append(tool_def.model_dump())
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

    async def message_to_text(
        self, ctx: commands.Context, message: discord.Message, *, for_tool: bool = False
    ) -> Optional[str]:
        if not for_tool:
            if message.clean_content.strip().startswith(self.COMMENT_MARKER):
                return None
            if self.RESET_PHRASE in message.clean_content.lower():
                raise IndexError  # Conversation reset point
        parts: list[str] = []
        if reference := message.reference:
            reference_message: Optional[discord.Message] = None
            if reference.cached_message:
                reference_message = reference.cached_message
            else:
                channel = self.bot.get_channel(reference.channel_id)
                if channel is None:
                    try:
                        channel = await self.bot.fetch_channel(reference.channel_id)
                    except discord.HTTPException:
                        channel = None
                if channel is not None and reference.message_id is not None:
                    try:
                        reference_message = await channel.fetch_message(reference.message_id)
                    except (AttributeError, discord.NotFound):
                        pass
            if reference_message is not None:
                parts.append(
                    f'_W odpowiedzi na wiadomość użytkownika {reference_message.author.display_name} z {reference_message.created_at.strftime("%Y-%m-%d %H:%M:%S")} o treści "{reference_message.clean_content.strip()}"_'
                )
        if message.clean_content:
            parts.append(message.clean_content)
            if not for_tool:
                prefixes = await self.bot.get_prefix(message)
                for prefix in prefixes + [f"<@{message.guild.me.display_name}"]:
                    if parts[0].startswith(prefix):
                        parts[0] = parts[0][len(prefix) :].lstrip()
                        break
        if message.embeds:
            parts.append(await self.embeds_to_text(ctx, message.embeds))
        for attachment in message.attachments:
            ct = attachment.content_type or "unknown"
            parts.append(f"Załącznik: {attachment.filename} ({ct}, {attachment.size} B) — URL: {attachment.url}")
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
                                "type": "input_text" if m.author_display_name_with_id else "output_text",
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

        output_parts: list[str] = []
        math_operations: list[str] = []
        online_queries: list[str] = []
        resulted_in_command_message = False
        all_tools = self._all_available_commands_as_tools
        for iterations_left in range(self.ITERATION_LIMIT - 1, -1, -1):
            async with ctx.typing():
                response = await aclient.responses.create(
                    model="gpt-5.4",
                    input=prompt_messages,
                    user=str(ctx.author.id),
                    tools=all_tools if iterations_left else NOT_GIVEN,
                    store=False,
                    truncation="auto",
                )
                tool_calls = []
                for item in response.output:
                    if item.type == "function_call":
                        tool_calls.append(item)
                    elif item.type == "web_search_call" and "query" in item.action:
                        online_queries.append(item.action["query"])  # Website visits don't have a `query`
                if not tool_calls:
                    # LLM decided it's done
                    final_text = disembed_links(response.output_text.strip())
                    output_parts.append(final_text)
                    break

                # There are tool calls - collect any intermediate text
                if response.output_text:
                    output_parts.append(disembed_links(response.output_text.strip()))

                iteration_had_command_message = await self.process_tool_calls(
                    ctx,
                    prompt_messages,
                    output_parts,
                    math_operations,
                    iterations_left,
                    tool_calls,
                )
                if iteration_had_command_message:
                    resulted_in_command_message = True

        final_message = "\n".join(output_parts) if output_parts else "Nie udało mi się wykonać zadania. 😔"
        if online_queries:
            final_message += "\n-# Wyszukiwania: "
            final_message += ", ".join(online_queries)
        if math_operations:
            final_message += "\n-# Obliczenia: "
            final_message += ", ".join(f"`{operation}`" for operation in math_operations)

        await self.bot.send(ctx, final_message, reply=not resulted_in_command_message)

    async def process_tool_calls(
        self,
        ctx: commands.Context,
        prompt_messages: list,
        output_parts: list[str],
        math_operations: list[str],
        iterations_left: int,
        tool_calls: list[ResponseFunctionToolCall],
    ) -> bool:
        iteration_resulted_in_command_message = False
        for call in tool_calls:
            if call.name == CALCULATOR_FUNCTION_DEFINITION.name:
                resulting_message_content = self.execute_calculator(math_operations, prompt_messages, call)
            elif call.name in DISCORD_TOOL_DEFINITIONS:
                try:
                    args = json.loads(call.arguments)
                except json.JSONDecodeError:
                    resulting_message_content = "⚠️ Nieprawidłowe argumenty narzędzia"
                    prompt_messages.append({"role": "system", "content": resulting_message_content})
                    continue
                output_parts.append(self._discord_tool_human_description(call.name, args))
                prompt_messages.append(
                    {
                        "role": "assistant",
                        "content": f"Używam narzędzia {call.name}.",
                    }
                )
                resulting_message_content = await self._execute_discord_tool(ctx, prompt_messages, call.name, args)
            else:
                resulting_message_content, tool_call_resulted_in_command_message = await self.invoke_command(
                    ctx, prompt_messages, call
                )
                if tool_call_resulted_in_command_message:
                    iteration_resulted_in_command_message = True

            prompt_messages.append(
                {
                    "role": "system",
                    "content": "Narzędzie nie dało rezultatu."
                    if not resulting_message_content
                    else f"Rezultat narzędzia:\n{resulting_message_content}",
                }
            )
            prompt_messages.append(
                {
                    "role": "system",
                    "content": "Wystarczy już narzędzi, odpowiedz jak możesz."
                    if iterations_left == 1
                    else "Spróbuj ponownie naprawiając ten błąd."
                    if resulting_message_content and "⚠️" in str(resulting_message_content)
                    else "Kontynuuj. Jeśli powyższy wynik wystarczy do odpowiedzi, odpowiedz w swoim stylu. Jeśli nie, użyj kolejnych narzędzi. 😏",
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
        return f"Obliczono że {', '.join(f'`{result}`' for result in results)}. Wykorzystaj te wyniki do ostatecznej odpowiedzi. NIE LICZ TYCH WYRAŻEŃ PONOWNIE."

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
            return f"Komenda `{invoker}` nie istnieje.", False
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

    # Discord tool helpers

    def _resolve_channel(self, guild: discord.Guild, channel_ref: str) -> Optional[discord.TextChannel]:
        match = re.match(r"<#(\d+)>", channel_ref)
        if match:
            ch = guild.get_channel(int(match.group(1)))
            return ch if isinstance(ch, discord.TextChannel) else None
        return discord.utils.get(guild.text_channels, name=channel_ref.strip("#").strip())

    def _require_channel(
        self,
        ctx: commands.Context,
        channel_name: str,
        *,
        user_perms: Sequence[str] = ("view_channel",),
        bot_perms: Sequence[str] = (),
    ) -> discord.TextChannel:
        """Resolve a channel by name and check permissions. Raises ValueError with a user-facing message on failure."""
        channel = self._resolve_channel(ctx.guild, channel_name)
        if not channel:
            raise ValueError(f"⚠️ Nie znaleziono kanału o nazwie #{channel_name}")
        user_p = channel.permissions_for(ctx.author)
        for perm in user_perms:
            if not getattr(user_p, perm, False):
                raise ValueError(f"⚠️ Nie masz uprawnień do kanału #{channel.name}")
        bot_p = channel.permissions_for(ctx.guild.me)
        for perm in bot_perms:
            if not getattr(bot_p, perm, False):
                raise ValueError(f"⚠️ Nie mam uprawnień do kanału #{channel.name}")
        return channel

    def _resolve_member(self, guild: discord.Guild, user_ref: str) -> Optional[discord.Member]:
        match = re.match(r"<@!?(\d+)>", user_ref)
        if match:
            return guild.get_member(int(match.group(1)))
        try:
            return guild.get_member(int(user_ref.strip()))
        except ValueError:
            return discord.utils.get(guild.members, display_name=user_ref.strip())

    @staticmethod
    def _discord_tool_human_description(tool_name: str, args: dict) -> str:
        esc = discord.utils.escape_markdown
        if tool_name == "send_message_in_another_channel":
            return f"_Wysyła wiadomość na kanał #{esc(args['channel_name'])}…_"
        elif tool_name == "read_history_of_another_channel":
            return f"_Czyta historię kanału #{esc(args['channel_name'])}…_"
        elif tool_name == "search_messages":
            channel_part = f" na kanale #{esc(args['channel_name'])}" if args.get("channel_name") else ""
            return f'_Szuka wiadomości "{esc(args["query"])}"{channel_part}…_'
        elif tool_name == "list_channels":
            return "_Sprawdza listę kanałów…_"
        elif tool_name == "list_members":
            role_part = f" z rolą {esc(args['role_name'])}" if args.get("role_name") else ""
            return f"_Sprawdza listę członków{role_part}…_"
        elif tool_name == "get_channel_topic":
            return f"_Sprawdza opis kanału #{esc(args['channel_name'])}…_"
        elif tool_name == "read_attachment":
            filename = esc(args["url"].split("/")[-1]) if "/" in args.get("url", "") else ""
            return f"_Czyta załącznik {filename}…_"
        elif tool_name == "get_user_info":
            return f"_Sprawdza informacje o użytkowniku {esc(args['user_id'])}…_"
        return f"_{esc(tool_name)}…_"

    async def _execute_discord_tool(
        self, ctx: commands.Context, prompt_messages: list, tool_name: str, args: dict
    ) -> str:
        handler = {
            "send_message_in_another_channel": self._tool_send_message,
            "read_history_of_another_channel": self._tool_read_history,
            "search_messages": self._tool_search_messages,
            "list_channels": self._tool_list_channels,
            "list_members": self._tool_list_members,
            "get_channel_topic": self._tool_get_channel_topic,
            "read_attachment": self._tool_read_attachment,
            "get_user_info": self._tool_get_user_info,
        }.get(tool_name)
        if not handler:
            return f"⚠️ Nieznane narzędzie: {tool_name}"
        try:
            return await handler(ctx, prompt_messages, args)
        except ValueError as e:
            return str(e)
        except Exception as e:
            return f"⚠️ Błąd: {e}"

    async def _tool_send_message(self, ctx: commands.Context, _prompt_messages: list, args: dict) -> str:
        channel = self._require_channel(
            ctx,
            args["channel_name"],
            user_perms=("view_channel", "send_messages"),
            bot_perms=("send_messages",),
        )
        message_text = args["message"][:2000]
        await channel.send(message_text, allowed_mentions=discord.AllowedMentions.none())
        return f"Wysłano wiadomość na kanał #{channel.name}"

    async def _tool_read_history(self, ctx: commands.Context, _prompt_messages: list, args: dict) -> str:
        channel = self._require_channel(
            ctx,
            args["channel_name"],
            user_perms=("view_channel", "read_message_history"),
            bot_perms=("read_message_history",),
        )
        try:
            limit = min(int(args.get("limit", 20)), 50)
        except (ValueError, TypeError):
            limit = 20
        messages = []
        async for msg in channel.history(limit=limit):
            text = await self.message_to_text(ctx, msg, for_tool=True)
            if text:
                timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M")
                messages.append(f"[{timestamp}] {msg.author.display_name}: {text}")
        messages.reverse()
        return "\n".join(messages) if messages else f"Brak wiadomości na kanale #{channel.name}"

    async def _tool_search_messages(self, ctx: commands.Context, _prompt_messages: list, args: dict) -> str:
        query = args["query"].lower()
        channel_name = args.get("channel_name")
        if channel_name:
            search_channel = self._require_channel(
                ctx,
                channel_name,
                user_perms=("view_channel", "read_message_history"),
                bot_perms=("read_message_history",),
            )
        else:
            search_channel = ctx.channel
        results = []
        async for msg in search_channel.history(limit=200):
            text = await self.message_to_text(ctx, msg, for_tool=True) or ""
            if query in text.lower():
                timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M")
                results.append(f"[{timestamp} #{search_channel.name}] {msg.author.display_name}: {text}")
                if len(results) >= 15:
                    break
        results.reverse()
        if not results:
            return 'Nie znaleziono wiadomości zawierających "%s"' % args["query"]
        return "\n".join(results)

    async def _tool_list_channels(self, ctx: commands.Context, _prompt_messages: list, args: dict) -> str:
        lines = []
        for channel in ctx.guild.text_channels:
            if not channel.permissions_for(ctx.author).view_channel:
                continue
            category = f" [{channel.category.name}]" if channel.category else ""
            topic = f" — {channel.topic[:100]}" if channel.topic else ""
            lines.append(f"#{channel.name}{category}{topic}")
        return "\n".join(lines) if lines else "Brak kanałów tekstowych"

    async def _tool_list_members(self, ctx: commands.Context, _prompt_messages: list, args: dict) -> str:
        role_name = args.get("role_name")
        if role_name:
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if not role:
                return '⚠️ Nie znaleziono roli o nazwie "%s"' % role_name
            members = role.members
        else:
            members = ctx.guild.members
        lines = []
        for member in members[:50]:
            status = str(member.status)
            top_role = member.top_role.name if member.top_role != ctx.guild.default_role else ""
            role_info = f" ({top_role})" if top_role else ""
            lines.append(f"{member.display_name} <@{member.id}> — {status}{role_info}")
        count_note = f" (pokazuję pierwszych 50 z {len(members)})" if len(members) > 50 else ""
        header = f"Liczba członków: {len(members)}{count_note}"
        return header + "\n" + "\n".join(lines)

    async def _tool_get_channel_topic(self, ctx: commands.Context, _prompt_messages: list, args: dict) -> str:
        channel = self._require_channel(ctx, args["channel_name"])
        topic = channel.topic or "(brak opisu)"
        category = channel.category.name if channel.category else "(brak kategorii)"
        return f"Kanał: #{channel.name}\nKategoria: {category}\nOpis: {topic}"

    async def _tool_read_attachment(self, ctx: commands.Context, prompt_messages: list, args: dict) -> str:
        url = args["url"]
        if "cdn.discordapp.com" not in url and "media.discordapp.net" not in url:
            return "⚠️ URL musi być z cdn.discordapp.com lub media.discordapp.net"
        async with self.bot.session.get(url) as resp:
            if resp.status != 200:
                return f"⚠️ Nie udało się pobrać załącznika (HTTP {resp.status})"
            content_type = resp.content_type or ""
            if content_type.startswith("image/"):
                prompt_messages.append({"role": "user", "content": [{"type": "input_image", "image_url": url}]})
                return "Obraz załadowany do kontekstu — opisz go lub odpowiedz na pytanie dotyczące obrazu"
            data = await resp.read()
            if len(data) > TEXT_ATTACHMENT_MAX_SIZE:
                text = data[:TEXT_ATTACHMENT_MAX_SIZE].decode("utf-8", errors="replace")
                return f"Zawartość pliku (obcięto do {TEXT_ATTACHMENT_MAX_SIZE} B):\n{text}"
            return f"Zawartość pliku:\n{data.decode('utf-8', errors='replace')}"

    async def _tool_get_user_info(self, ctx: commands.Context, _prompt_messages: list, args: dict) -> str:
        member = self._resolve_member(ctx.guild, args["user_id"])
        if not member:
            return f"⚠️ Nie znaleziono użytkownika {args['user_id']}"
        roles = ", ".join(r.name for r in member.roles[1:]) if len(member.roles) > 1 else "brak"
        joined = member.joined_at.strftime("%Y-%m-%d %H:%M") if member.joined_at else "nieznana"
        created = member.created_at.strftime("%Y-%m-%d %H:%M")
        status = str(member.status)
        activity = str(member.activity) if member.activity else "brak"
        return (
            f"Użytkownik: {member.display_name} ({member.name}) <@{member.id}>\n"
            f"Status: {status}\n"
            f"Aktywność: {activity}\n"
            f"Dołączenie na serwer: {joined}\n"
            f"Konto utworzone: {created}\n"
            f"Role: {roles}"
        )

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
