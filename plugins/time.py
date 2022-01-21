# Copyright 2022 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import datetime as dt

from discord.ext import commands

from core import cooldown
from somsiad import Somsiad, SomsiadMixin

HOUR_TO_WORD = {
    1: "Pierwsza",
    2: "Druga",
    3: "Trzecia",
    4: "Czwarta",
    5: "Piąta",
    6: "Szósta",
    7: "Siódma",
    8: "Ósma",
    9: "Dziewiąta",
    10: "Dziesiąta",
    11: 'Jedenasta',
    12: "Dwunasta",
    13: "Trzynasta",
    14: "Czternasta",
    15: "Piętnasta",
    16: "Szesnasta",
    17: "Siedemnasta",
    18: "Osiemnasta",
    19: "Dziewiętnasta",
    20: "Dwudziesta",
    21: "Dwudziesta pierwsza",
    22: "Dwudziesta druga",
    23: "Dwudziesta trzecia",
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
    relevant_minute_to_word = MINUTE_TO_WORD_ACCUSATIVE if hour == 0 else MINUTE_TO_WORD
    if minute == 0:
        if hour == 0:
            return 'Północ'
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
        return f"{minute_written} minut po północy"
    else:
        hour_written = HOUR_TO_WORD[hour]
        return ' '.join(map(str, filter(None, (hour_written, minute_written))))


class Time(commands.Cog, SomsiadMixin):
    @commands.command(aliases=['ktoragodzina', 'któragodzina', 'whattime', 'wiespät'])
    @cooldown()
    async def what_time_is_it(self, ctx):
        now = dt.datetime.now()
        current_time = (now.hour, now.minute)
        if current_time == (1, 23):
            embed = self.bot.generate_embed(
                '☢️',
                'Czarnobylowa',
                "26 kwietnia 1986 roku o godzinie 1:23 w wyniku nieudanego testu bezpieczeństwa, doszło do wybuchu reaktora nr 4 w Czarnobylskiej Elektrowni Jądrowej. Wieczna pamięć i szacunek dla pracowników elektrowni, strażaków, żołnierzy, milicjantów, górników, inżynierów oraz robotników budowlanych i innych osób, które poświęciły swoje życie lub zdrowie pracując przy akcji usuwania skutków awarii.",
            )
        elif current_time == (4, 20):
            embed = self.bot.generate_embed('🪴', 'Ziołowa (poranna)')
        elif current_time == (13, 37):
            embed = self.bot.generate_embed('👾', 'Leetowa')
        elif current_time == (16, 20):
            embed = self.bot.generate_embed('💨', 'Ziołowa (popołudniowa)')
        elif current_time == (21, 37):
            embed = self.bot.generate_embed('🌝', 'Papieżowa')
        else:
            emoji_hour = (now.hour - 1) % 12 + 1
            nearest_emoji_time = f'{emoji_hour}30' if now.minute >= 30 else str(emoji_hour)
            embed = self.bot.generate_embed(f':clock{nearest_emoji_time}:', write_time_out(*current_time))
        await self.bot.send(ctx, embed=embed)


def setup(bot: Somsiad):
    bot.add_cog(Time(bot))
