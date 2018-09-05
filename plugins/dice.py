# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import random
import discord
from somsiad import somsiad


@somsiad.client.command(aliases=['rzuć', 'rzuc'])
@discord.ext.commands.cooldown(1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user)
@discord.ext.commands.guild_only()
async def roll(ctx, *args):
    number_of_dice = 1
    number_of_sides_on_a_die = 6

    if len(args) == 1:
        if len(args[0].lower().split('d')) >= 2 and args[0].lower().split('d')[0] != '':
            # Handle the argument if it's in the format {number_of_dice}d{number_of_sides_on_a_die}
            argument = args[0].lower().split('d')
            number_of_dice = int(argument[0])
            number_of_sides_on_a_die = int(argument[1])
        else:
            # Handle the argument if only either number_of_dice or number_of_sides_on_a_die were given
            if args[0].lower().startswith('d'):
                number_of_sides_on_a_die = int(args[0].strip('dD'))
            else:
                number_of_dice = int(args[0])
    elif args:
        if args[0].lower().startswith('d'):
            number_of_dice = int(args[1])
            number_of_sides_on_a_die = int(args[0].strip('dD'))
        else:
            number_of_dice = int(args[0])
            number_of_sides_on_a_die = int(args[1].strip('dD'))

    if number_of_sides_on_a_die > 1:
        # Limit the number of dice to between 1 and 100 (including 1 and 100)
        if number_of_dice > 100:
            number_of_dice = 100
        elif number_of_dice < 1:
            number_of_dice = 1
        # Generate random results
        results = []
        for _ in range(number_of_dice):
            result = random.randint(1, number_of_sides_on_a_die)
            results.append(result)
        # Send the results
        if number_of_dice == 1:
            await ctx.send(
                f':game_die: Rzucono {number_of_sides_on_a_die}-ścienną kością. Wypadło {results[0]}.'
            )
        else:
            results_string = ', '.join(list(map(str, results[:-1]))) # converts items in the results list to str
            results_string += f' i {results[-1]}'
            await ctx.send(
                f':game_die: Rzucono {number_of_dice} {number_of_sides_on_a_die}-ściennymi koścmi. '
                f'Wypadło {results_string}. Suma tych liczb to {sum(results)}.'
            )
    else:
        await ctx.send(
            f'{ctx.author.mention}\n:game_die: {number_of_sides_on_a_die}-ścienna kość nie ma sensu!'
        )
