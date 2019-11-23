# Copyright 2018-2019 Twixes

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


with open(os.path.join(somsiad.bot_dir_path, 'data', 'choice_answers.json'), 'r') as f:
    choice_answers = json.load(f)

categories = ['definitive' for _ in range(49)] + ['enigmatic']

@somsiad.command(aliases=['choose', 'wybierz'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def random_choice(ctx, *, raw_options = ''):
    """Randomly chooses one of provided options."""
    raw_options = raw_options.replace(';', ',').replace('|', ',')
    options_words = []
    for word in raw_options.strip('?').split():
        if word.lower() in ('or', 'czy', 'albo', 'lub'):
            options_words.append(',')
        else:
            options_words.append(word)

    options = [option.strip() for option in ' '.join(options_words).split(',') if option.strip() != '']
    if len(options) >= 2:
        if 'trebuchet' in options:
            chosen_option = 'trebuchet'
        elif 'trebusz' in options:
            chosen_option = 'trebusz'
        elif 'trebuszet' in options:
            chosen_option = 'trebuszet'
        else:
            chosen_option = random.choice(options)
        category = random.choice(categories)
        answer = random.choice(choice_answers[category]).format(f':point_right: {chosen_option} :point_left:')
        await ctx.send(f'{ctx.author.mention}\n{answer}')
    else:
        await ctx.send(
            f'{ctx.author.mention}\nChętnie pomógłbym z wyborem, ale musisz podać mi kilka oddzielonych '
            'przecinkami, średnikami, "lub", "albo" lub "czy" opcji!'
        )
