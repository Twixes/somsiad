# Copyright 2018-2019 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Optional, Union
from numbers import Number
from collections import defaultdict
import os
import locale
import discord
from discord.ext import commands
import pytube
from core import Help, somsiad, youtube_client
from utilities import human_amount_of_time
from configuration import configuration


class DiscoManager:
    _CACHE_DIR_PATH = os.path.join(somsiad.cache_dir_path, 'disco')

    def __init__(self):
        self.servers = defaultdict(lambda: {'volume': 1.0, 'song_url': None, 'song_audio': None})
        if not os.path.exists(self._CACHE_DIR_PATH):
            os.makedirs(self._CACHE_DIR_PATH)

    @staticmethod
    async def channel_connect(channel: discord.VoiceChannel):
        if channel.guild.voice_client is None:
            await channel.connect()
        elif channel.guild.me.voice.channel != channel:
            await channel.guild.voice_client.move_to(channel)

    @staticmethod
    async def server_disconnect(server: discord.Guild) -> Optional[discord.VoiceChannel]:
        if server.me.voice is None:
            return None
        else:
            channel = server.me.voice.channel
            await server.voice_client.disconnect()
            return channel

    async def channel_play_song(self, ctx: commands.Context, query: str):
        channel = ctx.author.voice.channel
        await self.channel_connect(channel)
        try:
            pytube.extract.video_id(query)
        except pytube.exceptions.RegexMatchError:
            search_result = await youtube_client.search(query)
            video_url = search_result.url if search_result is not None else None
        else:
            video_url = query
        if video_url is not None:
            video = await somsiad.loop.run_in_executor(None, pytube.YouTube, video_url)
            embed = self.generate_embed(channel, video, 'Pobieranie', '⏳')
            message = await somsiad.send(ctx, embed=embed)
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
                path = os.path.join(self._CACHE_DIR_PATH, stream.default_filename)
                if not os.path.isfile(path):
                    await somsiad.loop.run_in_executor(None, stream.download, self._CACHE_DIR_PATH)
                if channel.guild.voice_client is not None:
                    channel.guild.voice_client.stop()
                song_audio = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(path), self.servers[channel.guild.id]['volume']
                )
                self.servers[channel.guild.id]['song_audio'] = song_audio
                self.servers[channel.guild.id]['song_url'] = video_url
                def after(error):
                    song_audio.cleanup()
                    embed = self.generate_embed(channel, video, 'Zakończono', '⏹')
                    somsiad.loop.create_task(message.edit(embed=embed))
                embed = self.generate_embed(channel, video, 'Odtwarzanie', '▶️')
                channel.guild.voice_client.play(self.servers[channel.guild.id]['song_audio'], after=after)
            await message.edit(embed=embed)
        else:
            embed = somsiad.generate_embed('🙁', f'Brak wyników dla zapytania "{query}"')
            await somsiad.send(ctx, embed=embed)

    def server_change_volume(self, server: discord.Guild, volume_percentage: Number):
        volume_float = abs(float(volume_percentage)) / 100
        self.servers[server.id]['volume'] = volume_float
        if self.servers[server.id]['song_audio']:
            self.servers[server.id]['song_audio'].volume = volume_float

    def generate_embed(
            self, channel: discord.VoiceChannel, video: pytube.YouTube, status: str, emoji: str, notice: str = None
    ) -> discord.Embed:
        embed = somsiad.generate_embed(
            emoji, f'{video.title} – {notice}' if notice else video.title, url=video.watch_url
        )
        embed.set_author(name=video.author)
        embed.set_thumbnail(url=video.thumbnail_url)
        embed.add_field(name='Status', value=status)
        embed.add_field(name='Kanał', value=channel.name)
        embed.add_field(name='Głośność', value=f'{int(self.servers[channel.guild.id]["volume"] * 100)}%')
        embed.add_field(name='Długość', value=human_amount_of_time(int(video.length)))
        embed.set_footer(icon_url=youtube_client.FOOTER_ICON_URL, text=youtube_client.FOOTER_TEXT)
        return embed


disco_manager = DiscoManager()

