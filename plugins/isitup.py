# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import aiohttp
from discord.ext import commands
from utilities import first_url, md_link
from core import cooldown
from configuration import configuration


class IsItUp(commands.Cog):
    HTTP_CODE_WIKIPEDIA_URLS = {
        1:'https://pl.wikipedia.org/wiki/Kod_odpowiedzi_HTTP#Kody_informacyjne',
        2:'https://pl.wikipedia.org/wiki/Kod_odpowiedzi_HTTP#Kody_powodzenia',
        3:'https://pl.wikipedia.org/wiki/Kod_odpowiedzi_HTTP#Kody_przekierowania',
        4:'https://pl.wikipedia.org/wiki/Kod_odpowiedzi_HTTP#Kody_błędu_aplikacji_klienta',
        5:'https://pl.wikipedia.org/wiki/Kod_odpowiedzi_HTTP#Kody_błędu_serwera_HTTP'
    }

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=('isup', 'czydziała', 'czydziala'))
    @cooldown()
    async def isitup(self, ctx, *, query='https://google.com'):
        """Returns information about website status."""
        async with ctx.typing():
            protocol, rest = first_url(query, protocol_separate=True)
            url_valid = rest is not None and protocol in (None, 'http', 'https')
            status = None
            if url_valid:
                protocol = protocol or 'https'
                url = f'{protocol}://{rest}'
                async with aiohttp.ClientSession() as session:
                    try:
                        for method in (session.head, session.get):
                            async with method(url, allow_redirects=True, headers=self.bot.HEADERS) as request:
                                if request.status == 405 and request.method != 'get':
                                    continue
                                status = request.status
                    except aiohttp.InvalidURL:
                        url_valid = False
                    except aiohttp.ClientConnectorError:
                        pass
            if url_valid:
                if status is not None and status // 100 == 2:
                    emoji, notice = '✅', f'Strona {rest} jest dostępna'
                else:
                    emoji, notice = '🔴', f'Strona {rest} nie jest dostępna'
                if status is not None:
                    status_presentation = md_link(status, self.HTTP_CODE_WIKIPEDIA_URLS[status // 100])
                else:
                    status_presentation = 'brak odpowiedzi'
                embed = self.bot.generate_embed(emoji, notice, url=url)
                embed.add_field(name='Status',value=status_presentation)
            else:
                embed = self.bot.generate_embed('⚠️', 'Podany adres jest niepoprawny')
            await self.bot.send(ctx, embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(IsItUp(bot))
