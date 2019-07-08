# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Optional, Sequence
import discord
from somsiad import somsiad


class Reactor:
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

    @classmethod
    def _convert_diacritic_character(cls, character: str, ctx: discord.ext.commands.Context = None) -> str:
        """Converts diacritic characters to server emojis or ASCII characters."""
        if character in cls.DIACRITIC_CHARACTERS:
            if ctx is not None:
                for emoji in ctx.guild.emojis:
                    if emoji.name == cls.DIACRITIC_CHARACTERS[character][0]:
                        return emoji
            return cls.DIACRITIC_CHARACTERS[character][1]
        else:
            return character

    @classmethod
    def _convert_ascii_character(cls, character: str, characters: Sequence[str] = '') -> str:
        """Converts ASCII characters to Unicode emojis."""
        if isinstance(character, str) and character in cls.ASCII_CHARACTERS:
            if cls.ASCII_CHARACTERS[character][0] not in characters:
                return cls.ASCII_CHARACTERS[character][0]
            elif (
                    len(cls.ASCII_CHARACTERS[character]) == 2
                    and cls.ASCII_CHARACTERS[character][1] not in characters
            ):
                return cls.ASCII_CHARACTERS[character][1]
            else:
                return ''
        else:
            return character

    @classmethod
    def _clean_characters(cls, ctx: discord.ext.commands.Context, characters: str):
        """Cleans characters so that they are most suitable for use in reactions."""
        # initialization
        passes = []
        # first pass: create a tuple of lowercase characters
        passes.append([])
        passes[-1] = (character.lower() for character in characters if character != ' ')
        # second pass: convert diacritic characters to server emojis or ASCII characters
        passes.append([])
        for character in passes[-2]:
            passes[-1].append(cls._convert_diacritic_character(character, ctx))
        # third pass: convert ASCII characters to Unicode emojis
        passes.append([])
        for character in passes[-2]:
            passes[-1].append(cls._convert_ascii_character(character, passes[-1]))
        # return the final pass
        return passes[-1]

    @classmethod
    async def react(cls, ctx: discord.ext.commands.Context, characters: str, member: discord.Member = None):
        """Converts the provided string to emojis and reacts with them."""
        clean_characters = cls._clean_characters(ctx, characters)
        await cls.raw_react(ctx, clean_characters, member)

    @classmethod
    async def raw_react(cls, ctx: discord.ext.commands.Context, characters: str, member: discord.Member = None):
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


@somsiad.bot.command(aliases=['zareaguj', 'x'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def react(
    ctx, member: Optional[discord.Member] = None, *,
    characters: discord.ext.commands.clean_content(fix_channel_mentions=True) = ''
):
    """Reacts with the provided characters."""
    await Reactor.react(ctx, characters, member)


@somsiad.bot.command(aliases=['pomógł', 'pomogl'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def helped(ctx, member: discord.Member = None):
    """Reacts with "POMÓGŁ"."""
    await Reactor.react(ctx, 'pomógł', member)


@somsiad.bot.command(aliases=['niepomógł', 'niepomogl'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def didnothelp(ctx, member: discord.Member = None):
    """Reacts with "NIEPOMÓGŁ"."""
    await Reactor.react(ctx, 'niepomógł', member)


@somsiad.bot.command(aliases=['^', 'to', 'up', 'upvote'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def this(ctx, member: discord.Member = None):
    """Reacts with "⬆"."""
    await Reactor.raw_react(ctx, '⬆', member)


@somsiad.bot.command(aliases=['hm', 'hmm', 'hmmm', 'hmmmm', 'hmmmmm', 'myśl', 'mysl', 'think', '🤔'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def thinking(ctx, member: discord.Member = None):
    """Reacts with "🤔"."""
    await Reactor.raw_react(ctx, '🤔', member)


@somsiad.bot.command()
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def f(ctx, member: discord.Member = None):
    """Reacts with "F"."""
    await Reactor.raw_react(ctx, '🇫', member)

@somsiad.bot.command(aliases=['chlip', '😢'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def sob(ctx, member: discord.Member = None):
    """Reacts with "😢"."""
    await Reactor.raw_react(ctx, '😢', member)
