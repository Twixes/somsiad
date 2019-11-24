# Copyright 2018-2019 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import asyncio
import locale
import datetime as dt
import string
from typing import Union, Optional
from numbers import Number
import discord
from core import somsiad
from utilities import TextFormatter, interpret_str_as_datetime
from configuration import configuration

LETTER_EMOIJS = {
    'A': '🇦', 'B': '🇧', 'C': '🇨', 'D': '🇩', 'E': '🇪', 'F': '🇫', 'G': '🇬', 'H': '🇭', 'I': '🇮', 'J': '🇯',
    'K': '🇰', 'L': '🇱', 'M': '🇲', 'N': '🇳', 'O': '🇴', 'P': '🇵', 'Q': '🇶', 'R': '🇷', 'S': '🇸', 'T': '🇹',
    'U': '🇺', 'V': '🇻', 'W': '🇼', 'X': '🇽', 'Y': '🇾', 'Z': '🇿'
}

@somsiad.command(aliases=['głosowanie', 'glosowanie', 'poll', 'ankieta'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def vote(
        ctx, duration: Optional[Union[int, locale.atoi, interpret_str_as_datetime]] = None,
        *, statement: discord.ext.commands.clean_content(fix_channel_mentions=True)
    ):
    """Holds a vote."""
    now_datetime = dt.datetime.now().astimezone()
    if isinstance(duration, dt.datetime) and now_datetime < duration <= now_datetime + dt.timedelta(days=7):
        results_datetime = duration
        results_and_now_timedelta = results_datetime - now_datetime
        seconds = results_and_now_timedelta.total_seconds()
        human_readable_time = TextFormatter.human_readable_time(seconds)
        embed = discord.Embed(
            title=f':ballot_box: {statement}',
            description=(
                'Zagłosuj w tej sprawie przy użyciu reakcji.\n'
                f'Wynik zostanie ogłoszony {duration.strftime("%-d %B %Y o %H:%M")}.'
            ),
            timestamp=results_datetime,
            color=somsiad.COLOR
        )
    elif isinstance(duration, Number) and 0.0 < duration <= 10080.0:
        seconds = duration * 60.0
        results_datetime = now_datetime + dt.timedelta(seconds=seconds)
        human_readable_time = TextFormatter.human_readable_time(seconds)
        embed = discord.Embed(
            title=f':ballot_box: {statement}',
            description=(
                'Zagłosuj w tej sprawie przy użyciu reakcji.\n'
                f'Wynik zostanie ogłoszony po {TextFormatter.human_readable_time(seconds)} od rozpoczęcia głosowania.'
            ),
            timestamp=results_datetime,
            color=somsiad.COLOR
        )
    else:
        seconds = None
        embed = discord.Embed(
            title=f':ballot_box: {statement}',
            description='Zagłosuj w tej sprawie przy użyciu reakcji.',
            color=somsiad.COLOR
        )

    letter_options_found = []
    for letter in string.ascii_uppercase:
        if f'{letter}.' in statement or f'{letter}:' in statement:
            letter_options_found.append(letter)
        else:
            break

    if letter_options_found:
        options = [LETTER_EMOIJS[letter] for letter in letter_options_found]
    else:
        options = ('✅', '🔴')

    message = await ctx.send(ctx.author.mention, embed=embed)
    for option_emoji in options:
        await message.add_reaction(option_emoji)

    if seconds is not None:
        await asyncio.sleep(seconds)

        try:
            message_final = await ctx.channel.fetch_message(message.id)
        except discord.NotFound:
            pass
        else:
            result = {
                reaction.emoji: reaction.count - 1 for reaction in message_final.reactions if reaction.emoji in options
            }

            winning_emojis = []
            winning_count = -1

            for option in result.items():
                if option[1] > winning_count:
                    winning_emojis = [option[0]]
                    winning_count = option[1]
                elif option[1] == winning_count:
                    winning_emojis.append(option[0])

            if len(winning_emojis) != 1:
                result_emoji = '❓'
            else:
                result_emoji = winning_emojis[0]

            embed_results = discord.Embed(
                title=f'{result_emoji} {statement}',
                description=(
                    f'Głosowanie zostało zakończone po {human_readable_time} od rozpoczęcia.'
                ),
                timestamp=results_datetime,
                color=somsiad.COLOR
            )
            if letter_options_found:
                for letter in letter_options_found:
                    letter_emoji = LETTER_EMOIJS[letter]
                    if letter_emoji in winning_emojis and winning_count > 0:
                        presentation_count = f'**{result[letter_emoji]}**'
                    else:
                        presentation_count = result[letter_emoji]
                    embed_results.add_field(name=f'Opcja {letter}', value=presentation_count)
            else:
                embed_results.add_field(
                    name='Za',
                    value=f'**{result["✅"]}**' if '✅' in winning_emojis and winning_count > 0 else result['✅']
                )
                embed_results.add_field(
                    name='Przeciw',
                    value=f'**{result["🔴"]}**' if '🔴' in winning_emojis and winning_count > 0 else result['🔴']
                )

            await message_final.edit(embed=embed_results)
            await ctx.send(ctx.author.mention, embed=embed_results)


@vote.error
async def vote_error(ctx, error):
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        embed = discord.Embed(
            title=f':warning: Nie podano sprawy w jakiej ma się odbyć głosowanie!',
            color=somsiad.COLOR
        )
        await ctx.send(ctx.author.mention, embed=embed)
