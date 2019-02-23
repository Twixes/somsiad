# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import os
import locale
from typing import Optional, Union, Dict, Any
from numbers import Number
import discord
import youtube_dl
from somsiad import somsiad
from utilities import TextFormatter
from plugins.help_message import Helper


class DiscoManager:
    FOOTER_TEXT_YOUTUBE = 'YouTube'
    FOOTER_ICON_URL_YOUTUBE = (
        'https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/'
        'YouTube_full-color_icon_%282017%29.svg/60px-YouTube_full-color_icon_%282017%29.svg.png'
    )
    FOOTER_TEXT_SOUNDCLOUD = 'SoundCloud'
    FOOTER_ICON_URL_SOUNDCLOUD = 'https://a-v2.sndcdn.com/assets/images/sc-icons/favicon-2cadd14b.ico'
    FOOTER_TEXT_VIMEO = 'Vimeo'
    FOOTER_ICON_URL_VIMEO = 'https://i.vimeocdn.com/favicon/main-touch_60'

    _CACHE_DIR_PATH = os.path.join(somsiad.cache_dir_path, 'disco')
    _YOUTUBE_DL_OPTIONS = {
        'format': 'bestaudio[ext=mp3]/bestaudio[ext=m4a]',
        'extractaudio': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': somsiad.conf['disco_max_file_size_in_mib'] * 2 ** 20,
        'outtmpl': os.path.join(_CACHE_DIR_PATH, '%(id)s'),
        'default_search': 'auto'
    }

    def __init__(self):
        if not discord.opus.is_loaded():
            discord.opus.load_opus('opus')
        if not os.path.exists(self._CACHE_DIR_PATH):
            os.makedirs(self._CACHE_DIR_PATH)
        self._youtube_dl = youtube_dl.YoutubeDL(self._YOUTUBE_DL_OPTIONS)
        self.servers = {}

    def ensure_server_registration(self, server: discord.Guild) -> Dict[str, Any]:
        if server.id not in self.servers:
            self.servers[server.id] = {}
            self.servers[server.id]['volume'] = 1.0
            self.servers[server.id]['song_url'] = None
            self.servers[server.id]['song_audio'] = None

        return self.servers[server.id]

    @staticmethod
    async def channel_connect(voice_channel: discord.VoiceChannel):
        if voice_channel.guild.me.voice is None:
            await voice_channel.connect()
        elif voice_channel.guild.me.voice.channel != voice_channel:
            await voice_channel.guild.voice_client.move_to(voice_channel)

    @staticmethod
    async def server_disconnect(server: discord.Guild) -> Optional[discord.VoiceChannel]:
        if server.me.voice is None:
            return None
        else:
            voice_channel = server.me.voice.channel
            await server.voice_client.disconnect()
            return voice_channel

    async def channel_play_song(self, voice_channel: discord.VoiceChannel, query: str) -> Optional[dict]:
        await self.channel_connect(voice_channel)
        song_info = self._youtube_dl.extract_info(query, download=False)

        if song_info is not None:

            if 'search' in song_info['extractor']:
                song_filename = song_info["entries"][0]["id"]
            else:
                song_filename = song_info["id"]

            if not os.path.isfile(os.path.join(self._CACHE_DIR_PATH, song_filename)):
                with self._youtube_dl:
                    self._youtube_dl.download([query])

            if os.path.isfile(os.path.join(self._CACHE_DIR_PATH, song_filename)):
                song_path = os.path.join(self._CACHE_DIR_PATH, song_filename)

                voice_channel.guild.voice_client.stop()

                song_audio = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(song_path), self.servers[voice_channel.guild.id]['volume']
                )
                self.servers[voice_channel.guild.id]['song_audio'] = song_audio

                def after(error):
                    song_audio.cleanup()

                voice_channel.guild.voice_client.play(self.servers[voice_channel.guild.id]['song_audio'], after=after)

                song_status = 2 # means that song can be played
            else:
                song_status = 1 # means that file size limit was exceeded
        else:
            song_status = 0 # means that no song was found

        embed = self._generate_song_embed(
            voice_channel, query, song_status, song_info
        )
        disco_manager.servers[voice_channel.guild.id]['song_url'] = embed.url

        return embed

    def server_change_volume(self, server: discord.Guild, volume_percentage: Number):
        volume_float = abs(float(volume_percentage)) / 100
        self.servers[server.id]['volume'] = volume_float

        if self.servers[server.id]['song_audio']:
            self.servers[server.id]['song_audio'].volume = volume_float

    @staticmethod
    def _generate_song_embed(
            voice_channel: discord.VoiceChannel, query: str, song_status: int, song_info: dict
    ) -> discord.Embed:
        if song_status == 0:
            embed = discord.Embed(
                title=f':slight_frown: Brak wyników dla zapytania "{query}"',
                color=somsiad.color
            )
        elif song_status == 1:
            embed = discord.Embed(
                title=':slight_frown: Znaleziony utwór przekracza limit rozmiaru wynoszący '
                f'{somsiad.conf["disco_max_file_size_in_mib"]} MiB',
                color=somsiad.color
            )
        else:
            extractor = song_info['extractor']

            if extractor.endswith(':search'):
                song_info = song_info['entries'][0]

            if extractor.startswith('soundcloud'):
                uploader_url = '/'.join(song_info['webpage_url'].split('/')[:-1])
            else:
                try:
                    uploader_url = song_info['uploader_url']
                except KeyError:
                    uploader_url = None

            embed = discord.Embed(
                title=f':arrow_forward: {song_info["title"]}',
                url=song_info['webpage_url'],
                color=somsiad.color
            )
            embed.set_author(name=song_info['uploader'], url=uploader_url)
            embed.set_thumbnail(url=song_info['thumbnail'])
            embed.add_field(name='Długość', value=TextFormatter.human_readable_time(song_info['duration']))
            embed.add_field(
                name='Kanał', value=voice_channel.name
            )

            if extractor.startswith('youtube'):
                embed.set_footer(
                    icon_url=disco_manager.FOOTER_ICON_URL_YOUTUBE, text=disco_manager.FOOTER_TEXT_YOUTUBE
                )
            elif extractor.startswith('soundcloud'):
                embed.set_footer(
                    icon_url=disco_manager.FOOTER_ICON_URL_SOUNDCLOUD, text=disco_manager.FOOTER_TEXT_SOUNDCLOUD
                    )
            elif extractor.startswith('vimeo'):
                embed.set_footer(
                    icon_url=disco_manager.FOOTER_ICON_URL_VIMEO, text=disco_manager.FOOTER_TEXT_VIMEO
                )

        return embed


