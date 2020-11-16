# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import itertools
import random
import re
from typing import Optional, Tuple, Union

import discord
from discord.ext import commands

from core import cooldown


class React(commands.Cog):
    """Handles reacting to messages."""

    DIACRITIC_CONVERSIONS = {
        'ą': ('aw', 'a'),
        'ć': ('ci', 'c'),
        'ę': ('ew', 'e'),
        'ń': ('ni', 'n'),
        'ł': ('el', 'l'),
        'ó': ('oo', 'o'),
        'ś': ('si', 's'),
        'ż': ('zg', 'z'),
        'ź': ('zi', 'z'),
    }
    EMOJIS = [
        {
            '0': '0️⃣',
            '1': '1⃣',
            '2': '2⃣',
            '3': '3⃣',
            '4': '4️⃣',
            '5': '5️⃣',
            '6': '6️⃣',
            '7': '7️⃣',
            '8': '8️⃣',
            '9': '9️⃣',
            'a': '🇦🅰',
            'b': '🇧🅱',
            'c': '🇨©️',
            'd': '🇩',
            'e': '🇪',
            'f': '🇫',
            'g': '🇬',
            'h': '🇭',
            'i': '🇮ℹ️',
            'j': '🇯',
            'k': '🇰',
            'l': '🇱',
            'm': '🇲Ⓜ️',
            'n': '🇳🆕',
            'o': '🇴🅾⭕️',
            'p': '🇵🅿️',
            'q': '🇶',
            'r': '🇷®️',
            's': '🇸',
            't': '🇹',
            'u': '🇺',
            'v': '🇻',
            'w': '🇼',
            'x': '🇽❌',
            'y': '🇾',
            'z': '🇿💤',
            '?': '❓',
            '!': '❗',
            '^': '⬆',
            '>': '▶',
            '<': '◀',
        },
        {
            '!!': '‼️',
            '!?': '⁉️',
            'ng': '🆖',
            'ok': '🆗',
            'up': '🆙',
            'wc': '🚾',
            'ab': '🆎',
            'cl': '🆑',
            'vs': '🆚',
            'id': '🆔',
            '10': '🔟',
            'tm': '™️',
        },
        {'sos': '🆘', '100': '💯', 'zzz': '💤', 'atm': '🏧', 'abc': '🔤', 'up!': '🆙', 'new': '🆕'},
        {'abcd': '🔠🔡', 'cool': '🆒', 'free': '🆓', '1234': '🔢'},
    ]
    CUSTOM_EMOJI_REGEX = re.compile(r'<:\S+?:(\d+)>')

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _convert_string(
        self, string: str, message: discord.Message, server: discord.Guild
    ) -> Tuple[Union[str, discord.Emoji]]:
        """Converts message content string to emojis."""
        emojis = list(' '.join(filter(None, string.lower().split())))
        used_emojis = {reaction.emoji for reaction in message.reactions if reaction.me}
        for match in reversed(tuple(self.CUSTOM_EMOJI_REGEX.finditer(string))):
            emoji = self.bot.get_emoji(int(match.groups()[0]))
            if emoji is not None and emoji not in used_emojis:
                emojis = emojis[: match.start()] + [emoji] + emojis[match.end() :]
                used_emojis.add(emoji)
            else:
                emojis = emojis[: match.start()] + emojis[match.end() :]
        diacritic_replacements = {}
        for i, character in enumerate(emojis):
            if len(used_emojis) >= 20:
                break
            if character is None or not isinstance(character, str):
                continue
            if character == ' ':
                while True:
                    random_emoji = random.choice(self.bot.EMOJIS)
                    if random_emoji not in used_emojis:
                        break
                emojis[i] = random_emoji
                used_emojis.add(random_emoji)
                continue
            if character in self.DIACRITIC_CONVERSIONS:
                if diacritic_replacements.get(character) is None:
                    valid_emoji_names = (
                        self.DIACRITIC_CONVERSIONS[character][0][-2:],
                        self.DIACRITIC_CONVERSIONS[character][0],
                    )
                    for emoji in server.emojis:
                        if emoji.name.lower() in valid_emoji_names:
                            diacritic_replacements[character] = emoji
                            break
                    else:
                        diacritic_replacements[character] = self.DIACRITIC_CONVERSIONS[character][1]
                emojis[i] = diacritic_replacements[character]
            was_emoji_found = False
            for extra_length, group_emojis in reversed(tuple(enumerate(self.EMOJIS, 1))):
                group = emojis[i]
                try:
                    for extra_i in range(1, extra_length):
                        group += emojis[i + extra_i]
                except (IndexError, TypeError):
                    continue
                else:
                    for emoji in group_emojis.get(group, ''):
                        if emoji and emoji not in used_emojis:
                            emojis[i] = emoji
                            for extra_i in range(1, extra_length):
                                emojis[i + extra_i] = None
                            used_emojis.add(emoji)
                            was_emoji_found = True
                            break
                    if was_emoji_found:
                        break
        unique_emojis = tuple(itertools.islice(filter(None, emojis), 20))
        return unique_emojis

    async def _find_message(self, ctx: commands.Context, member: discord.Member = None) -> discord.Message:
        """Finds specified member's last non-command message.
        If no member was specified, adds emojis to the last non-command message sent in the given channel.
        """
        if member is not None and member != ctx.author:
            async for message in ctx.history(limit=15):
                if message.author == member:
                    return message
        else:
            messages = await ctx.history(limit=2).flatten()
            if len(messages) > 1:
                return messages[1]
        return None

    async def _react(
        self, ctx: commands.Context, characters: str, member: discord.Member = None, *, convert: bool = True
    ):
        """Converts the provided string to emojis and reacts with them."""
        message = await self._find_message(ctx, member)
        if message is None:
            return
        emojis = self._convert_string(characters, message, ctx.guild) if convert else characters
        for emoji in emojis:
            try:
                await message.add_reaction(emoji)
            except discord.HTTPException:
                pass

    @commands.command(aliases=['zareaguj', 'reaguj', 'x'])
    @cooldown()
    @commands.guild_only()
    async def react(
        self,
        ctx,
        member: Optional[discord.Member] = None,
        *,
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
        await self._react(ctx, '⬆', member, convert=False)

    @commands.command(aliases=['down'])
    @cooldown()
    @commands.guild_only()
    async def downvote(self, ctx, member: discord.Member = None):
        """Reacts with "⬇"."""
        await self._react(ctx, '⬇', member, convert=False)

    @commands.command(aliases=['hm', 'hmm', 'hmmm', 'hmmmm', 'hmmmmm', 'myśl', 'mysl', 'think', '🤔'])
    @cooldown()
    @commands.guild_only()
    async def thinking(self, ctx, member: discord.Member = None):
        """Reacts with "🤔"."""
        await self._react(ctx, '🤔', member, convert=False)

    @commands.command()
    @cooldown()
    @commands.guild_only()
    async def f(self, ctx, member: discord.Member = None):
        """Reacts with "F"."""
        await self._react(ctx, '🇫', member, convert=False)

    @commands.command(aliases=['chlip', '😢'])
    @cooldown()
    @commands.guild_only()
    async def sob(self, ctx, member: discord.Member = None):
        """Reacts with "😢"."""
        await self._react(ctx, '😢', member, convert=False)


def setup(bot: commands.Bot):
    bot.add_cog(React(bot))
