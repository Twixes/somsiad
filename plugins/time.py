# Copyright 2022 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import datetime as dt
from random import random
from typing import Dict, Optional, Tuple

from discord.ext import commands

from core import cooldown
from somsiad import Somsiad, SomsiadMixin
from utilities import word_number_form

HOUR_TO_WORD = {
    1: "pierwsza",
    2: "druga",
    3: "trzecia",
    4: "czwarta",
    5: "piąta",
    6: "szósta",
    7: "siódma",
    8: "ósma",
    9: "dziewiąta",
    10: "dziesiąta",
    11: 'jedenasta',
    12: "dwunasta",
    13: "trzynasta",
    14: "czternasta",
    15: "piętnasta",
    16: "szesnasta",
    17: "siedemnasta",
    18: "osiemnasta",
    19: "dziewiętnasta",
    20: "dwudziesta",
    21: "dwudziesta pierwsza",
    22: "dwudziesta druga",
    23: "dwudziesta trzecia",
}
MINUTE_TO_WORD = {
    1: "jeden",
    2: "dwa",
    3: "trzy",
    4: "cztery",
    5: "pięć",
    6: 'sześć',
    7: 'siedem',
    8: 'osiem',
    9: 'dziewięć',
    10: 'dziesięć',
    11: 'jedenaście',
    12: 'dwanaście',
    13: "trzynaście",
    14: "czternaście",
    15: "piętnaście",
    16: "szesnaście",
    17: "siedemnaście",
    18: "osiemnaście",
    19: "dziewiętnaście",
    20: "dwadzieścia",
    30: "trzydzieści",
    40: "czterdzieści",
    50: "pięćdziesiąt",
}
MINUTE_TO_WORD_ACCUSATIVE = {
    1: "jedna",
    2: "dwie",
    3: "trzy",
    4: "cztery",
    5: "pięć",
    6: 'sześć',
    7: 'siedem',
    8: 'osiem',
    9: 'dziewięć',
    10: 'dziesięć',
    11: 'jedenaście',
    12: 'dwanaście',
    13: "trzynaście",
    14: "czternaście",
    15: "piętnaście",
    16: "szesnaście",
    17: "siedemnaście",
    18: "osiemnaście",
    19: "dziewiętnaście",
    20: "dwadzieścia",
    30: "trzydzieści",
    40: "czterdzieści",
    50: "pięćdziesiąt",
}


def write_time_out(hour: int, minute: int) -> str:
    relevant_minute_to_word = (
        MINUTE_TO_WORD_ACCUSATIVE if hour == 0 and (minute == 1 or minute % 10 != 1) else MINUTE_TO_WORD
    )
    if minute == 0:
        minute_written = None
    elif minute in relevant_minute_to_word:
        minute_written = relevant_minute_to_word[minute]
    else:
        minute_tens = (minute // 10) * 10
        minute_tens_written = relevant_minute_to_word[minute_tens]
        minute_ones = minute % 10
        minute_ones_written = relevant_minute_to_word[minute_ones] if minute_ones else None
        minute_written = ' '.join(map(str, filter(None, (minute_tens_written, minute_ones_written))))

    if hour == 0:
        return (
            f"{minute_written} {word_number_form(minute, 'minuta', 'minuty', 'minut', include_number=False)} po północy".capitalize()
            if minute_written is not None
            else 'Północ'
        )
    else:
        hour_written = HOUR_TO_WORD[hour]
        return ' '.join(map(str, filter(None, (hour_written, minute_written)))).capitalize()


class Time(commands.Cog, SomsiadMixin):
    MOMENTS_OF_INTEREST: Dict[Tuple[int, int], Tuple[str, str, Optional[str]]] = {
        (0, 30): ('🕧', "gimme gimme gimme", None),
        (0, 42): ('🐭', 'Autostopowa', None),
        (1, 23): (
            '☢️',
            'Czarnobylowa',
            "26 kwietnia 1986 roku o godzinie 1:23 w wyniku nieudanego testu bezpieczeństwa, doszło do wybuchu reaktora nr 4 w Czarnobylskiej Elektrowni Jądrowej. Wieczna pamięć i szacunek dla pracowników elektrowni, strażaków, żołnierzy, milicjantów, górników, inżynierów oraz robotników budowlanych i innych osób, które poświęciły swoje życie lub zdrowie pracując przy akcji usuwania skutków awarii.",
        ),
        (3, 20): ('✈️', 'Airbusowa (mała)', None),
        (3, 50): ('✈️', 'Airbusowa (średnia)', None),
        (4, 20): ('🪴', 'Ziołowa (poranna)', None),
        (7, 37): ('✈️', 'Boeingowa (mała)', None),
        (7, 47): ('✈️', 'Boeingowa (duża)', None),
        (13, 37): ('👾', 'Leetowa', None),
        (16, 20): ('💨', 'Ziołowa (popołudniowa)', None),
        (21, 37): ('🌝', 'Papieżowa', None),
        (21, 38): ('🌚', 'Anty-papieżowa', None),
    }

    @cooldown()
    @commands.command(aliases=['ktoragodzina', 'któragodzina', 'whattime', 'wiespät'])
    async def what_time_is_it(self, ctx, hour: Optional[int] = None, minute: Optional[int] = None):
        chance = random()
        if chance < 0.01:
             embed = self.bot.generate_embed('🕰️', 'Wpół do komina')
        else:
            now = dt.datetime.now()
            current_time = (hour or now.hour, minute or now.minute)
            if moment := self.MOMENTS_OF_INTEREST.get(current_time):
                embed = self.bot.generate_embed(*moment)
            elif chance < 0.5:
                # If after that day's papieżowa, show "Papieżowa + n minut", otherwise show "n minut do papieżowej"
                if (now.hour, now.minute) > (21, 37):
                    diff = now.hour * 60 + now.minute - 21 * 60 - 37
                    text = f"Papieżowa + {word_number_form(diff, 'minuta', 'minuty', 'minut')}"
                else:
                    diff = 21 * 60 + 37 - now.hour * 60 - now.minute
                    text = f"{word_number_form(diff, 'minuta', 'minuty', 'minut')} do papieżowej"
                embed = self.bot.generate_embed(self.MOMENTS_OF_INTEREST[(21, 37)][0], text)
            else:
                emoji_hour = (now.hour - 1) % 12 + 1
                nearest_emoji_time = f'{emoji_hour}30' if now.minute >= 30 else str(emoji_hour)
                embed = self.bot.generate_embed(f':clock{nearest_emoji_time}:', write_time_out(*current_time))
        await self.bot.send(ctx, embed=embed)


async def setup(bot: Somsiad):
    await bot.add_cog(Time(bot))
