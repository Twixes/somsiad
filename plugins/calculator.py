# Copyright 2018-2019 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import string
from py_expression_eval import Parser
import discord
from core import somsiad
from utilities import TextFormatter
from configuration import configuration


parser = Parser()
input_data_strip_chars = string.whitespace + ';'

previous_expressions = {}

@somsiad.command(aliases=['oblicz', 'policz'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def calculate(ctx, *, data):
    """Calculates the provided expressions and sends the results.
    If calculation is not possible with available data, simplifies the expression.
    """
    input_data = [part.strip() for part in data.strip(input_data_strip_chars).replace('\\', '').split(';')]
    expression = None
    variables_list = None
    used_previous_expression = False
    try:
        expression = [input_data[0], parser.parse(input_data[0])]
    except Exception:
        try:
            if '=' not in input_data[0]:
                raise ValueError
            expression = previous_expressions[ctx.channel.id][ctx.author.id]
        except (ValueError, KeyError):
            embed = discord.Embed(
                title=':warning: Błąd w wyrażeniu!',
                color=somsiad.COLOR
            )
        else:
            used_previous_expression = True
            variables_list = input_data
    else:
        variables_list = input_data[1:]
        if ctx.channel.id not in previous_expressions:
            previous_expressions[ctx.channel.id] = {}
        previous_expressions[ctx.channel.id][ctx.author.id] = expression

    roundDigits = None
    variables_dict = {}
    if variables_list:
        try:
            roundDigits = int(variables_list[-1])
        except ValueError:
            pass
        else:
            variables_list.pop()

        for variable in variables_list:
            key_value_pair = variable.split('=')
            try:
                key = key_value_pair[0].strip()
                variables_dict[key] = float(key_value_pair[1].strip())
                if int(variables_dict[key]) == variables_dict[key]:
                    variables_dict[key] = int(variables_dict[key])
            except (IndexError, ValueError):
                embed = discord.Embed(
                    title=f':warning: Błąd w zmiennej `{variable}`!',
                    color=somsiad.COLOR
                )
                return await ctx.send(ctx.author.mention, embed=embed)

    if expression is not None:
        input_info = '\n'.join(
            [expression[0]] +
            [f'{variable[0]} = {variable[1]}' for variable in variables_dict.items()]
        )
        try:
            result = expression[1].evaluate(variables_dict)
        except Exception:
            try:
                result = expression[1].simplify(variables_dict).toString()
            except Exception:
                embed = discord.Embed(
                    title=':warning: Błąd w wyrażeniu lub zmiennych!',
                    color=somsiad.COLOR
                )
            else:
                embed = discord.Embed(
                    title=':1234: Uproszczono wyrażenie',
                    color=somsiad.COLOR
                )
                embed.add_field(name='Wejście', value=f'```Matlab\n{input_info}```', inline=False)
                embed.add_field(name='Wyjście', value=f'```Matlab\n{result}```', inline=False)
        else:
            input_details = 'Wejście (zastosowano poprzednie wyrażenie)' if used_previous_expression else 'Wejście'

            output_details = 'Wyjście'

            if int(result) == result:
                result = int(result)

            if roundDigits is not None:
                result = round(result, roundDigits)
                if roundDigits <= 0:
                    result = int(result)
                    if roundDigits == 0:
                        output_details = f'Wyjście zaokrąglone do całości'
                    else:
                        output_details = (
                            'Wyjście zaokrąglone do '
                            f'{TextFormatter.word_number_variant(-roundDigits, "cyfry", "cyfr")} przed przecinkiem'
                        )
                else:
                    output_details = (
                        'Wyjście zaokrąglone do '
                        f'{TextFormatter.word_number_variant(roundDigits, "cyfry", "cyfr")} po przecinku'
                    )

            embed = discord.Embed(
                title=':1234: Obliczono wartość wyrażenia',
                color=somsiad.COLOR
            )
            embed.add_field(name=input_details, value=f'```Matlab\n{input_info}```', inline=False)
            embed.add_field(name=output_details, value=f'```Matlab\n{result}```', inline=False)

    return await ctx.send(ctx.author.mention, embed=embed)

@calculate.error
async def calculate_error(ctx, error):
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        embed = discord.Embed(
            title=':warning: Nie podano wyrażenia ani zmiennych!',
            color=somsiad.COLOR
        )
        await ctx.send(ctx.author.mention, embed=embed)
