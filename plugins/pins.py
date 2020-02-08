# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import io
from collections import defaultdict
import discord
from core import ServerSpecific, ChannelRelated, somsiad, Help
from utilities import first_url, word_number_form
from configuration import configuration
import data

channel_being_processed_for_servers = defaultdict()


class PinArchive(data.Base, ServerSpecific, ChannelRelated):
    async def archive(self, channel: discord.TextChannel) -> int:
        """Archives the provided message."""
        archive_channel = self.discord_channel
        messages = await channel.pins()
        if not messages:
            raise ValueError
        channel_being_processed_for_servers[channel.guild.id] = channel
        for message in reversed(messages):
            await self._archive_message(archive_channel, message)
        return len(messages)

    async def _archive_message(self, archive_channel: discord.TextChannel, message: discord.Message):
        pin_embed = discord.Embed(
            description=message.content,
            color=somsiad.COLOR,
            timestamp=message.created_at
        )
        pin_embed.set_author(
            name=message.author.display_name,
            url=message.jump_url,
            icon_url=message.author.avatar_url
        )
        pin_embed.set_footer(text=f'#{message.channel}')

        files = []
        for attachment in message.attachments:
            filename = attachment.filename
            fp = io.BytesIO()
            await attachment.save(fp)
            file = discord.File(fp, filename)
            files.append(file)

        if len(files) == 1:
            if message.attachments[0].height is not None:
                pin_embed.set_image(url=f'attachment://{message.attachments[0].filename}')
            await archive_channel.send(embed=pin_embed, file=files[0])
        elif len(files) > 1:
            await archive_channel.send(embed=pin_embed, files=files)
        else:
            url_from_content = first_url(message.content)
            if url_from_content is not None:
                pin_embed.set_image(url=url_from_content)
            await archive_channel.send(embed=pin_embed)


GROUP = Help.Command(
    ('przypięte', 'przypinki', 'piny'), (), 'Grupa komend związanych z archiwizacją przypiętych wiadomości.'
)
COMMANDS = (
    Help.Command(
        ('kanał', 'kanal'), '?kanał',
        'Jeśli podano <?kanał>, ustawia go jako serwerowy kanał archiwum przypiętych wiadomości. '
        'W przeciwnym razie pokazuje jaki kanał obecnie jest archiwum przypiętych wiadomości.'
    ),
    Help.Command(
        ('archiwizuj', 'zarchiwizuj'), (),
        'Archiwizuje wiadomości przypięte na kanale na którym użyto komendy przez zapisanie ich na kanale archiwum.'
    ),
    Help.Command(
        ('wyczyść', 'wyczysc'), (), 'Odpina wszystkie wiadomości na kanale.'
    )
)
HELP = Help(COMMANDS, group=GROUP)


@somsiad.group(aliases=['przypięte', 'przypinki', 'piny'], invoke_without_command=True, case_insensitive=True)
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def pins(ctx):
    """A group of pin-related commands."""
    await somsiad.send(ctx, embeds=HELP.embeds)


