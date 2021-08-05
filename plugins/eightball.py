# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import datetime as dt
import hashlib
import random
from typing import Optional, cast

import discord
from somsiad import SomsiadMixin

from discord.ext import commands

from core import cooldown

class Eightball(commands.Cog, SomsiadMixin):
    CATEGORIES_POOL = ['affirmative'] * 7 + ['negative'] * 7 + ['enigmatic'] * 1
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
            'To wielce prawdopodobne.',
            'Z przeprowadzonych przeze mnie właśnie analiz wynika, że raczej tak.',
            'YES, YES, YES!',
            'Yep.',
            'Ja!',
            'Dа.',
        ],
        'negative': [
            'Zdecydowanie nie.',
            'Absolutnie nie.',
            'Nie ma mowy.',
            'Niestety nie.',
            'Na szczęście nie.',
            'Raczej nie.',
            'Nie wydaje mi się.',
            'Mój wywiad donosi: NIE.',
            'Nie, nie i jeszcze raz NIE.',
            'Sprawdziłem wszystkie dostępne mi zasoby wiedzy i wygląda na to, że nie.',
            'Mocno skłaniam się ku: nie.',
            'Nope.',
            'Nein!',
            'Niet.',
        ],
        'enigmatic': [
            'Zbyt wcześnie, by powiedzieć.',
            'Kto wie?',
            'Być może.',
            'Mój wywiad donosi: MOŻE?',
            'Trudno powiedzieć.',
            'To pytanie jest dla mnie zbyt głębokie.',
            'Przecież już znasz odpowiedź.',
            'Moim zdaniem to nie ma tak, że tak albo że nie.',
            'Mnie się o to pytaj.',
            'Powiem ci, że nie wiem.',
            'Nie mam ochoty zajmować się dziś takimi bzdurnymi tematami. Spróbuj kiedy indziej.',
            'Uwierz mi, tej odpowiedzi nie chcesz znać.',
        ],
    }

    def ask(self, stripped_question: str, category: Optional[str] = None) -> str:
        question_hash = hashlib.md5(stripped_question.encode())
        question_hash.update(dt.date.today().isoformat().encode())
        question_hash_int = int.from_bytes(question_hash.digest(), 'big')
        if not category:
            category = self.CATEGORIES_POOL[question_hash_int % len(self.CATEGORIES_POOL)]
        answer = self.ANSWERS[category][question_hash_int % len(self.ANSWERS)]
        return answer

    def AsK(self, stripped_question: str) -> str:
        aNSwEr = ''.join(random.choice([letter.lower(), letter.upper()]) for letter in self.ask(stripped_question))
        return aNSwEr

    @commands.command(aliases=['8ball', '8-ball', '8', 'czy'])
    @cooldown()
    async def eightball(self, ctx: commands.Context, *, question: commands.clean_content(fix_channel_mentions=True) = ''):
        """Returns an 8-Ball answer."""
        stripped_question = question.strip('`~!@#$%^&*()-_=+[{]}\\|;:\'",<.>/?‽').lower()
        if stripped_question:
            if '‽' in question or 'fccchk' in stripped_question:
                text = f'👺 {self.AsK(stripped_question)}'
            else:
                text = f'🎱 {self.ask(stripped_question)}'
        else:
            text = '⚠️ By zadać magicznej kuli pytanie musisz użyć *słów*.'
        await self.bot.send(ctx, text)

    @commands.command(aliases=['niepierdol'])
    @cooldown()
    async def dontbullshit(self, ctx: commands.Context):
        """Inverts the last 8-Ball answer in the channel."""
        async for message in ctx.history(limit=10):
            if message.author != ctx.me:
                continue
            message_content = cast(str, cast(discord.Message, message).clean_content)
            if not message_content.startswith('🎱 '):
                continue
            previous_answer = message_content[2:]
            if previous_answer in self.ANSWERS['affirmative']:
                new_category = 'negative'
            elif previous_answer in self.ANSWERS['negative']:
                new_category = 'affirmative'
            else:
                new_category = random.choice(['affirmative', 'negative'])
            new_text = f'🎱 {random.choice(self.ANSWERS[new_category])}'
            await message.edit(content=new_text)
            break



def setup(bot: commands.Bot):
    bot.add_cog(Eightball(bot))