GROUP = Help.Command(('disco', 'd'), (), 'Grupa komend związanych z odtwarzaniem muzyki.')
COMMANDS = (
    Help.Command(('zagraj', 'graj'), 'zapytanie/link', 'Odtwarza utwór na kanale głosowym.'),
    Help.Command(
        ('powtórz', 'powtorz', 'replay'), (), 'Odtwarza od początku obecnie lub ostatnio odtwarzany na serwerze utwór.'
    ),
    Help.Command(('spauzuj', 'pauzuj', 'pauza'), (), 'Pauzuje obecnie odtwarzany utwór.'),
    Help.Command(('wznów', 'wznow'), (), 'Wznawia odtwarzanie utworu.'),
    Help.Command(('pomiń', 'pomin'), (), 'Pomija obecnie odtwarzany utwór.'),
    Help.Command(
        ('głośność', 'glosnosc', 'volume', 'vol'), '?nowa głośność w procentach',
        'Sprawdza głośność odtwarzania lub, jeśli podano <?nową głośność>, ustawia ją.'
    ),
    Help.Command(('rozłącz', 'rozlacz', 'stop'), (), 'Rozłącza z kanału głosowego.'),
)
HELP = Help(COMMANDS, group=GROUP)


@somsiad.group(aliases=['d'], invoke_without_command=True)
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
)
@commands.guild_only()
async def disco(ctx):
    await somsiad.send(ctx, embeds=HELP.embeds)


@disco.command(aliases=['play', 'zagraj', 'graj', 'puść', 'pusc', 'odtwórz', 'odtworz'])
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default
)
@commands.guild_only()
async def disco_play(ctx, *, query):
    """Starts playing music on the voice channel where the invoking user currently resides."""
    if ctx.author.voice is None:
        embed = discord.Embed(
            title=':warning: Nie odtworzono utworu, bo nie jesteś połączony z żadnym kanałem głosowym!',
            color=somsiad.COLOR
        )
        await somsiad.send(ctx, embed=embed)
    else:
        async with ctx.typing():
            await disco_manager.channel_play_song(ctx, query)


@disco_play.error
async def disco_play_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title=f':warning: Nie podano zapytania ani linku!',
            color=somsiad.COLOR
        )
        await somsiad.send(ctx, embed=embed)


@disco.command(aliases=['powtórz', 'powtorz', 'znów', 'znow', 'znowu', 'again', 'repeat', 'replay'])
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default
)
@commands.guild_only()
async def disco_again(ctx):
    """Starts playing music on the voice channel where the invoking user currently resides."""
    if ctx.author.voice is None:
        embed = discord.Embed(
            title=':warning: Nie powtórzono utworu, bo nie jesteś połączony z żadnym kanałem głosowym!',
            color=somsiad.COLOR
        )
        await somsiad.send(ctx, embed=embed)
    elif disco_manager.servers[ctx.guild.id]['song_url'] is None:
        embed = discord.Embed(
            title=':red_circle: Nie powtórzono utworu, bo nie ma żadnego do powtórzenia',
            color=somsiad.COLOR
        )
        await somsiad.send(ctx, embed=embed)
    else:
        async with ctx.typing():
            await disco_manager.channel_play_song(ctx, disco_manager.servers[ctx.guild.id]['song_url'])


@disco.command(aliases=['pauza', 'spauzuj', 'pauzuj', 'pause'])
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default
)
@commands.guild_only()
async def disco_pause(ctx):
    """Pauses the currently played song."""
    if ctx.voice_client is None:
        embed = discord.Embed(
            title=':red_circle: Nie spauzowano utworu, bo bot nie jest połączony z żadnym kanałem głosowym',
            color=somsiad.COLOR
        )
    elif ctx.author.voice is None or ctx.author.voice.channel != ctx.me.voice.channel:
        embed = discord.Embed(
            title=':warning: Odtwarzanie można kontrolować tylko będąc na tym samym kanale co bot!',
            color=somsiad.COLOR
        )
    elif ctx.voice_client.is_paused():
        embed = discord.Embed(
            title=':red_circle: Nie spauzowano utworu, bo już jest spauzowany',
            color=somsiad.COLOR
        )
    elif not ctx.voice_client.is_playing():
        embed = discord.Embed(
            title=':red_circle: Nie spauzowano utworu, bo żaden nie jest odtwarzany',
            color=somsiad.COLOR
        )
    else:
        ctx.voice_client.pause()
        embed = discord.Embed(
            title=f':pause_button: Spauzowano utwór',
            color=somsiad.COLOR
        )
    await somsiad.send(ctx, embed=embed)


