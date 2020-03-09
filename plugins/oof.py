# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from discord.ext import commands
from core import MemberSpecific, cooldown
from utilities import word_number_form
import data


class Oofer(data.Base, MemberSpecific):
    oofs = data.Column(data.Integer, nullable=False, default=1)


class Oof(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, case_insensitive=True)
    @cooldown()
    @commands.guild_only()
    async def oof(self, ctx):
        with data.session(commit=True) as session:
            oofer = session.query(Oofer).get({'server_id': ctx.guild.id, 'user_id': ctx.author.id})
            if oofer is not None:
                oofer.oofs = Oofer.oofs + 1
            else:
                oofer = Oofer(server_id=ctx.guild.id, user_id=ctx.author.id)
                session.add(oofer)
        await self.bot.send(ctx, 'Oof!')

    @oof.group(aliases=['ile'], invoke_without_command=True, case_insensitive=True)
    @cooldown()
    @commands.guild_only()
    async def oof_how_many(self, ctx, *, member: discord.Member = None):
        await ctx.invoke(self.oof_how_many_member, member=member)

    @oof_how_many.command(aliases=['member', 'user', 'członek', 'użytkownik'])
    @cooldown()
    @commands.guild_only()
    async def oof_how_many_member(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        with data.session() as session:
            oofer = session.query(Oofer).get({'server_id': ctx.guild.id, 'user_id': member.id})
            oofs = oofer.oofs if oofer is not None else 0

        address = 'Masz' if member == ctx.author else f'{member.display_name} ma'
        embed = self.bot.generate_embed(
            '💨', f'{address} na koncie {word_number_form(oofs, "oofnięcie", "oofnięcia", "oofnięć")}'
        )
        await self.bot.send(ctx, embed=embed)

    @oof_how_many_member.error
    async def oof_how_many_member_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = self.bot.generate_embed('⚠️', 'Nie znaleziono na serwerze pasującego użytkownika')
            await self.bot.send(ctx, embed=embed)

    @oof_how_many.command(aliases=['server', 'serwer', 'ranking'])
    @cooldown()
    @commands.guild_only()
    async def oof_how_many_server(self, ctx):
        await ctx.invoke(self.oof_server)

    @oof.command(aliases=['server', 'serwer', 'ranking'])
    @cooldown()
    @commands.guild_only()
    async def oof_server(self, ctx):
        async with ctx.typing():
            with data.session() as session:
                total_oofs = session.query(data.func.sum(Oofer.oofs).filter(Oofer.server_id == ctx.guild.id)).scalar()
                top_results = session.query(
                    Oofer,
                    data.func.dense_rank().over(order_by = Oofer.oofs.desc()).label('rank')
                ).filter(Oofer.server_id == ctx.guild.id).limit(25).all()
            ranking = []
            for result in top_results:
                if result.rank > 10:
                    break
                ranking.append(
                    f'{result.rank}. <@{result.Oofer.user_id}> – '
                    f'{word_number_form(result.Oofer.oofs, "oofnięcie", "oofnięcia", "oofnięć")}'
                )
            if total_oofs:
                notice = f'Do tej pory oofnięto na serwerze {word_number_form(total_oofs, "raz", "razy")}'
            else:
                notice = 'Na serwerze nie oofnięto jeszcze ani razu'
            embed = self.bot.generate_embed('💨', notice)
            if ranking:
                embed.add_field(name='Najaktywniejsi ooferzy', value='\n'.join(ranking), inline=False)
            await self.bot.send(ctx, embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Oof(bot))
