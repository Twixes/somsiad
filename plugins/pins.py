# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import io
import discord
from discord.ext import commands
from core import ServerSpecific, ChannelRelated, Help, cooldown
from utilities import first_url, word_number_form
import data

channel_being_processed_for_servers = {}


class PinArchive(data.Base, ServerSpecific, ChannelRelated):
    async def archive(self, bot: commands.Bot, channel: discord.TextChannel) -> int:
        """Archives the provided message."""
        archive_channel = self.discord_channel
        messages = await channel.pins()
        if not messages:
            raise ValueError
        channel_being_processed_for_servers[channel.guild.id] = channel
        for message in reversed(messages):
            await self._archive_message(bot, archive_channel, message)
        return len(messages)

    async def _archive_message(self, bot: commands.Bot, archive_channel: discord.TextChannel, message: discord.Message):
        pin_embed = bot.generate_embed(description=message.content, timestamp=message.created_at)
        pin_embed.set_author(name=message.author.display_name, url=message.jump_url, icon_url=message.author.avatar_url)
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


class Pins(commands.Cog):
    GROUP = Help.Command(
        ('przypięte', 'przypinki', 'piny'), (), 'Komendy związane z archiwizacją przypiętych wiadomości.'
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
    HELP = Help(COMMANDS, '📌', group=GROUP)

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(aliases=['przypięte', 'przypinki', 'piny'], invoke_without_command=True, case_insensitive=True)
    @cooldown()
    async def pins(self, ctx):
        """A group of pin-related commands."""
        await self.bot.send(ctx, embeds=self.HELP.embeds)

    @pins.command(aliases=['kanał', 'kanal'])
    @cooldown()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def pins_channel(self, ctx, channel: discord.TextChannel = None):
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
            embed = self.bot.generate_embed('✅', f'Ustawiono #{channel} jako kanał archiwum przypiętych wiadomości')
        else:
            if pin_archive is not None and pin_archive.channel_id is not None:
                notice = f'Kanałem archiwum przypiętych wiadomości jest #{pin_archive.discord_channel}'
            else:
                notice = 'Nie ustawiono na serwerze kanału archiwum przypiętych wiadomości'
            embed = self.bot.generate_embed('🗃️', notice)
        await self.bot.send(ctx, embed=embed)

    @pins_channel.error
    async def pins_channel_error(self, ctx, error):
        notice = None
        if isinstance(error, commands.BadArgument):
            notice = 'Nie znaleziono podanego kanału na serwerze'
        elif isinstance(error, commands.MissingPermissions):
            notice = (
                'Do sprawdzenia lub zmiany kanału archiwum przypiętych wiadomości potrzebne są '
                'uprawnienia do zarządzania kanałami'
            )
        if notice is not None:
            embed = self.bot.generate_embed('⚠️', notice)
            await self.bot.send(ctx, embed=embed)

    @pins.command(aliases=['archiwizuj', 'zarchiwizuj'])
    @cooldown()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def pins_archive(self, ctx):
        """Archives pins in the channel where the command was invoked."""
        async with ctx.typing():
            with data.session() as session:
                pin_archive = session.query(PinArchive).get(ctx.guild.id)
                if pin_archive is None or pin_archive.channel_id is None:
                    emoji, notice = '⚠️', 'Nie ustawiono na serwerze kanału archiwum przypiętych wiadomości'
                elif pin_archive.discord_channel is None:
                    emoji, notice = '⚠️', 'Ustawiony kanał archiwum przypiętych wiadomości już nie istnieje'
                elif channel_being_processed_for_servers.get(ctx.guild.id) is not None:
                    emoji, notice = (
                        '🔴', 'Na serwerze właśnie trwa przetwarzanie kanału '
                        f'#{channel_being_processed_for_servers[ctx.guild.id]}'
                    )
                else:
                    channel_being_processed_for_servers[ctx.guild.id] = pin_archive.discord_channel
                    try:
                        try:
                            async with pin_archive.discord_channel.typing():
                                archived = await pin_archive.archive(self.bot, ctx.channel)
                        except ValueError:
                            emoji, notice = '🔴', 'Brak przypiętych wiadomości do zarchiwizowania'
                        else:
                            forms = ('przypiętą wiadomość', 'przypięte wiadomości', 'przypiętych wiadomości')
                            emoji, notice = '✅', f'Zarchiwizowano {word_number_form(archived, *forms)}'
                    except:
                        raise
                    finally:
                        channel_being_processed_for_servers[ctx.guild.id] = None
            embed = self.bot.generate_embed(emoji, notice)
            await self.bot.send(ctx, embed=embed)

    @pins.command(aliases=['wyczyść', 'wyczysc'])
    @cooldown()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def pins_clear(self, ctx):
        """Unpins all pins in the channel."""
        async with ctx.typing():
            messages = await ctx.channel.pins()
            if not messages:
                emoji, notice = '🔴', 'Brak przypiętych wiadomości do odpięcia'
            elif channel_being_processed_for_servers.get(ctx.guild.id) == ctx.channel:
                emoji, notice = '🔴', 'Ten kanał jest właśnie przetwarzany'
            else:
                channel_being_processed_for_servers[ctx.guild.id] = ctx.channel
                try:
                    for pin in messages:
                        await pin.unpin()
                except:
                    raise
                else:
                    forms = ('przypiętą wiadomość', 'przypięte wiadomości', 'przypiętych wiadomości')
                    emoji, notice = '✅', f'Odpięto {word_number_form(len(messages), *forms)}'
                finally:
                    channel_being_processed_for_servers[ctx.guild.id] = None
            embed = self.bot.generate_embed(emoji, notice)
            await self.bot.send(ctx, embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Pins(bot))
