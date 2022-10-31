# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import io
from typing import Dict, List, cast

import discord
from discord.ext import commands

import data
from core import Help, cooldown, has_permissions
from somsiad import Somsiad, SomsiadMixin
from utilities import first_url, word_number_form

channel_being_processed_for_servers = {}


class PinArchive(data.ServerSpecific, data.ChannelRelated, data.Base):
    class ChannelNotFound(Exception):
        pass

    async def archive(self, bot: commands.Bot, channel: discord.TextChannel) -> Dict[str, int]:
        """Archives the provided message."""
        archive_channel = self.discord_channel(bot)
        if archive_channel is None:
            raise self.ChannelNotFound()
        messages = await channel.pins()
        if not messages:
            raise ValueError
        channel_being_processed_for_servers[channel.guild.id] = channel
        archivization_counts = {'successful': 0, 'too_large': 0, 'unknown_error': 0}
        for message in reversed(messages):
            try:
                await self._archive_message(bot, archive_channel, message)
                archivization_counts['successful'] += 1
            except discord.HTTPException:
                archivization_counts['too_large'] += 1
            except:
                archivization_counts['unknown_error'] += 1
        return archivization_counts

    async def _archive_message(self, bot: Somsiad, archive_channel: discord.TextChannel, message: discord.Message):
        pin_embed = bot.generate_embed(description=message.content, timestamp=message.created_at)
        pin_embed.set_author(name=message.author.display_name, url=message.jump_url, icon_url=message.author.display_avatar.url)
        pin_embed.set_footer(text=f'#{message.channel}')
        files: List[discord.File] = []
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
            url_from_content = cast(str, first_url(message.content))
            if url_from_content is not None:
                pin_embed.set_image(url=url_from_content)
            await archive_channel.send(embed=pin_embed)


class Pins(commands.Cog, SomsiadMixin):
    GROUP = Help.Command(
        ('przypięte', 'przypinki', 'piny'), (), 'Komendy związane z archiwizacją przypiętych wiadomości.'
    )
    COMMANDS = (
        Help.Command(
            ('kanał', 'kanal'),
            '?kanał',
            'Jeśli podano <?kanał>, ustawia go jako serwerowy kanał archiwum przypiętych wiadomości. '
            'W przeciwnym razie pokazuje jaki kanał obecnie jest archiwum przypiętych wiadomości.',
        ),
        Help.Command(
            ('archiwizuj', 'zarchiwizuj'),
            (),
            'Archiwizuje wiadomości przypięte na kanale na którym użyto komendy przez zapisanie ich na kanale archiwum.',
        ),
        Help.Command(('wyczyść', 'wyczysc'), (), 'Odpina wszystkie wiadomości na kanale.'),
    )
    HELP = Help(COMMANDS, '📌', group=GROUP)

    @cooldown()
    @commands.group(aliases=['przypięte', 'przypinki', 'piny'], invoke_without_command=True, case_insensitive=True)
    async def pins(self, ctx):
        """A group of pin-related commands."""
        await self.bot.send(ctx, embed=self.HELP.embeds)

    @cooldown()
    @pins.command(aliases=['kanał', 'kanal'])
    @commands.guild_only()
    @has_permissions(manage_channels=True)
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
                notice = f'Kanałem archiwum przypiętych wiadomości jest #{pin_archive.discord_channel(self.bot)}'
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

    @cooldown()
    @pins.command(aliases=['archiwizuj', 'zarchiwizuj'])
    @commands.guild_only()
    @has_permissions(manage_messages=True)
    async def pins_archive(self, ctx):
        """Archives pins in the channel where the command was invoked."""
        async with ctx.typing():
            with data.session() as session:
                pin_archive = session.query(PinArchive).get(ctx.guild.id)
                description = None
                if pin_archive is None or pin_archive.channel_id is None:
                    emoji, notice = '⚠️', 'Nie ustawiono na serwerze kanału archiwum przypiętych wiadomości'
                elif pin_archive.discord_channel(self.bot) is None:
                    emoji, notice = '⚠️', 'Ustawiony kanał archiwum przypiętych wiadomości już nie istnieje'
                elif channel_being_processed_for_servers.get(ctx.guild.id) is not None:
                    emoji, notice = (
                        '🔴',
                        'Na serwerze właśnie trwa przetwarzanie kanału '
                        f'#{channel_being_processed_for_servers[ctx.guild.id]}',
                    )
                else:
                    channel_being_processed_for_servers[ctx.guild.id] = pin_archive.discord_channel(self.bot)
                    try:
                        try:
                            async with channel_being_processed_for_servers[ctx.guild.id].typing():
                                archivization_counts = await pin_archive.archive(self.bot, ctx.channel)
                        except ValueError:
                            emoji, notice = '🔴', 'Brak przypiętych wiadomości do zarchiwizowania'
                        except PinArchive.ChannelNotFound:
                            emoji, notice = '⚠️', 'Musisz ustawić nowy kanał archiwum przypiętych wiadomości'
                        else:
                            pinned_forms = ('przypiętą wiadomość', 'przypięte wiadomości', 'przypiętych wiadomości')
                            emoji = '✅'
                            notice = (
                                'Zarchiwizowano '
                                f'{word_number_form(archivization_counts["successful"], *pinned_forms)}'
                            )
                            description_parts = []
                            forms = ('wiadomość', 'wiadomości')
                            if archivization_counts['too_large'] > 0:
                                description_parts.append(
                                    f'{word_number_form(archivization_counts["too_large"], *forms)} pominięto z '
                                    'powodu zbyt dużego rozmiaru.'
                                )
                            if archivization_counts['unknown_error'] > 0:
                                description_parts.append(
                                    f'{word_number_form(archivization_counts["unknown_error"], *forms)} '
                                    'pominięto z powodu niespodziewanych błędów.'
                                )
                            if description_parts:
                                description = '\n'.join(description_parts)
                    except:
                        raise
                    finally:
                        channel_being_processed_for_servers[ctx.guild.id] = None
            embed = self.bot.generate_embed(emoji, notice, description)
            await self.bot.send(ctx, embed=embed)

    @cooldown()
    @pins.command(aliases=['wyczyść', 'wyczysc'])
    @commands.guild_only()
    @has_permissions(manage_messages=True)
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


async def setup(bot: Somsiad):
    await bot.add_cog(Pins(bot))
