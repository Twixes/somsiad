# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import os
import random
import json
import discord
from somsiad import somsiad


class Ball:
    with open(os.path.join(somsiad.bot_dir_path, 'data', 'eightball_answers.json')) as f:
        eightball_answers = json.load(f)

    categories = ['definitive' for _ in range(49)] + ['enigmatic']
    definitive_categories = ('affirmative', 'negative')

    @classmethod
    def ask(cls) -> str:
        category = random.choice(cls.categories)
        specific_category = 'enigmatic' if category == 'enigmatic' else random.choice(cls.definitive_categories)
        answer = random.choice(cls.eightball_answers[specific_category])
        return answer

    @classmethod
    def AsK(cls) -> str:
        aNSwEr = ''.join(random.choice([letter.lower(), letter.upper()]) for letter in cls.ask())
        return aNSwEr


@somsiad.command(aliases=['8ball', '8-ball', '8', 'czy'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def eightball(ctx, *, question: discord.ext.commands.clean_content(fix_channel_mentions=True) = ''):
    """Returns an 8-Ball answer."""
    stripped_question = question.strip('`~!@#$%^&*()-_=+[{]}\\|;:\'",<.>/?')
    if stripped_question == '':
        await ctx.send(
            f'{ctx.author.mention}\nMagiczna kula potrafi odpowiadać tylko na pytania! '
            'Aby zadać pytanie musisz użyć *słów*.'
        )
    else:
        if 'fccchk' in stripped_question.lower():
            await ctx.send(f'{ctx.author.mention}\n:japanese_goblin: {Ball.AsK()}')
        else:
            await ctx.send(f'{ctx.author.mention}\n:8ball: {Ball.ask()}')
