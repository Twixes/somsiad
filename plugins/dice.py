# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import random
import discord
from discord.ext import commands
from core import cooldown
from configuration import configuration


class Dice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['roll', 'rzuć', 'rzuc'])
    @cooldown()
    async def roll_dice(self, ctx, arguments):
        number_of_dice = 1
        number_of_sides_on_a_die = 6
        parts = arguments.lower().replace('k', 'd').split()
        try:
            if len(parts) == 1:
                argument = parts[0]
                if len(parts[0].split('d')) >= 2 and parts[0].split('d')[0] != '':
                    # handle the argument if it's in the format {number_of_dice}d{number_of_sides_on_a_die}
                    argument = parts[0].split('d')
                    number_of_dice = int(argument[0])
                    number_of_sides_on_a_die = int(argument[1])
                else:
                    # handle the argument if only either number_of_dice or number_of_sides_on_a_die were given
                    if argument.startswith('d'):
                        number_of_sides_on_a_die = abs(int(argument.lstrip('d')))
                    else:
                        number_of_dice = abs(int(argument))
            elif len(parts) >= 2:
                # handle the arguments if there's 2 or more of them
                if parts[0].startswith('d'):
                    number_of_dice = abs(int(parts[1]))
                    number_of_sides_on_a_die = abs(int(parts[0].lstrip('d')))
                else:
                    number_of_dice = abs(int(parts[0]))
                    number_of_sides_on_a_die = abs(int(parts[1].lstrip('d')))
        except ValueError:
            raise commands.BadArgument

        if number_of_sides_on_a_die > 1:
            # limit the number of dice to 100 or less
            number_of_dice = min(number_of_dice, 100)
            # limit the number of sides on a die to 100 million or less
            number_of_sides_on_a_die = min(number_of_sides_on_a_die, 100000000)
            # generate random results
            results = [random.randint(1, number_of_sides_on_a_die) for _ in range(number_of_dice)]
            # send the results
            if number_of_dice == 1:
                number_of_sides_description = (
                    'sześcienną' if number_of_sides_on_a_die == 6 else f'{number_of_sides_on_a_die}-ścienną'
                )
                results_info = f'Wypadło {results[0]}.'
                embed = discord.Embed(
                    title=f':game_die: Rzucono {number_of_sides_description} kością',
                    description=results_info,
                    color=self.bot.COLOR
                )
            else:
                # convert results to strings and concatenate them
                results_string = ', '.join(list(map(str, results[:-1])))
                results_string = f'{results_string} i {results[-1]}'
                number_of_sides_description = (
                    'sześciennymi' if number_of_sides_on_a_die == 6 else f'{number_of_sides_on_a_die}-ściennymi'
                )
                results_info = f'Wypadło {results_string}.\nSuma tych liczb to {sum(results)}.'
                embed = discord.Embed(
                    title=f':game_die: Rzucono {number_of_dice} {number_of_sides_description} koścmi',
                    description=results_info,
                    color=self.bot.COLOR
                )
        else:
            embed = discord.Embed(
                title=f':warning: {number_of_sides_on_a_die}-ścienna kość nie ma sensu!',
                color=self.bot.COLOR
            )

        await self.bot.send(ctx, embed=embed)


    @roll_dice.error
    async def roll_dice_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title=':warning: Podano nieprawidłowy argument!',
                description='Ta komenda przyjmuje argumenty w formacie <?liczba kości> <?liczba ścianek kości>.',
                color=self.bot.COLOR
            )

            await self.bot.send(ctx, embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Dice(bot))