disco_manager = DiscoManager()


@somsiad.bot.group(aliases=['d'], invoke_without_command=True)
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def disco(ctx):
    command_name = 'disco'
    subcommands = (
        Helper.Command(('zagraj', 'graj'), 'zapytanie/link', 'Odtwarza utwór na kanale głosowym.'),
        Helper.Command(
            ('powtórz', 'powtorz'), None, 'Odtwarza od początku obecnie lub ostatnio odtwarzany na serwerze utwór.'
        ),
        Helper.Command(('spauzuj', 'pauzuj', 'pauza'), None, 'Pauzuje obecnie odtwarzany utwór.'),
        Helper.Command(('wznów', 'wznow'), None, 'Wznawia odtwarzanie utworu.'),
        Helper.Command(('pomiń', 'pomin'), None, 'Pomija obecnie odtwarzany utwór.'),
        Helper.Command(
            ('głośność', 'glosnosc', 'volume', 'vol'), '?nowa głośność w procentach',
            'Sprawdza głośność odtwarzania lub, jeśli podano <?nową głośność>, ustawia ją.'
        ),
        Helper.Command(('rozłącz', 'rozlacz', 'stop'), None, 'Rozłącza z kanału głosowego.'),
    )
    embed = Helper.generate_subcommands_embed(command_name, subcommands)
    await ctx.send(ctx.author.mention, embed=embed)


