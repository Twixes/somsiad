# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import datetime as dt
import hashlib
from somsiad import SomsiadMixin

from discord.ext import commands

from core import cooldown


class Choice(commands.Cog, SomsiadMixin):
    CATEGORIES_POOL = ['definitive'] * 24 + ['enigmatic']  # 96% one option, 4% unknown
    ANSWERS = {
        'definitive': [
            'Z mojej strony zdecydowane {0}.',
            'Nie znam się, ale myślę, że najlepszą opcją jest {0}.',
            '{0}, choć bez przekonania…',
            'Może {0}?',
            'Sugerowałbym {0}.',
            'Muszę powiedzieć, że {0} brzmi nieźle.',
            'Zdecydowanie {0}.',
            '{0}, bez dwóch zdań.',
            'To oczywiste, że {0}.',
            'Wiem coś o tym i z czystym sumieniem mogę doradzić {0}.',
            'Nie ma nad czym się tutaj zastanawiać: {0}.',
            'Dla mnie sprawa jest prosta: {0}.',
            'W razie wątpliwości zawsze wybieraj {0}.',
            'Na twoim miejscu spróbowałbym {0}.',
        ],
        'enigmatic': [
            'Żadna z opcji nie wygląda ciekawie.',
            'Wszystkie opcje brzmią kusząco.',
            'Przecież już znasz odpowiedź.',
            'Powiem ci, że nie wiem.',
            'Nie mam ochoty zajmować się dziś takimi bzdurnymi tematami. Spróbuj kiedy indziej.',
            'Tak.',
            'Nie.',
        ],
    }

    @cooldown()
    @commands.command(aliases=['choose', 'wybierz'])
    async def random_choice(self, ctx, *, raw_options=''):
        """Randomly chooses one of provided options."""
        raw_options = raw_options.replace(';', ',').replace('|', ',')
        options_words = []
        for word in raw_options.strip('?').split():
            if word.lower() in ('or', 'czy', 'albo', 'lub'):
                options_words.append(',')
            else:
                options_words.append(word)
        options = [option.strip() for option in ' '.join(options_words).split(',') if option.strip() != '']
        if len(options) >= 2:
            question_hash = hashlib.md5()
            for option in options:
                question_hash.update(option.lower().encode())
            question_hash.update(dt.date.today().isoformat().encode())
            question_hash_int = int.from_bytes(question_hash.digest(), 'big')
            if 'trebuchet' in options:
                chosen_option = 'trebuchet'
            elif 'trebusz' in options:
                chosen_option = 'trebusz'
            elif 'trebuszet' in options:
                chosen_option = 'trebuszet'
            else:
                chosen_option = options[question_hash_int % len(options)]
            category = self.CATEGORIES_POOL[question_hash_int % len(self.CATEGORIES_POOL)]
            answer = self.ANSWERS[category][question_hash_int % len(self.ANSWERS)].format(f'👉 {chosen_option} 👈')
            await self.bot.send(ctx, answer)
        else:
            await self.bot.send(
                ctx,
                'Chętnie pomógłbym z wyborem, ale musisz podać mi kilka oddzielonych przecinkami, średnikami, '
                '"lub", "albo" lub "czy" opcji!',
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Choice(bot))
