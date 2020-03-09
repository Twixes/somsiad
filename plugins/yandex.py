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
from core import cooldown
from configuration import configuration


class Yandex(commands.Cog):
    """Handles Yandex stuff."""
    FOOTER_TEXT = 'Yandex'
    FOOTER_ICON_URL = 'https://tech.yandex.com/favicon_en.ico'
    TRANSLATE_API_URL = 'https://translate.yandex.net/api/v1.5/tr.json/translate'

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_translation(
            self, text: str, target_language_code: str, source_language_code: str = None
    ) -> Optional[str]:
        """Translates text."""
        if source_language_code is None:
            lang = target_language_code
        else:
            lang = f'{source_language_code}-{target_language_code}'
        params = {
            'key': configuration['yandex_translate_key'], 'text': text, 'lang': lang, 'options': 1
        }
        try:
            async with self.bot.session.get(self.TRANSLATE_API_URL, params=params) as request:
                return await request.json()
        except aiohttp.client_exceptions.ClientConnectorError:
            return None

    async def translation_embed(self, text: str, target_language_code: str, source_language_code: str) -> discord.Embed:
        """Generates an embed presenting the requested translation."""
        target_language_code = target_language_code.lower()
        target_language_display = target_language_code.upper()
        if source_language_code.strip('-_?') == '':
            source_language_code = None
            source_language_display = 'wykryj'
        else:
            source_language_code = source_language_code.lower()
            source_language_display = source_language_code.upper()
        translation = await self.fetch_translation(text, target_language_code, source_language_code)
        if translation is None:
            embed = self.bot.generate_embed('⚠️', 'Nie udało się połączyć z serwerem tłumaczenia')
        elif translation['code'] == 200:
            embed = self.bot.generate_embed('🌐', 'Przetłumaczono tekst')
            if source_language_code is None:
                source_language_display = f'{translation["detected"]["lang"].upper()} (wykryto)'
            embed.add_field(
                name=f'{source_language_display} → {target_language_display}',
                value=translation['text'][0]
            )
        elif translation['code'] == 422:
            embed = self.bot.generate_embed('🙁', 'Podany tekst jest nieprzetłumaczalny')
        elif translation['code'] == 501 or translation['code'] == 502:
            embed = self.bot.generate_embed(
                '🙁', f'Podany kierunek tłumaczenia ({source_language_display} → {target_language_display}) '
                'nie jest obsługiwany'
            )
        else:
            embed = self.bot.generate_embed('⚠️', 'Błąd')
        embed.set_footer(text=self.FOOTER_TEXT, icon_url=self.FOOTER_ICON_URL)
        return embed

    @commands.command(aliases=['tłumacz', 'tlumacz', 'translator'])
    @cooldown()
    async def translate(self, ctx, source_language_code, target_language_code, *, text):
        embed = await self.translation_embed(text, target_language_code, source_language_code)
        await self.bot.send(ctx, embed=embed)

    @translate.error
    async def translate_error(self, ctx, error):
        notice, description = None, None
        if isinstance(error, commands.errors.MissingRequiredArgument):
            if error.param.name == 'source_language_code':
                notice = 'Nie podano kodu języka źródłowego'
                description = 'Przykładowo: EN, JP, ?.\nZnak zapytania spowoduje wykrycie języka źródłowego.'
            elif error.param.name == 'target_language_code':
                notice = 'Nie podano kodu języka docelowego'
                description = 'Przykładowo: PL, DE, RU.'
            elif error.param.name == 'text':
                notice = 'Nie podano tekstu do przetłumaczenia'
        if notice is not None:
            embed = self.bot.generate_embed('⚠️', notice, description)
            embed.set_footer(text=self.FOOTER_TEXT, icon_url=self.FOOTER_ICON_URL)
            await self.bot.send(ctx, embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Yandex(bot))
