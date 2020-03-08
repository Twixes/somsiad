# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import random
from discord.ext import commands
from core import cooldown


class Eightball(commands.Cog):
    CATEGORIES_POOL = ['definitive'] * 49 + ['enigmatic'] * 1
    DEFINITIVE_SUBCATEGORIES_POOL = ['affirmative', 'negative']
    ANSWERS = {
        'affirmative': [
            'Jak najbardziej tak.',
            'Z całą pewnością tak.',
            'Bez wątpienia tak.',
            'Niestety tak.',
            'Na szczęście tak.',
            'Chyba tak.',
            'Wszystko wskazuje na to, że tak.',
            'Mój wywiad donosi: TAK.',
            'YES, YES, YES!',
            'Yep.',
            'Ja!',
            'Dа.'
        ], 'negative': [
            'Zdecydowanie nie.',
            'Absolutnie nie.',
            'Nie ma mowy.',
            'Niestety nie.',
            'Na szczęście nie.',
            'Raczej nie.',
            'Nie wydaje mi się.',
            'Mój wywiad donosi: NIE.',
            'Nope.',
            'Nein!',
            'Niet.'
        ], 'enigmatic': [
            'Zbyt wcześnie, by powiedzieć.',
            'Kto wie?',
            'Być może.',
            'Mój wywiad donosi: MOŻE?',
            'Trudno powiedzieć.',
            'To pytanie jest dla mnie zbyt głębokie.',
            'Przecież już znasz odpowiedź.'
        ]
    }

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def ask(self) -> str:
        category = random.choice(self.CATEGORIES_POOL)
        specific_category = 'enigmatic' if category == 'enigmatic' else random.choice(
            self.DEFINITIVE_SUBCATEGORIES_POOL
        )
        answer = random.choice(self.ANSWERS[specific_category])
        return answer

    def AsK(self) -> str:
        aNSwEr = ''.join(random.choice([letter.lower(), letter.upper()]) for letter in self.ask())
        return aNSwEr

    @commands.command(aliases=['8ball', '8-ball', '8', 'czy'])
    @cooldown()
    async def eightball(self, ctx, *, question: commands.clean_content(fix_channel_mentions=True) = ''):
        """Returns an 8-Ball answer."""
        stripped_question = question.strip('`~!@#$%^&*()-_=+[{]}\\|;:\'",<.>/?').lower()
        if stripped_question:
            if 'fccchk' in stripped_question or '‽' in stripped_question:
                text = f'👺 {self.AsK()}'
            else:
                text = f'🎱 {self.ask()}'
        else:
            text = '⚠️ By zadać magicznej kuli pytanie musisz użyć *słów*'
        await self.bot.send(ctx, text)


def setup(bot: commands.Bot):
    bot.add_cog(Eightball(bot))
