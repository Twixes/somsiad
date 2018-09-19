# Copyright 2018 Twixes

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


@somsiad.client.command(aliases=['choice', 'choose', 'wybierz'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def random_choice(ctx, *args):
    """Randomly chooses one of provided options."""
    options = [
        option.strip() for option in ' '.join(args).replace(' czy ', ',').replace(' or ', ',').split(',')
        if option.strip() != ''
    ]
    if len(options) <= 1:
        await ctx.send(
            f'{ctx.author.mention}\nChętnie pomógłbym z wyborem, ale musisz podać mi kilka oddzielonych '
            'przecinkami lub "czy" opcji!'
        )
    else:
        chosen_option = random.choice(options)
        chosen_answer = random.choice(choice_answers).replace('{}', f'"{chosen_option}"')
        await ctx.send(f'{ctx.author.mention}\n:point_right: {chosen_answer}')
