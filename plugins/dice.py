# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import random
from somsiad import Somsiad, SomsiadMixin

from discord.ext import commands

from core import cooldown


class Dice(commands.Cog, SomsiadMixin):
    @cooldown()
    @commands.command(aliases=['roll', 'rzuć', 'rzuc'])
    async def roll_dice(self, ctx, *, arguments=''):
        number_of_dice = 1
        number_of_sides_on_a_die = 6
        parts = arguments.lower().replace('-', '').replace('k', 'd').split()
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
                        number_of_sides_on_a_die = int(argument.lstrip('d'))
                    else:
                        number_of_dice = int(argument)
            elif len(parts) >= 2:
                # handle the arguments if there's 2 or more of them
                if parts[0].startswith('d'):
                    number_of_dice = int(parts[1])
                    number_of_sides_on_a_die = int(parts[0].lstrip('d'))
                else:
                    number_of_dice = int(parts[0])
                    number_of_sides_on_a_die = int(parts[1].lstrip('d'))
        except ValueError:
            raise commands.BadArgument
        if number_of_dice == 0:
            embed = self.bot.generate_embed('🎲', 'Nie rzucono kością')
        elif number_of_sides_on_a_die > 1:
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
                embed = self.bot.generate_embed('🎲', f'Rzucono {number_of_sides_description} kością', results_info)
            else:
                # convert results to strings and concatenate them
                results_string = ', '.join(list(map(str, results[:-1])))
                results_string = f'{results_string} i {results[-1]}'
                number_of_sides_description = (
                    'sześciennymi' if number_of_sides_on_a_die == 6 else f'{number_of_sides_on_a_die}-ściennymi'
                )
                results_info = f'Wypadło {results_string}.\nSuma tych liczb to {sum(results)}.'
                embed = self.bot.generate_embed(
                    '🎲', f'Rzucono {number_of_dice} {number_of_sides_description} koścmi', results_info
                )
        else:
            embed = self.bot.generate_embed('⚠️', f'{number_of_sides_on_a_die}-ścienna kość nie ma sensu')
        await self.bot.send(ctx, embed=embed)

    @roll_dice.error
    async def roll_dice_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = self.bot.generate_embed(
                '⚠️',
                f'Podano nieprawidłowy argument',
                'Ta komenda przyjmuje argumenty w formacie <?liczba kości> <?liczba ścianek kości>.',
            )
            await self.bot.send(ctx, embed=embed)


async def setup(bot: Somsiad):
    await bot.add_cog(Dice(bot))
