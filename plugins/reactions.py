# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Optional
import discord
from somsiad import somsiad


class Reactor:
    """Handles reacting to messages."""
    ASCII_CHARACTERS_EMOJIS = {
        'a': '🇦', 'b': '🇧', 'c': '🇨', 'd': '🇩', 'e': '🇪', 'f': '🇫', 'g': '🇬', 'h': '🇭', 'i': '🇮', 'j': '🇯',
        'k': '🇰', 'l': '🇱', 'm': '🇲', 'n': '🇳', 'o': '🇴', 'p': '🇵', 'q': '🇶', 'r': '🇷', 's': '🇸', 't': '🇹',
        'u': '🇺', 'v': '🇻', 'w': '🇼', 'x': '🇽', 'y': '🇾', 'z': '🇿', '?': '❓', '!': '❗', '^': '⬆'
    }
    NON_ASCII_CHARACTERS_EMOJIS = {
        'ą': ['regional_indicator_an', '🇦'], 'ć': ['regional_indicator_ci', '🇨'],
        'ę': ['regional_indicator_en', '🇪'], 'ł': ['regional_indicator_ll', '🇱'],
        'ó': ['regional_indicator_oo', '🇴'], 'ś': ['regional_indicator_si', '🇸'],
        'ż': ['regional_indicator_zg', '🇿'], 'ź': ['regional_indicator_zi', '🇿']
    }

    @classmethod
    def clean_characters(cls, ctx: discord.ext.commands.Context, characters: str):
        """Cleans characters so that they are most suitable for use in reactions."""
        # initialization
        passes = [characters]
        # first pass: create a list of lowercase characters
        passes.append([])
        passes[1] = [character.lower() for character in characters]
        # second pass: convert ASCII characters to Unicode emojis
        passes.append([])
        for character in passes[1]:
            if character in cls.ASCII_CHARACTERS_EMOJIS:
                passes[2].append(cls.ASCII_CHARACTERS_EMOJIS[character])
            else:
                passes[2].append(character)
        # second pass: convert non-ASCII characters to server emojis or Unicode emojis
        passes.append([])
        for character in passes[2]:
            if character in cls.NON_ASCII_CHARACTERS_EMOJIS:
                was_matching_emoji_found = False
                for emoji in ctx.guild.emojis:
                    if not was_matching_emoji_found and emoji.name == cls.NON_ASCII_CHARACTERS_EMOJIS[character][0]:
                        passes[3].append(emoji)
                        was_matching_emoji_found = True
                if not was_matching_emoji_found:
                    passes[3].append(cls.NON_ASCII_CHARACTERS_EMOJIS[character][1])
            else:
                passes[3].append(character)
        # return the final pass
        return passes[-1]

    @classmethod
    async def react(cls, ctx: discord.ext.commands.Context, characters: str, member: discord.Member = None):
        """Adds provided emojis to the specified member's last non-command message in the form of reactions.
        If no member was specified, adds emojis to the last non-command message sent by any non-bot member
        in the given channel.
        """
        clean_characters = cls.clean_characters(ctx, characters)
        history = ctx.history(limit=15)
        if member is not None:
            async for message in history:
                if (
                    message.author == member
                    and not message.content.startswith(somsiad.conf['command_prefix'])
                ):
                    for reaction in clean_characters:
                        try:
                            await message.add_reaction(reaction)
                        except discord.HTTPException:
                            pass
                    break
        else:
            async for message in history:
                if (
                    not message.content.startswith(somsiad.conf['command_prefix'])
                ):
                    for reaction in clean_characters:
                        try:
                            await message.add_reaction(reaction)
                        except discord.HTTPException:
                            pass
                    break


@somsiad.bot.command(aliases=['zareaguj'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def react(ctx, member: Optional[discord.Member], *, characters: discord.ext.commands.clean_content):
    """Reacts with the provided characters."""
    await Reactor.react(ctx, characters, member)


@somsiad.bot.command(aliases=['pomógł', 'pomogl'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def helped(ctx, member: Optional[discord.Member]):
    """Reacts with "POMÓGŁ"."""
    await Reactor.react(ctx, 'pomógł', member)


@somsiad.bot.command(aliases=['niepomógł', 'niepomogl'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def didnothelp(ctx, member: Optional[discord.Member]):
    """Reacts with "NIEPOMÓGŁ"."""
    await Reactor.react(ctx, 'niepomógł', member)
