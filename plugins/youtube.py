# Copyright 2018-2020 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from discord.ext import commands
from core import cooldown
from utilities import HttpError


class YouTube(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['youtube', 'yt', 'tuba'])
    @cooldown()
    @commands.guild_only()
    async def youtube_search(self, ctx, *, query = None):
        """Returns first matching result from YouTube."""
        if query is None:
            result_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        else:
            try:
                result = await self.bot.youtube_client.search(query)
            except HttpError as e:
                if e.resp.status == 403:
                    embed = self.bot.generate_embed('⚠️', 'Wyczerpał się dzienny limit wyszukiwań', 'Reset rano.')
                    embed.set_footer(
                        icon_url=self.bot.youtube_client.FOOTER_ICON_URL, text=self.bot.youtube_client.FOOTER_TEXT
                    )
                    return await self.bot.send(ctx, embed=embed)
                raise e
            else:
                result_url = result.url if result is not None else None
        if result_url is not None:
            return await self.bot.send(ctx, result_url)
        else:
            embed = self.bot.generate_embed('🙁', f'Brak wyników dla zapytania "{query}"')
            embed.set_footer(icon_url=self.bot.youtube_client.FOOTER_ICON_URL, text=self.bot.youtube_client.FOOTER_TEXT)
            return await self.bot.send(ctx, embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(YouTube(bot))
