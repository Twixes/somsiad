# Copyright 2019-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Optional
import aiohttp
import discord
from discord.ext import commands
from core import somsiad
from configuration import configuration


class Yandex:
    """Handles Yandex stuff."""
    FOOTER_TEXT = 'Yandex'
    FOOTER_ICON_URL = 'https://tech.yandex.com/favicon_en.ico'
    TRANSLATE_API_URL = 'https://translate.yandex.net/api/v1.5/tr.json/translate'

    @classmethod
    async def translate(cls, text: str, target_language_code: str, source_language_code: str = None) -> Optional[str]:
        """Translates text."""
        params = {
            'key': configuration['yandex_translate_key'],
            'text': text,
            'lang': target_language_code if source_language_code is None else f'{source_language_code}-{target_language_code}',
            'options': 1
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(cls.TRANSLATE_API_URL, headers=somsiad.HEADERS, params=params) as request:
                    return await request.json()
        except aiohttp.client_exceptions.ClientConnectorError:
            return None

    @classmethod
    async def translation_embed(cls, text: str, target_language_code: str, source_language_code: str) -> discord.Embed:
        """Generates an embed presenting the requested translation."""
        target_language_code = target_language_code.lower()
        target_language_display = target_language_code.upper()
        if source_language_code.strip('-_?') == '':
            source_language_code = None
            source_language_display = 'wykryj'
        else:
            source_language_code = source_language_code.lower()
            source_language_display = source_language_code.upper()

        translation = await Yandex.translate(text, target_language_code, source_language_code)

        if translation is None:
            embed = discord.Embed(
                title=f':warning: Nie udało się połączyć z serwerem tłumaczenia!',
                color=somsiad.COLOR
            )
        elif translation['code'] == 200:
            embed = discord.Embed(
                title=':globe_with_meridians: Przetłumaczono tekst',
                color=somsiad.COLOR
            )
            if source_language_code is None:
                source_language_display = f'{translation["detected"]["lang"].upper()} (wykryto)'
            embed.add_field(
                name=f'{source_language_display} → {target_language_display}',
                value=translation['text'][0]
            )
        elif translation['code'] == 422:
            embed = discord.Embed(
                title=':warning: Podany tekst jest nieprzetłumaczalny!',
                color=somsiad.COLOR
            )
        elif translation['code'] == 501 or translation['code'] == 502:
            embed = discord.Embed(
                title=f':warning: Podany kierunek tłumaczenia ({source_language_display} → {target_language_display}) '
                'nie jest obsługiwany!',
                color=somsiad.COLOR
            )
        else:
            embed = discord.Embed(
                title=':warning: Błąd',
                color=somsiad.COLOR
            )

        embed.set_footer(
            text=cls.FOOTER_TEXT,
            icon_url=cls.FOOTER_ICON_URL
        )

        return embed


@somsiad.command(aliases=['tłumacz', 'tlumacz', 'translator'])
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
)
async def translate(ctx, source_language_code, target_language_code, *, text):
    """The Wikipedia search command."""
    embed = await Yandex.translation_embed(text, target_language_code, source_language_code)
    await somsiad.send(ctx, embed=embed)


@translate.error
async def translate_error(ctx, error):
    print(error)
    embed = None
    if isinstance(error, commands.errors.MissingRequiredArgument):
        if error.param.name == 'source_language_code':
            embed = discord.Embed(
                title=':warning: Nie podano kodu języka źródłowego!',
                description='Przykłady: EN, JP, ?.\n'
                'Znak zapytania spowoduje wykrycie języka źródłowego.',
                color=somsiad.COLOR
            )
        elif error.param.name == 'target_language_code':
            embed = discord.Embed(
                title=':warning: Nie podano kodu języka docelowego!',
                description='Przykłady: PL, DE, RU.',
                color=somsiad.COLOR
            )
        elif error.param.name == 'text':
            embed = discord.Embed(
                title=':warning: Nie podano tekstu do przetłumaczenia!',
                color=somsiad.COLOR
            )
        embed.set_footer(
            text=Yandex.FOOTER_TEXT,
            icon_url=Yandex.FOOTER_ICON_URL
        )
        await somsiad.send(ctx, embed=embed)
