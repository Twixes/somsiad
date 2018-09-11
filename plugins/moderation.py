# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from somsiad import TextFormatter, somsiad

AUTODESTRUCTION_TIME_IN_SECONDS = 5
AUTODESTRUCTION_NOTICE = (
    f'Ta wiadomość ulegnie autodestrukcji w ciągu '
    f'{TextFormatter.noun_variant(AUTODESTRUCTION_TIME_IN_SECONDS, "sekundy", "sekund")} od wysłania.'
)


@somsiad.client.command(aliases=['wyczyść', 'wyczysc'])
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

    last_adjective_variant = TextFormatter.adjective_variant(
        number_of_messages_to_delete, 'ostatnią', 'ostatnie', 'ostatnich'
    )
    messages_noun_variant = TextFormatter.noun_variant(
        number_of_messages_to_delete, 'wiadomość', 'wiadomości', include_number=False
    )
    embed = discord.Embed(
        title=f':white_check_mark: Usunięto z kanału {last_adjective_variant} {messages_noun_variant}',
        description=AUTODESTRUCTION_NOTICE,
        color=somsiad.color
    )

    await ctx.send(ctx.author.mention, embed=embed, delete_after=AUTODESTRUCTION_TIME_IN_SECONDS)


@purge.error
async def purge_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.BotMissingPermissions):
        embed = discord.Embed(
            title=':warning: Nie usunięto z kanału żadnych wiadomości, ponieważ bot nie ma tutaj do tego uprawnień',
            description=AUTODESTRUCTION_NOTICE,
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed, delete_after=AUTODESTRUCTION_TIME_IN_SECONDS)
    elif isinstance(error, discord.ext.commands.MissingPermissions):
        embed = discord.Embed(
            title=':warning: Nie usunięto z kanału żadnych wiadomości, ponieważ nie masz tutaj uprawnień do tego',
            description=AUTODESTRUCTION_NOTICE,
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed, delete_after=AUTODESTRUCTION_TIME_IN_SECONDS)
    elif isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Podana wartość nie jest prawidłową liczbą wiadomości do usunięcia',
            description=AUTODESTRUCTION_NOTICE,
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed, delete_after=AUTODESTRUCTION_TIME_IN_SECONDS)


@somsiad.client.command(aliases=['zaproś', 'zapros'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def invite(ctx, *args):
    is_user_permitted_to_invite = False
    for current_channel in ctx.guild.channels:
        if current_channel.permissions_for(ctx.author).create_instant_invite:
            is_user_permitted_to_invite = True
            break

    argument = ' '.join(args).lower()

    if 'somsi' in argument or str(ctx.me.id) in argument:
        embed = discord.Embed(
            title=':house: Zapraszam do Somsiad Labs - mojegu domu',
            description='http://discord.gg/EFj3hhQ',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)

    elif is_user_permitted_to_invite:
        max_uses = 0
        unique = True

        if args:
            for arg in args:
                if 'recykl' in arg.lower():
                    unique = False
                if 'jednorazow' in arg.lower():
                    max_uses = 1
                elif arg.isnumeric():
                    max_uses = int(arg)

        channel = None
        invite = None
        if ctx.channel.permissions_for(ctx.me).create_instant_invite:
            channel = ctx.channel
        else:
            for current_channel in ctx.guild.channels:
                if (current_channel.permissions_for(ctx.me).create_instant_invite
                        and current_channel.permissions_for(ctx.author).create_instant_invite
                        and not isinstance(current_channel, discord.CategoryChannel)):
                    channel = current_channel
                    break

        invite = await channel.create_invite(
            max_uses=max_uses,
            unique=unique,
            reason=str(ctx.author)
        )

        if channel is None:
            embed = discord.Embed(
                title=':warning: Nie utworzono zaproszenia, bo bot nie ma do tego uprawnień na żadnym kanale, '
                'na którym ty je masz',
                description=AUTODESTRUCTION_NOTICE,
                color=somsiad.color
            )
            await ctx.send(ctx.author.mention, embed=embed, delete_after=AUTODESTRUCTION_TIME_IN_SECONDS)
        else:
            if max_uses == 0:
                max_uses_info = ' o nieskończonej liczbie użyć'
            elif max_uses == 1:
                max_uses_info = ' jednorazowe'
            else:
                max_uses_info = f' o {max_uses} użyciach'
            embed = discord.Embed(
                title=f':white_check_mark: {"Utworzono" if unique else "Zrecyklowano (jeśli się dało)"}'
                f'{max_uses_info if max_uses == 1 else ""} zaproszenie na kanał '
                f'{"#" if isinstance(channel, discord.TextChannel) else ""}{channel}'
                f'{max_uses_info if max_uses != 1 else ""}',
                description=invite.url,
                color=somsiad.color
            )
            await ctx.send(ctx.author.mention, embed=embed)

    else:
        embed = discord.Embed(
            title=':warning: Nie utworzono zaproszenia, bo nie masz do tego uprawnień na żadnym kanale',
            description=AUTODESTRUCTION_NOTICE,
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed, delete_after=AUTODESTRUCTION_TIME_IN_SECONDS)