@pins.command(aliases=['kanał', 'kanal'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
@discord.ext.commands.has_permissions(manage_channels=True)
async def pins_channel(ctx, channel: discord.TextChannel = None):
    """Sets the pin archive channel of the server."""
    session = data.Session()
    pin_archive = session.query(PinArchive).get(ctx.guild.id)
    if channel is not None:
        if pin_archive:
            pin_archive.channel_id = channel.id
        else:
            pin_archive = PinArchive(server_id=ctx.guild.id, channel_id=channel.id)
            session.add(pin_archive)
        session.commit()
        session.close()
        embed = discord.Embed(
            title=f':white_check_mark: Ustawiono #{channel} jako kanał archiwum przypiętych wiadomości',
            color=somsiad.COLOR
        )
    else:
        if pin_archive is not None and pin_archive.channel_id is not None:
            embed = discord.Embed(
                title=f':card_box: Kanałem archiwum przypiętych wiadomości jest #{pin_archive.discord_channel}',
                color=somsiad.COLOR
            )
        else:
            embed = discord.Embed(
                title=':card_box: Nie ustawiono na serwerze kanału archiwum przypiętych wiadomości',
                color=somsiad.COLOR
            )
    await somsiad.send(ctx, embed=embed)


@pins_channel.error
async def pins_channel_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Nie znaleziono podanego kanału na serwerze',
            color=somsiad.COLOR
        )
        await somsiad.send(ctx, embed=embed)
    elif isinstance(error, discord.ext.commands.MissingPermissions):
        embed = discord.Embed(
            title=':warning: Do sprawdzenia lub zmiany kanału archiwum przypiętych wiadomości potrzebne są '
            'uprawnienia do zarządzania kanałami',
            color=somsiad.COLOR
        )
        await somsiad.send(ctx, embed=embed)


@pins.command(aliases=['archiwizuj', 'zarchiwizuj'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
@discord.ext.commands.has_permissions(manage_messages=True)
async def pins_archive(ctx):
    """Archives pins in the channel where the command was invoked."""
    session = data.Session()
    pin_archive = session.query(PinArchive).get(ctx.guild.id)
    if pin_archive is None or pin_archive.channel_id is None:
        embed = discord.Embed(
            title=':warning: Nie ustawiono na serwerze kanału archiwum przypiętych wiadomości',
            color=somsiad.COLOR
        )
    else:
        pin_archive_channel = pin_archive.discord_channel
        if pin_archive_channel is None:
            embed = discord.Embed(
                title=':warning: Ustawiony kanał archiwum przypiętych wiadomości już nie istnieje',
                color=somsiad.COLOR
            )
        else:
            if channel_being_processed_for_servers[ctx.guild.id] is None:
                channel_being_processed_for_servers[ctx.guild.id] = pin_archive.discord_channel
                try:
                    async with ctx.typing():
                        try:
                            archived = await pin_archive.archive(ctx.channel)
                        except ValueError:
                            embed = discord.Embed(
                                title=':red_circle: Brak przypiętych wiadomości do zarchiwizowania',
                                color=somsiad.COLOR
                            )
                        else:
                            embed = discord.Embed(
                                title=':white_check_mark: Zarchiwizowano '
                                f'{word_number_form(archived, "przypiętą wiadomość", "przypięte wiadomości", "przypiętych wiadomości")}',
                                color=somsiad.COLOR
                            )
                except:
                    raise
                finally:
                    channel_being_processed_for_servers[ctx.guild.id] = None
            else:
                embed = discord.Embed(
                    title=':red_circle: Na serwerze właśnie trwa przetwarzanie kanału '
                    f'#{channel_being_processed_for_servers[ctx.guild.id]}',
                    color=somsiad.COLOR
                )
    session.close()
    await somsiad.send(ctx, embed=embed)


@pins.command(aliases=['wyczyść', 'wyczysc'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
@discord.ext.commands.has_permissions(manage_messages=True)
async def pins_clear(ctx):
    """Unpins all pins in the channel."""
    messages = await ctx.channel.pins()
    if not messages:
        embed = discord.Embed(
            title=':red_circle: Brak przypiętych wiadomości do odpięcia',
            color=somsiad.COLOR
        )
    elif channel_being_processed_for_servers[ctx.guild.id] == ctx.channel:
        embed = discord.Embed(
            title=':red_circle: Ten kanał jest właśnie przetwarzany',
            color=somsiad.COLOR
        )
    else:
        channel_being_processed_for_servers[ctx.guild.id] = ctx.channel
        try:
            for pin in messages: await pin.unpin()
        except Exception as e:
            raise e
        else:
            embed = discord.Embed(
                title=':white_check_mark: Odpięto '
                f'{word_number_form(len(messages), "przypiętą wiadomość", "przypięte wiadomości", "przypiętych wiadomości")}',
                color=somsiad.COLOR
            )
        finally:
            channel_being_processed_for_servers[ctx.guild.id] = None
    await somsiad.send(ctx, embed=embed)
