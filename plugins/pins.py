# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import os
import io
import sqlite3
import discord
from somsiad import somsiad
from server_data import server_data_manager
from utilities import TextFormatter


class PinArchivesManager:
    def __init__(self):
        """Sets up the table in the database."""
        server_data_manager.servers_db_cursor.execute(
            '''CREATE TABLE IF NOT EXISTS pin_archive_channels(
                server_id INTEGER NOT NULL PRIMARY KEY,
                channel_id INTEGER NOT NULL
            )'''
        )
        server_data_manager.servers_db.commit()

    def set_archive_channel_id(self, server_id: int, channel_id: int):
        """Sets the ID of the server's pin archive channel."""
        if self.get_archive_channel_id(server_id) is None:
            server_data_manager.servers_db_cursor.execute(
                'INSERT INTO pin_archive_channels(server_id, channel_id) VALUES(?, ?)',
                (server_id, channel_id)
            )
        else:
            server_data_manager.servers_db_cursor.execute(
                'UPDATE pin_archive_channels SET channel_id = ? WHERE server_id = ?',
                (channel_id, server_id)
            )
        server_data_manager.servers_db.commit()

    def get_archive_channel_id(self, server_id: int) -> int:
        """Gets the ID of the server's pin archive channel."""
        server_data_manager.servers_db_cursor.execute(
            'SELECT channel_id FROM pin_archive_channels WHERE server_id = ?',
            (server_id,)
        )
        archive_channel_id = server_data_manager.servers_db_cursor.fetchone()

        if archive_channel_id is None:
            return None
        else:
            return archive_channel_id[0]

    @staticmethod
    async def archive_pin(pin: discord.Message, archive_channel: discord.TextChannel):
        """Archives the provided message in the provided channel."""
        pin_embed = discord.Embed(
            description=pin.content,
            color=somsiad.color,
            timestamp=pin.created_at
        )
        pin_embed.set_author(
            name=pin.author.display_name,
            url=pin.jump_url,
            icon_url=pin.author.avatar_url
        )
        pin_embed.set_footer(text=f'#{pin.channel}')

        files = []
        for attachment in pin.attachments:
            filename = attachment.filename
            fp = io.BytesIO()
            await attachment.save(fp)
            file = discord.File(fp, filename)
            files.append(file)

        if len(files) == 1:
            if pin.attachments[0].height is not None:
                pin_embed.set_image(url=f'attachment://{pin.attachments[0].filename}')
            await archive_channel.send(embed=pin_embed, file=files[0])
        elif len(files) > 1:
            await archive_channel.send(embed=pin_embed, files=files)
        else:
            url_from_content = TextFormatter.find_url(pin.content)
            if url_from_content is not None:
                pin_embed.set_image(url=url_from_content)
            await archive_channel.send(embed=pin_embed)


pin_archives_manager = PinArchivesManager()


@somsiad.bot.group(aliases=['przypinki'], invoke_without_command=True)
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def pins(ctx):
    """A group of pin-related commands."""
    embed = discord.Embed(
        title=f'Dostępne podkomendy {somsiad.conf["command_prefix"]}{ctx.invoked_with}',
        description=f'Użycie: {somsiad.conf["command_prefix"]}{ctx.invoked_with} <podkomenda>',
        color=somsiad.color
    )
    embed.add_field(
        name='kanał (kanal) <?kanał>',
        value='Ustawia <kanał> jako kanał archiwum przypiętych wiadomości. Jeśli nie podano <?kanału>, '
        'przyjmuje kanał na którym użyto komendy.',
        inline=False
    )
    embed.add_field(
        name='zarchiwizuj',
        value='Archiwizuje wiadomości przypięte na kanale na którym użyto komendy przez zapisanie ich '
        'na kanale archiwum.',
        inline=False
    )
    embed.add_field(
        name='wyczyść (wyczysc)',
        value='Odpina wszystkie wiadomości na kanale.',
        inline=False
    )

    await ctx.send(ctx.author.mention, embed=embed)


@pins.command(aliases=['kanał', 'kanal'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
@discord.ext.commands.has_permissions(manage_channels=True)
async def pins_channel(ctx, channel: discord.TextChannel = None):
    """Sets the pin archive channel of the server."""
    if channel is None:
        channel = ctx.channel

    pin_archives_manager.set_archive_channel_id(ctx.guild.id, channel.id)


    embed = discord.Embed(
        title=f':white_check_mark: Ustawiono #{channel} jako kanał archiwum przypiętych wiadomości',
        color=somsiad.color
    )

    await ctx.send(ctx.author.mention, embed=embed)


@pins.command(aliases=['zarchiwizuj'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
@discord.ext.commands.has_permissions(manage_messages=True)
async def pins_archive(ctx):
    """Archives pins in the channel where the command was invoked."""
    archive_channel_id = pin_archives_manager.get_archive_channel_id(ctx.guild.id)

    if archive_channel_id:
        archive_channel = ctx.guild.get_channel(archive_channel_id)
        if archive_channel:
            pins = await ctx.channel.pins()
            if pins:
                async with ctx.typing():
                    reversed_pins = reversed(pins)
                    for pin in reversed_pins:
                        await pin_archives_manager.archive_pin(pin, archive_channel)

                result_embed = discord.Embed(
                    title=':white_check_mark: Zarchiwizowano '
                    f'{TextFormatter.word_number_variant(len(pins), "przypinkę", "przypinki", "przypinek")}',
                    color=somsiad.color
                )
            else:
                result_embed = discord.Embed(
                    title=':red_circle: Brak przypinek do zarchiwizowania',
                    color=somsiad.color
                )
        else:
            result_embed = discord.Embed(
                title=f':warning: Ustawiony kanał archiwum przypinek już nie istnieje!',
                color=somsiad.color
            )
    else:
        result_embed = discord.Embed(
            title=f':warning: Nie ustawiono na serwerze kanału archiwum przypinek!',
            color=somsiad.color
        )

    await ctx.send(ctx.author.mention, embed=result_embed)


@pins.command(aliases=['wyczyść', 'wyczysc'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
@discord.ext.commands.has_permissions(manage_messages=True)
async def pins_clear(ctx):
    """Unpins all pins in the channel."""
    pins = await ctx.channel.pins()

    if pins:
        for pin in pins:
            await pin.unpin()

        result_embed = discord.Embed(
            title=':white_check_mark: Odpięto '
            f'{TextFormatter.word_number_variant(len(pins), "przypinkę", "przypinki", "przypinek")}',
            color=somsiad.color
        )
    else:
        result_embed = discord.Embed(
            title=':red_circle: Brak przypinek do odpięcia',
            color=somsiad.color
        )

    await ctx.send(ctx.author.mention, embed=result_embed)
