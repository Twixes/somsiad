# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Optional, Sequence
import random
import discord
from discord.ext import commands
from core import cooldown
from configuration import configuration


class React(commands.Cog):
    """Handles reacting to messages."""
    DIACRITIC_CHARACTERS = {
        'ą': ('regional_indicator_aw', 'a'), 'ć': ('regional_indicator_ci', 'c'),
        'ę': ('regional_indicator_ew', 'e'), 'ł': ('regional_indicator_el', 'l'),
        'ó': ('regional_indicator_oo', 'o'), 'ś': ('regional_indicator_si', 's'),
        'ż': ('regional_indicator_zg', 'z'), 'ź': ('regional_indicator_zi', 'z')
    }
    ASCII_CHARACTERS = {
        '0': ('0️⃣',), '1': ('1⃣',), '2': ('2⃣',), '3': ('3⃣',), '4': ('4️⃣',), '5': ('5️⃣',), '6': ('6️⃣',),
        '7': ('7️⃣',), '8': ('8️⃣',), '9': ('9️⃣',), 'a': ('🇦', '🅰'), 'b': ('🇧', '🅱'), 'c': ('🇨',), 'd': ('🇩',),
        'e': ('🇪',), 'f': ('🇫',), 'g': ('🇬',), 'h': ('🇭',), 'i': ('🇮',), 'j': ('🇯',), 'k': ('🇰',), 'l': ('🇱',),
        'm': ('🇲',), 'n': ('🇳',), 'o': ('🇴', '🅾'), 'p': ('🇵',), 'q': ('🇶',), 'r': ('🇷',), 's': ('🇸',),
        't': ('🇹',), 'u': ('🇺',), 'v': ('🇻',), 'w': ('🇼',), 'x': ('🇽',), 'y': ('🇾',), 'z': ('🇿',), '?': ('❓',),
        '!': ('❗',), '^': ('⬆',), '>': ('▶',), '<': ('◀',)
    }

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _convert_diacritic_character(self, character: str, ctx: commands.Context = None) -> str:
        """Converts diacritic characters to server emojis or ASCII characters."""
        if character in self.DIACRITIC_CHARACTERS:
            if ctx is not None:
                for emoji in ctx.guild.emojis:
                    if emoji.name == self.DIACRITIC_CHARACTERS[character][0]:
                        return emoji
            return self.DIACRITIC_CHARACTERS[character][1]
        else:
            return character

    def _convert_ascii_character(self, character: str, characters: Sequence[str] = '') -> str:
        """Converts ASCII characters to Unicode emojis."""
        if character == ' ':
            return random.choice(self.bot.EMOJIS)
        elif isinstance(character, str) and character in self.ASCII_CHARACTERS:
            if self.ASCII_CHARACTERS[character][0] not in characters:
                return self.ASCII_CHARACTERS[character][0]
            elif (
                    len(self.ASCII_CHARACTERS[character]) == 2
                    and self.ASCII_CHARACTERS[character][1] not in characters
            ):
                return self.ASCII_CHARACTERS[character][1]
            else:
                return ''
        else:
            return character

    def _clean_characters(self, ctx: commands.Context, characters: str):
        """Cleans characters so that they are most suitable for use in reactions."""
        # initialization
        passes = []
        # first pass: create a tuple of lowercase characters
        passes.append([])
        passes[-1] = (character.lower() for character in ' '.join(characters.split()))
        # second pass: convert diacritic characters to server emojis or ASCII characters
        passes.append([])
        for character in passes[-2]:
            passes[-1].append(self._convert_diacritic_character(character, ctx))
        # third pass: convert ASCII characters to Unicode emojis
        passes.append([])
        for character in passes[-2]:
            passes[-1].append(self._convert_ascii_character(character, passes[-1]))
        # return the final pass
        return passes[-1]

    async def _react(self, ctx: commands.Context, characters: str, member: discord.Member = None):
        """Converts the provided string to emojis and reacts with them."""
        clean_characters = self._clean_characters(ctx, characters)
        await self._raw_react(ctx, clean_characters, member)

    async def _raw_react(self, ctx: commands.Context, characters: str, member: discord.Member = None):
        """Adds provided emojis to the specified member's last non-command message in the form of reactions.
        If no member was specified, adds emojis to the last non-command message sent in the given channel.
        """
        if member is not None and member != ctx.author:
            async for message in ctx.history(limit=15):
                if message.author == member:
                    for reaction in characters:
                        try:
                            await message.add_reaction(reaction)
                        except discord.HTTPException:
                            pass
                    break
        else:
            messages = await ctx.history(limit=2).flatten()
            for reaction in characters:
                try:
                    await messages[1].add_reaction(reaction)
                except discord.HTTPException:
                    pass

    @commands.command(aliases=['zareaguj', 'x'])
    @cooldown()
    @commands.guild_only()
    async def react(
        self, ctx, member: Optional[discord.Member] = None, *,
        characters: commands.clean_content(fix_channel_mentions=True) = ''
    ):
        """Reacts with the provided characters."""
        await self._react(ctx, characters, member)

    @commands.command(aliases=['pomógł', 'pomogl'])
    @cooldown()
    @commands.guild_only()
    async def helped(self, ctx, member: discord.Member = None):
        """Reacts with "POMÓGŁ"."""
        await self._react(ctx, 'pomógł', member)

    @commands.command(aliases=['niepomógł', 'niepomogl'])
    @cooldown()
    @commands.guild_only()
    async def didnothelp(self, ctx, member: discord.Member = None):
        """Reacts with "NIEPOMÓGŁ"."""
        await self._react(ctx, 'niepomógł', member)

    @commands.command(aliases=['up', 'this', 'to', '^'])
    @cooldown()
    @commands.guild_only()
    async def upvote(self, ctx, member: discord.Member = None):
        """Reacts with "⬆"."""
        await self._raw_react(ctx, '⬆', member)

    @commands.command(aliases=['down'])
    @cooldown()
    @commands.guild_only()
    async def downvote(self, ctx, member: discord.Member = None):
        """Reacts with "⬇"."""
        await self._raw_react(ctx, '⬇', member)

    @commands.command(aliases=['hm', 'hmm', 'hmmm', 'hmmmm', 'hmmmmm', 'myśl', 'mysl', 'think', '🤔'])
    @cooldown()
    @commands.guild_only()
    async def thinking(self, ctx, member: discord.Member = None):
        """Reacts with "🤔"."""
        await self._raw_react(ctx, '🤔', member)

    @commands.command()
    @cooldown()
    @commands.guild_only()
    async def f(self, ctx, member: discord.Member = None):
        """Reacts with "F"."""
        await self._raw_react(ctx, '🇫', member)

    @commands.command(aliases=['chlip', '😢'])
    @cooldown()
    @commands.guild_only()
    async def sob(self, ctx, member: discord.Member = None):
        """Reacts with "😢"."""
        await self._raw_react(ctx, '😢', member)


def setup(bot: commands.Bot):
    bot.add_cog(React(bot))
