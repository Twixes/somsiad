# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import os
import secrets
import discord
from somsiad import somsiad


with open(os.path.join(somsiad.bot_dir_path, 'data', 'eightball_answers.txt')) as f:
    eightball_answers = [line.strip() for line in f.readlines() if not line.strip().startswith('#')]


@somsiad.client.command(aliases=['8ball', '8-ball', '8', 'czy'])
@discord.ext.commands.cooldown(1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user)
@discord.ext.commands.guild_only()
async def eightball(ctx, *args):
    """Returns an 8-Ball answer."""
    question = ' '.join(args)
    question = question.strip('`~!@#$%^&*()-_=+[{]}\\|;:\'",<.>/?')
    if question != '':
        question = question.strip('?')
        if 'fccchk' in question.lower():
            answer = secrets.choice(eightball_answers)
            aNSwEr = ''.join(secrets.choice([letter.lower(), letter.upper()]) for letter in answer)
            await ctx.send(f'{ctx.author.mention}\n:japanese_goblin: {aNSwEr}')
        elif question != '':
            answer = secrets.choice(eightball_answers)
            await ctx.send(f'{ctx.author.mention}\n:8ball: {answer}')
    else:
        await ctx.send(f'{ctx.author.mention}\nMagiczna kula potrafi odpowiadać tylko na pytania! '
            'Aby zadać pytanie musisz użyć *słów*.')
