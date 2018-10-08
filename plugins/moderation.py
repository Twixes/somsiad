# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from somsiad import somsiad
from utilities import TextFormatter


@somsiad.bot.command(aliases=['nope', 'nie'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def no(ctx, member: discord.Member = None):
    """Removes the last message sent by the bot in the channel on the requesting user's request."""
    if member is None:
        member = ctx.author

    if member == ctx.author or ctx.author.permissions_in(ctx.channel).manage_messages:
        async for message in ctx.history(limit=15):
            if message.author == ctx.me and member in message.mentions:
                await message.delete()
                break


@somsiad.bot.command(aliases=['wyczyść', 'wyczysc'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
@discord.ext.commands.has_permissions(manage_messages=True)
@discord.ext.commands.bot_has_permissions(manage_messages=True)
async def purge(ctx, number_of_messages_to_delete: int = 1):
    """Removes last n messages from the channel."""
    if number_of_messages_to_delete > 50:
        number_of_messages_to_delete = 50

    await ctx.channel.purge(limit=number_of_messages_to_delete+1)

    last_adjective_variant = TextFormatter.word_number_variant(
        number_of_messages_to_delete, 'ostatnią', 'ostatnie', 'ostatnich'
    )
    messages_noun_variant = TextFormatter.word_number_variant(
        number_of_messages_to_delete, 'wiadomość', 'wiadomości', include_number=False
    )
    embed = discord.Embed(
        title=f':white_check_mark: Usunięto z kanału {last_adjective_variant} {messages_noun_variant}',
        description=somsiad.message_autodestruction_notice,
        color=somsiad.color
    )

    await ctx.send(ctx.author.mention, embed=embed, delete_after=somsiad.message_autodestruction_time_in_seconds)


@purge.error
async def purge_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.BotMissingPermissions):
        embed = discord.Embed(
            title=':warning: Nie usunięto z kanału żadnych wiadomości, ponieważ bot nie ma tutaj do tego uprawnień',
            description=somsiad.message_autodestruction_notice,
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed, delete_after=somsiad.message_autodestruction_time_in_seconds)
    elif isinstance(error, discord.ext.commands.MissingPermissions):
        embed = discord.Embed(
            title=':warning: Nie usunięto z kanału żadnych wiadomości, ponieważ nie masz tutaj uprawnień do tego',
            description=somsiad.message_autodestruction_notice,
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed, delete_after=somsiad.message_autodestruction_time_in_seconds)
    elif isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Podana wartość nie jest prawidłową liczbą wiadomości do usunięcia',
            description=somsiad.message_autodestruction_notice,
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed, delete_after=somsiad.message_autodestruction_time_in_seconds)