@disco.command(aliases=['wznów', 'wznow', 'odpauzuj', 'unpause', 'resume'])
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default
)
@commands.guild_only()
async def disco_resume(ctx):
    """Resumes playing song."""
    if ctx.voice_client is None:
        embed = discord.Embed(
            title=':red_circle: Nie wznowiono odtwarzania utworu, bo bot nie jest połączony z żadnym kanałem głosowym',
            color=somsiad.COLOR
        )
    elif ctx.author.voice is None or ctx.author.voice.channel != ctx.me.voice.channel:
        embed = discord.Embed(
            title=':warning: Odtwarzanie można kontrolować tylko będąc na tym samym kanale co bot!',
            color=somsiad.COLOR
        )
    elif ctx.voice_client.is_playing():
        embed = discord.Embed(
            title=':red_circle: Nie wznowiono odtwarzania utworu, bo już jest odtwarzany',
            color=somsiad.COLOR
        )
    elif not ctx.voice_client.is_paused():
        embed = discord.Embed(
            title=':red_circle: Nie wznowiono odtwarzania utworu, bo żaden nie jest spauzowany',
            color=somsiad.COLOR
        )
    else:
        ctx.voice_client.resume()
        embed = discord.Embed(
            title=f':arrow_forward: Wznowiono odtwarzanie utworu',
            color=somsiad.COLOR
        )
    await somsiad.send(ctx, embed=embed)


@disco.command(aliases=['pomiń', 'pomin', 'skip'])
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default
)
@commands.guild_only()
async def disco_skip(ctx):
    """Skips the currently played song."""
    if ctx.voice_client is None:
        embed = discord.Embed(
            title=':red_circle: Nie pominięto utworu, bo bot nie jest połączony z żadnym kanałem głosowym',
            color=somsiad.COLOR
        )
    elif not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        embed = discord.Embed(
            title=':red_circle: Nie pominięto utworu, bo żaden nie jest odtwarzany',
            color=somsiad.COLOR
        )
    else:
        ctx.voice_client.stop()
        embed = discord.Embed(
            title=f':fast_forward: Pominięto utwór',
            color=somsiad.COLOR
        )
    await somsiad.send(ctx, embed=embed)


@disco.command(aliases=['rozłącz', 'rozlacz', 'stop'])
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default
)
@commands.guild_only()
async def disco_disconnect(ctx):
    """Disconnects from the server."""
    if ctx.voice_client is None:
        embed = discord.Embed(
            title=':warning: Nie rozłączono z kanałem głosowym, bo bot nie jest połączony z żadnym!',
            color=somsiad.COLOR
        )
    elif ctx.author.voice is None or ctx.author.voice.channel != ctx.me.voice.channel:
        embed = discord.Embed(
            title=':warning: Odtwarzanie można kontrolować tylko będąc na tym samym kanale co bot!',
            color=somsiad.COLOR
        )
    else:
        voice_channel = await disco_manager.server_disconnect(ctx.guild)
        embed = discord.Embed(
            title=f':stop_button: Rozłączono z kanałem {voice_channel}',
            color=somsiad.COLOR
        )
    await somsiad.send(ctx, embed=embed)


@disco.command(aliases=['głośność', 'glosnosc', 'poziom', 'volume', 'vol'])
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default
)
@commands.guild_only()
async def disco_volume(ctx, volume_percentage: Union[int, locale.atoi] = None):
    """Sets the volume."""
    if volume_percentage is None:
        embed = discord.Embed(
            title=':level_slider: Głośność ustawiona jest na '
            f'{int(disco_manager.servers[ctx.guild.id]["volume"] * 100)}%',
            color=somsiad.COLOR
        )
    else:
        if (
                ctx.voice_client is not None
                and (ctx.author.voice is None or ctx.author.voice.channel != ctx.me.voice.channel)
        ):
            embed = discord.Embed(
                title=':warning: Odtwarzanie można kontrolować tylko będąc na tym samym kanale co bot!',
                color=somsiad.COLOR
            )
        else:
            disco_manager.server_change_volume(ctx.guild, volume_percentage)
            embed = discord.Embed(
                title=':level_slider: Ustawiono głośność na '
                f'{int(disco_manager.servers[ctx.guild.id]["volume"] * 100)}%',
                color=somsiad.COLOR
            )
    await somsiad.send(ctx, embed=embed)


@disco_volume.error
async def disco_volume_error(ctx, error):
    if isinstance(error, commands.BadUnionArgument):
        embed = discord.Embed(
            title=f':warning: Podana wartość nie jest liczbą całkowitą!',
            color=somsiad.COLOR
        )
        await somsiad.send(ctx, embed=embed)
