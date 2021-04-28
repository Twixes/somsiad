# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import asyncio.futures
import functools
import locale
import os
from collections import defaultdict
from numbers import Number
from somsiad import Somsiad
from typing import Optional, Union
from urllib.error import HTTPError

import discord
import pytube
from discord.ext import commands

from configuration import configuration
from core import Help, cooldown
from utilities import human_amount_of_time


class Disco(commands.Cog):
    GROUP = Help.Command(('disco', 'd'), (), 'Komendy związane z odtwarzaniem muzyki.')
    COMMANDS = (
        Help.Command(('zagraj', 'graj'), 'zapytanie/link', 'Odtwarza utwór na kanale głosowym.'),
        Help.Command(
            ('powtórz', 'powtorz', 'replay'),
            (),
            'Odtwarza od początku obecnie lub ostatnio odtwarzany na serwerze utwór.',
        ),
        Help.Command(('spauzuj', 'pauzuj', 'pauza'), (), 'Pauzuje obecnie odtwarzany utwór.'),
        Help.Command(('wznów', 'wznow'), (), 'Wznawia odtwarzanie utworu.'),
        Help.Command(('pomiń', 'pomin'), (), 'Pomija obecnie odtwarzany utwór.'),
        Help.Command(
            ('głośność', 'glosnosc', 'volume', 'vol'),
            '?nowa głośność w procentach',
            'Sprawdza głośność odtwarzania lub, jeśli podano <?nową głośność>, ustawia ją.',
        ),
        Help.Command(('rozłącz', 'rozlacz', 'stop'), (), 'Rozłącza z kanału głosowego.'),
    )
    HELP = Help(COMMANDS, '🔈', group=GROUP)

    def __init__(self, bot: Somsiad):
        self.cache_dir_path = os.path.join(bot.cache_dir_path, 'disco')
        self.bot = bot
        self.servers = defaultdict(lambda: {'volume': 1.0, 'song_url': None, 'song_audio': None})
        if not os.path.exists(self.cache_dir_path):
            os.makedirs(self.cache_dir_path)

    @staticmethod
    async def channel_connect(channel: discord.VoiceChannel):
        for _ in range(3):
            try:
                if channel.guild.voice_client is None:
                    await channel.connect()
                elif channel.guild.voice_client.channel != channel:
                    await channel.guild.voice_client.move_to(channel)
            except asyncio.futures.TimeoutError:
                continue
            else:
                break

    @staticmethod
    async def server_disconnect(server: discord.Guild) -> Optional[discord.VoiceChannel]:
        if server.me.voice is None:
            return None
        channel = server.me.voice.channel
        for _ in range(3):
            try:
                await server.voice_client.disconnect()
            except asyncio.futures.TimeoutError:
                continue
            else:
                break
        return channel

    async def channel_play_song(self, ctx: commands.Context, query: str):
        channel = ctx.author.voice.channel
        await self.channel_connect(channel)
        try:
            pytube.extract.video_id(query)
        except pytube.exceptions.RegexMatchError:
            try:
                search_result = await self.bot.youtube_client.search(query)
            except (AttributeError, HTTPError):
                video_url = None
            else:
                video_url = search_result.url if search_result is not None else None
        else:
            video_url = query
        if video_url is not None:
            video_id = pytube.extract.video_id(video_url)
            try:
                video = await self.bot.loop.run_in_executor(None, pytube.YouTube, video_url)
            except:
                embed = self.bot.generate_embed('⚠️', 'Nie można zagrać tego utworu')
                await self.bot.send(ctx, embed=embed)
            else:
                embed = self.generate_embed(channel, video, 'Pobieranie', '⏳')
                message = await self.bot.send(ctx, embed=embed)
                streams = video.streams.filter(only_audio=True).order_by('abr').desc()
                stream = streams[0]
                i = 0
                while stream.filesize > configuration['disco_max_file_size_in_mib'] * 1_048_576:
                    i += 1
                    try:
                        stream = streams[i]
                    except IndexError:
                        embed = self.generate_embed(channel, video, 'Plik zbyt duży', '⚠️')
                        break
                else:
                    path = os.path.join(self.cache_dir_path, f'{video_id} - {stream.default_filename}')
                    if not os.path.isfile(path):
                        await self.bot.loop.run_in_executor(
                            None,
                            functools.partial(
                                stream.download, output_path=self.cache_dir_path, filename_prefix=f'{video_id} - '
                            ),
                        )
                    if channel.guild.voice_client is not None:
                        channel.guild.voice_client.stop()
                    song_audio = discord.PCMVolumeTransformer(
                        discord.FFmpegPCMAudio(path), self.servers[channel.guild.id]['volume']
                    )
                    self.servers[channel.guild.id]['song_audio'] = song_audio
                    self.servers[channel.guild.id]['song_url'] = video_url

                    async def try_edit(embed: discord.Embed):
                        try:
                            await message.edit(embed=embed)
                        except (discord.Forbidden, discord.NotFound):
                            pass

                    def after(error):
                        song_audio.cleanup()
                        embed = self.generate_embed(channel, video, 'Zakończono', '⏹')
                        self.bot.loop.create_task(try_edit(embed))

                    embed = self.generate_embed(channel, video, 'Odtwarzanie', '▶️')
                    await self.channel_connect(channel)
                    channel.guild.voice_client.play(self.servers[channel.guild.id]['song_audio'], after=after)
                await message.edit(embed=embed)
        else:
            embed = self.bot.generate_embed('🙁', f'Brak wyników dla zapytania "{query}"')
            await self.bot.send(ctx, embed=embed)

    def server_change_volume(self, server: discord.Guild, volume_percentage: Number):
        volume_float = abs(float(volume_percentage)) / 100
        self.servers[server.id]['volume'] = volume_float
        if self.servers[server.id]['song_audio']:
            self.servers[server.id]['song_audio'].volume = volume_float

    def generate_embed(
        self, channel: discord.VoiceChannel, video: pytube.YouTube, status: str, emoji: str, notice: str = None
    ) -> discord.Embed:
        embed = self.bot.generate_embed(
            emoji, f'{video.title} – {notice}' if notice else video.title, url=video.watch_url
        )
        embed.set_author(name=video.author)
        embed.set_thumbnail(url=video.thumbnail_url)
        embed.add_field(name='Długość', value=human_amount_of_time(int(video.length)))
        embed.add_field(name='Kanał', value=channel.name)
        embed.add_field(name='Głośność', value=f'{int(self.servers[channel.guild.id]["volume"] * 100)}%')
        embed.add_field(name='Status', value=status)
        embed.set_footer(icon_url=self.bot.youtube_client.FOOTER_ICON_URL, text=self.bot.youtube_client.FOOTER_TEXT)
        return embed

    @commands.group(aliases=['d'], invoke_without_command=True)
    @cooldown()
    @commands.guild_only()
    async def disco(self, ctx):
        await self.bot.send(ctx, embed=self.HELP.embeds)

    @disco.command(aliases=['play', 'zagraj', 'graj', 'puść', 'pusc', 'odtwórz', 'odtworz'])
    @cooldown()
    @commands.guild_only()
    async def disco_play(self, ctx, *, query):
        """Starts playing music on the voice channel where the invoking user currently resides."""
        if ctx.author.voice is None:
            embed = discord.Embed(
                title=':warning: Nie odtworzono utworu, bo nie jesteś połączony z żadnym kanałem głosowym!',
                color=self.bot.COLOR,
            )
            await self.bot.send(ctx, embed=embed)
        else:
            async with ctx.typing():
                await self.channel_play_song(ctx, query)

    @disco_play.error
    async def disco_play_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title=f':warning: Nie podano zapytania ani linku!', color=self.bot.COLOR)
            await self.bot.send(ctx, embed=embed)

    @disco.command(aliases=['powtórz', 'powtorz', 'znów', 'znow', 'znowu', 'again', 'repeat', 'replay'])
    @cooldown()
    @commands.guild_only()
    async def disco_again(self, ctx):
        """Starts playing music on the voice channel where the invoking user currently resides."""
        if ctx.author.voice is None:
            embed = discord.Embed(
                title=':warning: Nie powtórzono utworu, bo nie jesteś połączony z żadnym kanałem głosowym!',
                color=self.bot.COLOR,
            )
            await self.bot.send(ctx, embed=embed)
        elif self.servers[ctx.guild.id]['song_url'] is None:
            embed = discord.Embed(
                title=':red_circle: Nie powtórzono utworu, bo nie ma żadnego do powtórzenia', color=self.bot.COLOR
            )
            await self.bot.send(ctx, embed=embed)
        else:
            async with ctx.typing():
                await self.channel_play_song(ctx, self.servers[ctx.guild.id]['song_url'])

    @disco.command(aliases=['pauza', 'spauzuj', 'pauzuj', 'pause'])
    @cooldown()
    @commands.guild_only()
    async def disco_pause(self, ctx):
        """Pauses the currently played song."""
        if ctx.voice_client is None:
            embed = discord.Embed(
                title=':red_circle: Nie spauzowano utworu, bo bot nie jest połączony z żadnym kanałem głosowym',
                color=self.bot.COLOR,
            )
        elif ctx.author.voice is None or (ctx.me.voice.channel and ctx.author.voice.channel != ctx.me.voice.channel):
            embed = discord.Embed(
                title=':warning: Odtwarzanie można kontrolować tylko będąc na tym samym kanale co bot!',
                color=self.bot.COLOR,
            )
        elif ctx.voice_client.is_paused():
            embed = discord.Embed(
                title=':red_circle: Nie spauzowano utworu, bo już jest spauzowany', color=self.bot.COLOR
            )
        elif not ctx.voice_client.is_playing():
            embed = discord.Embed(
                title=':red_circle: Nie spauzowano utworu, bo żaden nie jest odtwarzany', color=self.bot.COLOR
            )
        else:
            ctx.voice_client.pause()
            embed = discord.Embed(title=f':pause_button: Spauzowano utwór', color=self.bot.COLOR)
        await self.bot.send(ctx, embed=embed)

    @disco.command(aliases=['wznów', 'wznow', 'odpauzuj', 'unpause', 'resume'])
    @cooldown()
    @commands.guild_only()
    async def disco_resume(self, ctx):
        """Resumes playing song."""
        if ctx.voice_client is None:
            embed = discord.Embed(
                title=':red_circle: Nie wznowiono odtwarzania utworu, bo bot nie jest połączony z żadnym kanałem głosowym',
                color=self.bot.COLOR,
            )
        elif ctx.author.voice is None or (ctx.me.voice.channel and ctx.author.voice.channel != ctx.me.voice.channel):
            embed = discord.Embed(
                title=':warning: Odtwarzanie można kontrolować tylko będąc na tym samym kanale co bot!',
                color=self.bot.COLOR,
            )
        elif ctx.voice_client.is_playing():
            embed = discord.Embed(
                title=':red_circle: Nie wznowiono odtwarzania utworu, bo już jest odtwarzany', color=self.bot.COLOR
            )
        elif not ctx.voice_client.is_paused():
            embed = discord.Embed(
                title=':red_circle: Nie wznowiono odtwarzania utworu, bo żaden nie jest spauzowany',
                color=self.bot.COLOR,
            )
        else:
            ctx.voice_client.resume()
            embed = discord.Embed(title=f':arrow_forward: Wznowiono odtwarzanie utworu', color=self.bot.COLOR)
        await self.bot.send(ctx, embed=embed)

    @disco.command(aliases=['pomiń', 'pomin', 'skip'])
    @cooldown()
    @commands.guild_only()
    async def disco_skip(self, ctx):
        """Skips the currently played song."""
        if ctx.voice_client is None:
            embed = discord.Embed(
                title=':red_circle: Nie pominięto utworu, bo bot nie jest połączony z żadnym kanałem głosowym',
                color=self.bot.COLOR,
            )
        elif not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            embed = discord.Embed(
                title=':red_circle: Nie pominięto utworu, bo żaden nie jest odtwarzany', color=self.bot.COLOR
            )
        else:
            ctx.voice_client.stop()
            embed = discord.Embed(title=f':fast_forward: Pominięto utwór', color=self.bot.COLOR)
        await self.bot.send(ctx, embed=embed)

    @disco.command(aliases=['rozłącz', 'rozlacz', 'stop'])
    @cooldown()
    @commands.guild_only()
    async def disco_disconnect(self, ctx):
        """Disconnects from the server."""
        if ctx.voice_client is None:
            embed = discord.Embed(
                title=':warning: Nie rozłączono z kanałem głosowym, bo bot nie jest połączony z żadnym!',
                color=self.bot.COLOR,
            )
        elif (
            ctx.author.voice is None or (ctx.me.voice.channel and ctx.author.voice.channel != ctx.me.voice.channel)
        ) and len(ctx.me.voice.channel.members) > 1:
            embed = discord.Embed(
                title=':warning: Odtwarzanie można kontrolować tylko będąc na tym samym kanale co bot!',
                color=self.bot.COLOR,
            )
        else:
            voice_channel = await self.server_disconnect(ctx.guild)
            embed = discord.Embed(title=f':stop_button: Rozłączono z kanałem {voice_channel}', color=self.bot.COLOR)
        await self.bot.send(ctx, embed=embed)

    @disco.command(aliases=['głośność', 'glosnosc', 'poziom', 'volume', 'vol'])
    @cooldown()
    @commands.guild_only()
    async def disco_volume(self, ctx, volume_percentage: Union[int, locale.atoi] = None):
        """Sets the volume."""
        if volume_percentage is None:
            embed = discord.Embed(
                title=':level_slider: Głośność ustawiona jest na '
                f'{int(self.servers[ctx.guild.id]["volume"] * 100)}%',
                color=self.bot.COLOR,
            )
        else:
            if ctx.voice_client is not None and (
                ctx.author.voice is None or (ctx.me.voice.channel and ctx.author.voice.channel != ctx.me.voice.channel)
            ):
                embed = discord.Embed(
                    title=':warning: Odtwarzanie można kontrolować tylko będąc na tym samym kanale co bot!',
                    color=self.bot.COLOR,
                )
            else:
                self.server_change_volume(ctx.guild, volume_percentage)
                embed = discord.Embed(
                    title=':level_slider: Ustawiono głośność na ' f'{int(self.servers[ctx.guild.id]["volume"] * 100)}%',
                    color=self.bot.COLOR,
                )
        await self.bot.send(ctx, embed=embed)

    @disco_volume.error
    async def disco_volume_error(self, ctx, error):
        if isinstance(error, commands.BadUnionArgument):
            embed = discord.Embed(title=f':warning: Podana wartość nie jest liczbą całkowitą!', color=self.bot.COLOR)
            await self.bot.send(ctx, embed=embed)


def setup(bot: Somsiad):
    if bot.youtube_client is not None:
        bot.add_cog(Disco(bot))
