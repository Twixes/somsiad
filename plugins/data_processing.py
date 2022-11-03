# Copyright 2022 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from core import Help, cooldown
from somsiad import Somsiad, SomsiadMixin
from core import DataProcessingOptOut
from discord.ext import commands
import data
from sqlalchemy.exc import IntegrityError


class DataProcessing(commands.Cog, SomsiadMixin):
    GROUP = Help.Command(
        'przetwarzanie-danych',
        (),
        'Narzędzia dotyczące przetwarzania Twoich danych przez Somsiada.',
    )
    COMMANDS = (
        Help.Command(('wypisz'), [], 'Wypisuje Cię z przetwarzania Twoich danych przez Somsiada i usuwa istniejące dane z systemu. Niektóre funkcje Somsiada mogą na skutek tego przestać dla Ciebie działać.'),
        Help.Command(('przywróć'), [], 'Przywraca zgodę na przetwarzanie Twoich danych przez Somsiada, pozwalając wszystkim funkcjom działać w pełni.'),
    )
    HELP = Help(COMMANDS, '😎', group=GROUP)

    @cooldown()
    @commands.group(aliases=['przetwarzanie-danych'], invoke_without_command=True, case_insensitive=True)
    async def data_processing(self, ctx):
        print(data.USER_RELATED_MODELS)
        await self.bot.send(ctx, embed=self.HELP.embeds)

    @cooldown()
    @data_processing.command(aliases=['wypisz'])
    async def data_processing_opt_out(self, ctx):
        try:
            with data.session(commit=True) as session:
                invocation = DataProcessingOptOut(
                    user_id=ctx.author.id,
                )
                session.add(invocation)
                for model in data.USER_RELATED_MODELS:
                    session.query(model).filter_by(user_id=ctx.author.id).delete()
        except IntegrityError:
            embed = self.bot.generate_embed('👤', 'Już jesteś wypisany z przetwarzania Twoich danych przez Somsiada')
        else:
            embed = self.bot.generate_embed('👤', 'Wypisano Cię z przetwarzania Twoich danych przez Somsiada', 'Usunięto także wszystkie istniejące dane związane z Tobą.')
        await self.bot.send(ctx, embed=embed)

    @cooldown()
    @data_processing.command(aliases=['przywróć', 'zapisz'])
    async def data_processing_opt_in(self, ctx):
        with data.session(commit=True) as session:
            deleted_count = session.query(DataProcessingOptOut).filter_by(user_id=ctx.author.id).delete()
        await self.bot.send(ctx, embed=self.bot.generate_embed('🙋', 'Przywrócono Somsiadowi możliwość przetwarzania Twoich danych' if deleted_count else 'Somsiad ma już możliwość przetwarzania Twoich danych'))


async def setup(bot: Somsiad):
    await bot.add_cog(DataProcessing(bot))
