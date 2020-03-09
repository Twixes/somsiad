# Copyright 2018-2020 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from discord.ext import commands
from googleapiclient.errors import HttpError
from core import cooldown


class Google(commands.Cog):
    FOOTER_TEXT = 'Google'
    FOOTER_ICON_URL = 'https://www.google.com/favicon.ico'

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['g', 'gugiel'])
    @cooldown()
    @commands.guild_only()
    async def google(self, ctx, *, query='bot somsiad'):
        """Returns first matching website from Google using the provided Custom Search Engine."""
        try:
            result = await self.bot.google_client.search(query)
        except HttpError:
            embed = self.bot.generate_embed(
                '⚠️', 'Nie udało się połączyć z serwerem wyszukiwania',
                'Możliwe, że wyczerpał się dzienny limit wyszukiwań.'
            )
        else:
            if result is None:
                embed = self.bot.generate_embed('🙁', f'Brak wyników dla zapytania "{query}"')
            else:
                embed = self.bot.generate_embed(None, result.title, result.snippet, url=result.source_link)
                embed.set_author(name=result.display_link, url=result.root_link)
                if result.image_link is not None:
                    embed.set_image(url=result.image_link)
        embed.set_footer(text=self.bot.google_client.FOOTER_TEXT, icon_url=self.bot.google_client.FOOTER_ICON_URL)
        await self.bot.send(ctx, embed=embed)

    @commands.command(aliases=['googleimage', 'gi', 'i'])
    @cooldown()
    @commands.guild_only()
    async def google_image(self, ctx, *, query='bot somsiad'):
        """Returns first matching image from Google using the provided Custom Search Engine."""
        try:
            result = await self.bot.google_client.search(query, search_type='image')
        except HttpError:
            embed = self.bot.generate_embed(
                '⚠️', 'Nie udało się połączyć z serwerem wyszukiwania',
                'Możliwe, że wyczerpał się dzienny limit wyszukiwań.'
            )
        else:
            if result is None:
                embed = self.bot.generate_embed('🙁', f'Brak wyników dla zapytania "{query}"')
            else:
                embed = self.bot.generate_embed(None, result.title, url=result.source_link)
                embed.set_author(name=result.display_link, url=result.root_link)
                if result.image_link is not None:
                    embed.set_image(url=result.image_link)
        embed.set_footer(text=self.bot.google_client.FOOTER_TEXT, icon_url=self.bot.google_client.FOOTER_ICON_URL)
        await self.bot.send(ctx, embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Google(bot))
