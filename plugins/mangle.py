# Copyright 2022 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import random
from secrets import choice
from typing import Optional, Tuple
from somsiad import Somsiad, SomsiadMixin
from discord.ext import commands
from core import cooldown


NEIGHBOR_LINES = ('1234567890-=', 'qwertyuiop[]', "asdfghjkl;'", 'zxcvbnm,./')
NEIGHBOR_LETTERS = ''.join(NEIGHBOR_LINES)
NEIGHBOR_SHIFT_LINES = ('!@#$%^&*()_+', "QWERTYUIOP{}", 'ASDFGHJKL:"', 'ZXCVBNM<>?')
NEIGHBOR_SHIFT_LETTERS = ''.join(NEIGHBOR_SHIFT_LINES)


def get_random_neighbor(key) -> str:
    relevant_lines: Tuple[str, str, str, str]
    if key in NEIGHBOR_LETTERS:
        relevant_lines = NEIGHBOR_LINES
    elif key in NEIGHBOR_SHIFT_LETTERS:
        relevant_lines = NEIGHBOR_SHIFT_LINES
    else:
        return key
    line_index, index = [(i, l.find(key)) for i, l in enumerate(relevant_lines) if key in l][0]
    lines = relevant_lines[line_index - 1 : line_index + 2] if line_index else relevant_lines[0:2]
    neighbors = [
        line[index + i]
        for line in lines
        for i in [-1, 0, 1]
        if len(line) > index + i and line[index + i] != key and index + i >= 0
    ]
    return choice(neighbors)


def shift_key(key: str) -> str:
    try:
        key_index = NEIGHBOR_LETTERS.index(key)
    except ValueError:
        try:
            key_index = NEIGHBOR_SHIFT_LETTERS.index(key)
        except ValueError:
            return key
        else:
            return NEIGHBOR_SHIFT_LETTERS[key_index]
    else:
        return NEIGHBOR_LETTERS[key_index]


POLISH_LETTER_TO_ASCII = {
    'ą': 'a',
    'ć': 'c',
    'ę': 'e',
    'ł': 'l',
    'ń': 'n',
    'ó': 'o',
    'ś': 's',
    'ż': 'z',
    'ź': 'z',
}

BASE_SWAP_RATE = 0.03
BASE_FORFEITURE_RATE = 0.12
BASE_TYPO_RATE = 0.12
BASE_SHIFT_RATE = 0.05


class Mangle(commands.Cog, SomsiadMixin):
    @commands.command(aliases=['magiel', 'magluj', 'kiwcio'])
    @cooldown()
    async def mangle(self, ctx: commands.Context, percentage: int, *, content: Optional[str] = None):
        if not content:
            async for message in ctx.history():
                if message != ctx.message and message.clean_content:
                    content = message.clean_content
                    break
        if not content:
            return await self.bot.send(ctx, 'Nie znaleziono tekstu do zkiwciowania!')
        working_content = list(content)
        swap_rate = percentage / 100 * BASE_SWAP_RATE
        forfeiture_rate = percentage / 100 * BASE_FORFEITURE_RATE
        typo_rate = percentage / 100 * BASE_TYPO_RATE
        shift_rate = percentage / 100 * BASE_SHIFT_RATE
        transformed_content = ''
        for i in range(len(working_content) - 1):
            if random.random() < swap_rate:
                # Oops, we swapped the letters!
                working_content[i], working_content[i + 1] = working_content[i + 1], working_content[i]
        for (index, letter) in enumerate(working_content):
            if random.random() < forfeiture_rate:
                continue  # Oops, we lost the letter!
            if letter in POLISH_LETTER_TO_ASCII:
                letter = POLISH_LETTER_TO_ASCII[letter]
            if random.random() < typo_rate:
                letter = get_random_neighbor(letter)  # Oops, we mangled the letter!
            if index > 0 and random.random() < shift_rate:
                letter = shift_key(letter)  # Oops, we shifted the letter!
            transformed_content += letter
        if not transformed_content:  # Make sure the returned string never is empty
            transformed_content = random.choice(content)
        await self.bot.send(ctx, transformed_content)


def setup(bot: Somsiad):
    bot.add_cog(Mangle(bot))
