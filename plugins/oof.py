# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Union, List
import discord
from somsiad import somsiad
from server_data import server_data_manager
from utilities import TextFormatter


class Oof:
    TABLE_NAME = 'oof'
    TABLE_COLUMNS = (
        'user_id INTEGER NOT NULL PRIMARY KEY',
        'oofs INTEGER NOT NULL DEFAULT 0'
    )

    @classmethod
    def get_oofs(cls, server: discord.Guild, member: Union[discord.User, discord.Member]) -> Union[int, None]:
        server_data_manager.ensure_table_existence_for_server(server.id, cls.TABLE_NAME, cls.TABLE_COLUMNS)
        server_data_manager.servers[server.id]['db_cursor'].execute(
            'SELECT oofs FROM oof WHERE user_id = ?',
            (member.id,)
        )
        result = server_data_manager.servers[server.id]['db_cursor'].fetchone()
        oofs = None if result is None else result['oofs']
        return oofs

    @classmethod
    def get_oofs_ranking(cls, server: discord.Guild) -> List[list]:
        server_data_manager.ensure_table_existence_for_server(server.id, cls.TABLE_NAME, cls.TABLE_COLUMNS)
        server_data_manager.servers[server.id]['db_cursor'].execute(
            'SELECT user_id, oofs FROM oof'
        )
        rows = [
            server_data_manager.dict_from_row(row)
            for row in server_data_manager.servers[server.id]['db_cursor'].fetchall()
        ]
        sorted_rows = sorted(rows, key=lambda row: row['oofs'], reverse=True)
        return sorted_rows

    @classmethod
    def ensure_user_registration(cls, server: discord.Guild, member: Union[discord.User, discord.Member]):
        if cls.get_oofs(server, member) is None:
            server_data_manager.servers[server.id]['db_cursor'].execute(
                'INSERT INTO oof(user_id) VALUES(?)',
                (member.id,)
            )
            server_data_manager.servers[server.id]['db'].commit()

    @classmethod
    def increment(cls, server: discord.Guild, member: Union[discord.User, discord.Member]):
        cls.ensure_user_registration(server, member)
        server_data_manager.servers[server.id]['db_cursor'].execute(
            'UPDATE oof SET oofs = oofs + 1 WHERE user_id = ?',
            (member.id,)
        )
        server_data_manager.servers[server.id]['db'].commit()


@somsiad.bot.group(invoke_without_command=True)
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def oof(ctx):
    Oof.increment(ctx.guild, ctx.author)
    await ctx.send('Oof!')


@oof.command(aliases=['ile'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def how_many(ctx, user: discord.User = None):
    is_selfcheck = False
    if user is None:
        user = ctx.author
        is_selfcheck = True

    oofs = Oof.get_oofs(ctx.guild, user)
    oofs = 0 if oofs is None else oofs

    if is_selfcheck:
        embed = discord.Embed(
            title='Masz na koncie '
            f'{TextFormatter.word_number_variant(oofs, "oofnięcie", "oofnięcia", "oofnięć")}',
            color=somsiad.color
        )
    else:
        embed = discord.Embed(
            title=f'{user.display_name} ma na koncie '
            f'{TextFormatter.word_number_variant(oofs, "oofnięcie", "oofnięcia", "oofnięć")}',
            color=somsiad.color
        )

    await ctx.send(ctx.author.mention, embed=embed)


@how_many.error
async def how_many_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Nie znaleziono podanego użytkownika!',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)


@oof.command()
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def ranking(ctx):
    oofs_ranking = Oof.get_oofs_ranking(ctx.guild)

    top_oofers = []
    rank = 1
    for oofer in oofs_ranking[:5]:
        oofer_user = ctx.bot.get_user(oofer['user_id'])
        top_oofers.append(
            f'{rank}. {oofer_user.mention} – '
            f'{TextFormatter.word_number_variant(oofer["oofs"], "oofnięcie", "oofnięcia", "oofnięć")}'
        )
        rank += 1
    top_oofers_string = '\n'.join(top_oofers) if top_oofers else 'Brak'

    embed = discord.Embed(
        title=f'Ranking ooferów serwera {ctx.guild}',
        description=top_oofers_string,
        color=somsiad.color
    )

    await ctx.send(ctx.author.mention, embed=embed)
