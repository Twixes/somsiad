# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from core import MemberSpecific, somsiad
from utilities import word_number_form
from configuration import configuration
import data


class Oofer(data.Base, MemberSpecific):
    oofs = data.Column(data.Integer, nullable=False, default=1)


@somsiad.group(invoke_without_command=True, case_insensitive=True)
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def oof(ctx):
    with data.session(commit=True) as session:
        oofer = session.query(Oofer).get({'server_id': ctx.guild.id, 'user_id': ctx.author.id})
        if oofer is not None:
            oofer.oofs = Oofer.oofs + 1
        else:
            oofer = Oofer(server_id=ctx.guild.id, user_id=ctx.author.id)
            session.add(oofer)
    await ctx.send('Oof!')


@oof.group(aliases=['ile'], invoke_without_command=True, case_insensitive=True)
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def oof_how_many(ctx, member: discord.Member = None):
    await ctx.invoke(oof_how_many_member, member)


@oof_how_many.command(aliases=['member', 'user', 'członek', 'użytkownik'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def oof_how_many_member(ctx, member: discord.Member = None):
    member = member or ctx.author
    with data.session() as session:
        oofer = session.query(Oofer).get({'server_id': ctx.guild.id, 'user_id': member.id})
        oofs = oofer.oofs if oofer is not None else 0

    if member == ctx.author:
        embed = discord.Embed(
            title='Masz na koncie '
            f'{word_number_form(oofs, "oofnięcie", "oofnięcia", "oofnięć")}',
            color=somsiad.COLOR
        )
    else:
        embed = discord.Embed(
            title=f'{member.display_name} ma na koncie '
            f'{word_number_form(oofs, "oofnięcie", "oofnięcia", "oofnięć")}',
            color=somsiad.COLOR
        )

    await ctx.send(ctx.author.mention, embed=embed)


@oof_how_many_member.error
async def oof_how_many_member_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Nie znaleziono na serwerze pasującego użytkownika!',
            color=somsiad.COLOR
        )
        await ctx.send(ctx.author.mention, embed=embed)


@oof_how_many.command(aliases=['server', 'serwer'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def oof_how_many_server(ctx):
    await ctx.invoke(oof_server)


@oof.command(aliases=['server', 'serwer'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def oof_server(ctx):
    with data.session() as session:
        total_oofs = session.query(data.func.sum(Oofer.oofs)).scalar()
        top_results = session.query(
            Oofer,
            data.func.dense_rank().over(order_by = Oofer.oofs.desc()).label('rank')
        ).limit(25).all()

    ranking = []
    for result in top_results:
        if result.rank > 10:
            break
        ranking.append(
            f'{result.rank}. <@{result.Oofer.user_id}> – '
            f'{word_number_form(result.Oofer.oofs, "oofnięcie", "oofnięcia", "oofnięć")}'
        )

    embed = discord.Embed(
        title=f'Do tej pory oofnięto na serwerze {word_number_form(total_oofs, "raz", "razy")}',
        color=somsiad.COLOR
    )
    if ranking:
        embed.add_field(name='Najaktywniejsi ooferzy', value='\n'.join(ranking), inline=False)

    await ctx.send(ctx.author.mention, embed=embed)