@disco.command(aliases=['play', 'zagraj', 'graj', 'puść', 'pusc', 'odtwórz', 'odtworz'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.default
)
@discord.ext.commands.guild_only()
async def disco_play(ctx, *, query):
    """Starts playing music on the voice channel where the invoking user currently resides."""
    disco_manager.ensure_server_registration(ctx.guild)

    if ctx.author.voice is None:
        embed = discord.Embed(
            title=':warning: Nie odtworzono utworu, bo nie jesteś połączony z żadnym kanałem głosowym!',
            color=somsiad.color
        )
    else:
        async with ctx.typing():
            embed = await disco_manager.channel_play_song(
                ctx.author.voice.channel, query
            )

    await ctx.send(ctx.author.mention, embed=embed)


@disco_play.error
async def disco_play_error(ctx, error):
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        embed = discord.Embed(
            title=f':warning: Nie podano zapytania ani linku!',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)


@disco.command(aliases=['powtórz', 'powtorz', 'znów', 'znow', 'znowu', 'again', 'repeat'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.default
)
@discord.ext.commands.guild_only()
async def disco_again(ctx):
    """Starts playing music on the voice channel where the invoking user currently resides."""
    disco_manager.ensure_server_registration(ctx.guild)

    if ctx.author.voice is None:
        embed = discord.Embed(
            title=':warning: Nie powtórzono utworu, bo nie jesteś połączony z żadnym kanałem głosowym!',
            color=somsiad.color
        )
    elif disco_manager.servers[ctx.guild.id]['song_url'] is None:
        embed = discord.Embed(
            title=':red_circle: Nie powtórzono utworu, bo nie ma żadnego do powtórzenia',
            color=somsiad.color
        )
    else:
        async with ctx.typing():
            embed = await disco_manager.channel_play_song(
                ctx.author.voice.channel, disco_manager.servers[ctx.guild.id]['song_url']
            )

    await ctx.send(ctx.author.mention, embed=embed)


@disco.command(aliases=['pauza', 'spauzuj', 'pauzuj', 'pause'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.default
)
@discord.ext.commands.guild_only()
async def disco_pause(ctx):
    """Pauses the currently played song."""
    if ctx.voice_client is None:
        embed = discord.Embed(
            title=':red_circle: Nie spauzowano utworu, bo bot nie jest połączony z żadnym kanałem głosowym',
            color=somsiad.color
        )
    elif ctx.author.voice is None or ctx.author.voice.channel != ctx.me.voice.channel:
        embed = discord.Embed(
            title=':warning: Odtwarzanie można kontrolować tylko będąc na tym samym kanale co bot!',
            color=somsiad.color
        )
    elif ctx.voice_client.is_paused():
        embed = discord.Embed(
            title=':red_circle: Nie spauzowano utworu, bo już jest spauzowany',
            color=somsiad.color
        )
    elif not ctx.voice_client.is_playing():
        embed = discord.Embed(
            title=':red_circle: Nie spauzowano utworu, bo żaden nie jest odtwarzany',
            color=somsiad.color
        )
    else:
        ctx.voice_client.pause()
        embed = discord.Embed(
            title=f':pause_button: Spauzowano utwór',
            color=somsiad.color
        )
    await ctx.send(ctx.author.mention, embed=embed)


@disco.command(aliases=['wznów', 'wznow', 'odpauzuj', 'unpause', 'resume'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.default
)
@discord.ext.commands.guild_only()
async def disco_resume(ctx):
    """Resumes playing song."""
    if ctx.voice_client is None:
        embed = discord.Embed(
            title=':red_circle: Nie wznowiono odtwarzania utworu, bo bot nie jest połączony z żadnym kanałem głosowym',
            color=somsiad.color
        )
    elif ctx.author.voice is None or ctx.author.voice.channel != ctx.me.voice.channel:
        embed = discord.Embed(
            title=':warning: Odtwarzanie można kontrolować tylko będąc na tym samym kanale co bot!',
            color=somsiad.color
        )
    elif ctx.voice_client.is_playing():
        embed = discord.Embed(
            title=':red_circle: Nie wznowiono odtwarzania utworu, bo już jest odtwarzany',
            color=somsiad.color
        )
    elif not ctx.voice_client.is_paused():
        embed = discord.Embed(
            title=':red_circle: Nie wznowiono odtwarzania utworu, bo żaden nie jest spauzowany',
            color=somsiad.color
        )
    else:
        ctx.voice_client.resume()
        embed = discord.Embed(
            title=f':arrow_forward: Wznowiono odtwarzanie utworu',
            color=somsiad.color
        )
    await ctx.send(ctx.author.mention, embed=embed)


@disco.command(aliases=['pomiń', 'pomin', 'skip'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.default
)
@discord.ext.commands.guild_only()
async def disco_skip(ctx):
    """Skips the currently played song."""
    if ctx.voice_client is None:
        embed = discord.Embed(
            title=':red_circle: Nie pominięto utworu, bo bot nie jest połączony z żadnym kanałem głosowym',
            color=somsiad.color
        )
    elif not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        embed = discord.Embed(
            title=':red_circle: Nie pominięto utworu, bo żaden nie jest odtwarzany',
            color=somsiad.color
        )
    else:
        ctx.voice_client.stop()
        embed = discord.Embed(
            title=f':fast_forward: Pominięto utwór',
            color=somsiad.color
        )
    await ctx.send(ctx.author.mention, embed=embed)


@disco.command(aliases=['rozłącz', 'rozlacz', 'stop'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.default
)
@discord.ext.commands.guild_only()
async def disco_disconnect(ctx):
    """Disconnects from the server."""
    if ctx.voice_client is None:
        embed = discord.Embed(
            title=':warning: Nie rozłączono z kanałem głosowym, bo bot nie jest połączony z żadnym!',
            color=somsiad.color
        )
    elif ctx.author.voice is None or ctx.author.voice.channel != ctx.me.voice.channel:
        embed = discord.Embed(
            title=':warning: Odtwarzanie można kontrolować tylko będąc na tym samym kanale co bot!',
            color=somsiad.color
        )
    else:
        voice_channel = await disco_manager.server_disconnect(ctx.guild)
        embed = discord.Embed(
            title=f':stop_button: Rozłączono z kanałem {voice_channel}',
            color=somsiad.color
        )
    await ctx.send(ctx.author.mention, embed=embed)


@disco.command(aliases=['głośność', 'glosnosc', 'poziom', 'volume', 'vol'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.default
)
@discord.ext.commands.guild_only()
async def disco_volume(ctx, volume_percentage: Union[int, locale.atoi] = None):
    """Sets the volume."""
    disco_manager.ensure_server_registration(ctx.guild)

    if volume_percentage is None:
        embed = discord.Embed(
            title=':level_slider: Głośność ustawiona jest na '
            f'{int(disco_manager.servers[ctx.guild.id]["volume"] * 100)}%',
            color=somsiad.color
        )
    else:
        if (
                ctx.voice_client is not None
                and (ctx.author.voice is None or ctx.author.voice.channel != ctx.me.voice.channel)
        ):
            embed = discord.Embed(
                title=':warning: Odtwarzanie można kontrolować tylko będąc na tym samym kanale co bot!',
                color=somsiad.color
            )
        else:
            disco_manager.server_change_volume(ctx.guild, volume_percentage)
            embed = discord.Embed(
                title=':level_slider: Ustawiono głośność na '
                f'{int(disco_manager.servers[ctx.guild.id]["volume"] * 100)}%',
                color=somsiad.color
            )
    await ctx.send(ctx.author.mention, embed=embed)


@disco_volume.error
async def disco_volume_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadUnionArgument):
        embed = discord.Embed(
            title=f':warning: Podana wartość nie jest liczbą całkowitą!',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)
