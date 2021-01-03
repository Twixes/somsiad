# Copyright 2018-2020 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import asyncio
import datetime as dt
import itertools
import os
import platform
import sys
import traceback
from collections import defaultdict
from typing import (
    DefaultDict,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)

import aiohttp
import discord
import psutil
import sentry_sdk
from aiochclient.client import ChClient
from discord.ext import commands
from multidict import CIMultiDict
from sqlalchemy.engine.url import make_url

import data
from configuration import configuration
from utilities import GoogleClient, YouTubeClient, localize, utc_to_naive_local, word_number_form
from version import __copyright__, __version__


class Cog(commands.Cog):
    def __init__(self, bot: "Somsiad"):
        self.bot = bot


class Somsiad(commands.AutoShardedBot):
    COLOR = 0x7289DA
    USER_AGENT = f'SomsiadBot/{__version__}'
    HEADERS = CIMultiDict([('User-Agent', USER_AGENT)])
    WEBSITE_URL = 'https://somsiad.net'
    EMOJIS = [
        '🐜',
        '🅱️',
        '🔥',
        '🐸',
        '🤔',
        '💥',
        '👌',
        '💩',
        '🐇',
        '🐰',
        '🦅',
        '🙃',
        '😎',
        '😩',
        '👹',
        '🤖',
        '✌️',
        '💭',
        '🙌',
        '👋',
        '💪',
        '👀',
        '👷',
        '🕵️',
        '💃',
        '🎩',
        '🤠',
        '🐕',
        '🐈',
        '🐹',
        '🐨',
        '🐽',
        '🐙',
        '🐧',
        '🐔',
        '🐎',
        '🦄',
        '🐝',
        '🐢',
        '🐬',
        '🐋',
        '🐐',
        '🌵',
        '🌻',
        '🌞',
        '☄️',
        '⚡',
        '🦆',
        '🦉',
        '🦊',
        '🍎',
        '🍉',
        '🍇',
        '🍑',
        '🍍',
        '🍆',
        '🍞',
        '🧀',
        '🍟',
        '🎂',
        '🍬',
        '🍭',
        '🍪',
        '🥑',
        '🥔',
        '🎨',
        '🎷',
        '🎺',
        '👾',
        '🎯',
        '🥁',
        '🚀',
        '🛰️',
        '⚓',
        '🏖️',
        '✨',
        '🌈',
        '💡',
        '💈',
        '🔭',
        '🎈',
        '🎉',
        '💯',
        '💝',
        '☢️',
        '🆘',
        '♨️',
    ]
    IGNORED_ERRORS = (
        commands.CommandNotFound,
        commands.MissingRequiredArgument,
        commands.BadArgument,
        commands.BadUnionArgument,
        commands.CommandOnCooldown,
        commands.NotOwner,
    )
    PREFIX_SAFE_COMMANDS = ('prefix', 'ping', 'info', 'help')

    bot_dir_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    storage_dir_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'somsiad')
    cache_dir_path = os.path.join(os.path.expanduser('~'), '.cache', 'somsiad')

    prefix_safe_aliases: Tuple[str]
    prefixes: Dict[int, Sequence[str]]
    diagnostics_on: bool
    commands_being_processed: DefaultDict[str, int]
    ready_datetime: Optional[dt.datetime]
    session: Optional[aiohttp.ClientSession]
    ch_client: Optional[ChClient]
    google_client: GoogleClient
    youtube_client: YouTubeClient
    system_channel: Optional[discord.TextChannel]

    def __init__(self):
        super().__init__(
            command_prefix=self._get_prefix,
            help_command=None,
            description='Zawsze pomocny Somsiad',
            case_insensitive=True,
            intents=discord.Intents.all(),
        )
        if not os.path.exists(self.storage_dir_path):
            os.makedirs(self.storage_dir_path)
        if not os.path.exists(self.cache_dir_path):
            os.makedirs(self.cache_dir_path)
        self.prefix_safe_aliases = ()
        self.prefixes = {}
        self.diagnostics_on = False
        self.commands_being_processed = defaultdict(int)
        self.ready_datetime = None
        self.session = None
        self.ch_client = None
        self.google_client = GoogleClient(
            configuration['google_key'], configuration['google_custom_search_engine_id'], self.loop
        )
        self.youtube_client = YouTubeClient(configuration['google_key'], self.loop)

    async def on_ready(self):
        psutil.cpu_percent()
        localize()
        self.ready_datetime = dt.datetime.now()
        self.session = aiohttp.ClientSession(loop=self.loop, headers=self.HEADERS)
        self.ch_client = ChClient(
            self.session,
            url=configuration["clickhouse_url"],
            user=configuration["clickhouse_user"],
            password=configuration["clickhouse_password"],
            database="somsiad",
        )
        assert await self.ch_client.is_alive()
        print('Przygotowywanie danych serwerów...')
        data.Server.register_all(self.guilds)
        with data.session(commit=True) as session:
            for server in session.query(data.Server):
                self.prefixes[server.id] = tuple(server.command_prefix.split('|')) if server.command_prefix else ()
                if server.joined_at is None:
                    discord_server = self.get_guild(server.id)
                    if discord_server is not None and discord_server.me is not None:
                        server.joined_at = utc_to_naive_local(discord_server.me.joined_at)
        self.system_channel = cast(Optional[discord.TextChannel], await self.fetch_channel(517422572615499777))  # magic
        self.loop.create_task(self.cycle_presence())
        await self.system_notify('✅', 'Włączyłem się')
        self.print_info()

    async def on_error(self, event_method, *args, **kwargs):
        self.register_error(event_method, cast(Exception, sys.exc_info()[1]))

    async def on_command(self, ctx):
        self.commands_being_processed[ctx.command.qualified_name] += 1

    async def on_command_completion(self, ctx):
        self.commands_being_processed[ctx.command.qualified_name] -= 1

    async def on_command_error(self, ctx, error):
        if ctx.command is not None:
            self.commands_being_processed[ctx.command.qualified_name] -= 1
        notice = None
        description = ''
        if isinstance(error, commands.NoPrivateMessage):
            notice = 'Ta komenda nie może być użyta w prywatnych wiadomościach'
        elif isinstance(error, commands.DisabledCommand):
            notice = 'Ta komenda jest wyłączona'
        elif isinstance(error, commands.MissingPermissions):
            notice = 'Nie masz wymaganych do tego uprawnień'
        elif isinstance(error, commands.BotMissingPermissions):
            notice = 'Bot nie ma wymaganych do tego uprawnień'
        elif not isinstance(error, self.IGNORED_ERRORS):
            notice = 'Wystąpił nieznany błąd'
            if configuration['sentry_dsn']:
                description = 'Okoliczności zajścia zostały zarejestrowane do analizy.'
            self.register_error('on_command', error, ctx)
        if notice is not None:
            await self.send(ctx, embed=self.generate_embed('⚠️', notice, description))

    async def on_guild_join(self, server):
        data.Server.register(server)

    def load_and_run(self, cogs: Optional[Sequence[Type[Cog]]] = None):
        print('Ładowanie rozszerzeń...')
        if cogs:
            for cog in cogs:
                self.add_cog(cog(self))
        for path in os.scandir('plugins'):
            if path.is_file() and path.name.endswith('.py'):
                self.load_extension(f'plugins.{path.name[:-3]}')
        self.prefix_safe_aliases = tuple(
            (
                variant
                for command in self.PREFIX_SAFE_COMMANDS
                for alias in [self.get_command(command).name] + self.get_command(command).aliases
                for variant in (
                    configuration['command_prefix'] + ' ' + command,
                    configuration['command_prefix'] + alias,
                )
            )
        )
        data.create_all_tables()
        print('Łączenie z Discordem...')
        self.run(configuration['discord_token'], reconnect=True)

    async def system_notify(
        self,
        emoji: Optional[str] = None,
        notice: Optional[str] = None,
        description: Union[str, discord.embeds._EmptyEmbed] = discord.Embed.Empty,
    ) -> bool:
        if self.system_channel is not None:
            await self.system_channel.send(
                content='<@171599592708767744>',
                embed=self.generate_embed(emoji, notice, description, timestamp=dt.datetime.utcnow()),
            )
            return True
        else:
            return False

    async def close(self):
        print('\nZatrzymywanie działania programu...')
        await self.system_notify('🛑', 'Wyłączam się…')
        if self.session is not None:
            await self.session.close()
        await super().close()
        sys.exit(0)

    def signal_handler(self, *args, **kwargs):
        asyncio.run(self.close())

    def invite_url(self) -> str:
        """Return the invitation URL of the bot."""
        return discord.utils.oauth_url(str(self.user.id), discord.Permissions(305392727))

    @property
    def server_count(self) -> int:
        return len([server.id for server in self.guilds if not server.name or 'bot' not in server.name.lower()])

    @property
    def user_count(self) -> int:
        return len(
            {
                member.id
                for server in self.guilds
                for member in server.members
                if not server.name or 'bot' not in server.name.lower()
            }
        )

    def print_info(self) -> str:
        """Return a block of bot information."""
        info_lines = [
            f'\nPołączono jako {self.user} (ID {self.user.id}). '
            f'{word_number_form(self.user_count, "użytkownik", "użytkownicy", "użytkowników")} '
            f'na {word_number_form(self.server_count, "serwerze", "serwerach")} '
            f'z {word_number_form(self.shard_count or 1, "sharda", "shardów")}.',
            '',
            self.invite_url(),
            '',
            *map(str, configuration.settings.values()),
            '',
            f'Somsiad {__version__} • discord.py {discord.__version__} • Python {platform.python_version()}',
            '',
            __copyright__,
        ]
        info = '\n'.join(info_lines)
        print(info)
        return info

    async def cycle_presence(self):
        """Cycle through prefix safe commands in the presence."""
        prefix_safe_command_names = ('prefiks', 'info', 'ping', 'pomocy')
        for command in itertools.cycle(prefix_safe_command_names):
            try:
                await self.change_presence(
                    activity=discord.Game(name=f'Kiedyś to było | {configuration["command_prefix"]}{command}')
                )
            except:
                pass
            await asyncio.sleep(60)

    def generate_embed(
        self,
        emoji: Optional[str] = None,
        notice: Optional[str] = None,
        description: Optional[Union[str, discord.embeds._EmptyEmbed]] = discord.Embed.Empty,
        *,
        url: Union[str, discord.embeds._EmptyEmbed] = discord.Embed.Empty,
        color: Optional[Union[discord.Color, int]] = None,
        timestamp: Union[dt.datetime, discord.embeds._EmptyEmbed] = discord.Embed.Empty,
    ):
        title_parts = tuple(filter(None, (emoji, notice)))
        color = color or self.COLOR
        color_value = color.value if isinstance(color, discord.Color) else color
        color = color if color_value != 0xFFFFFF else 0xFEFEFE  # Discord treats pure white as no color at all
        return discord.Embed(
            title=' '.join(title_parts) if title_parts else discord.Embed.Empty,
            url=url,
            timestamp=timestamp,
            color=color or self.COLOR,
            description=description or discord.Embed.Empty,
        )

    async def send(
        self,
        ctx: commands.Context,
        text: Optional[str] = None,
        *,
        direct: bool = False,
        embed: Optional[Union[discord.Embed, Sequence[discord.Embed]]] = None,
        file: Optional[discord.File] = None,
        files: Optional[List[discord.File]] = None,
        delete_after: Optional[float] = None,
        mention: Optional[Union[bool, Sequence[discord.User]]] = None,
    ) -> Optional[Union[discord.Message, List[discord.Message]]]:
        if embed is None:
            embeds = []
        elif isinstance(embed, discord.Embed):
            embeds = [embed]
        else:
            if len(embed) > 10:
                raise ValueError('no more than 10 embeds can be sent at the same time!')
            embeds = embed
        destination = cast(discord.abc.Messageable, ctx.author if direct else ctx.channel)
        direct = direct or isinstance(destination, discord.abc.PrivateChannel)
        content_elements: List[str] = []
        if text:
            content_elements.append(text)
        if mention is not None and not isinstance(mention, bool):
            content_elements.extend((user.mention for user in mention))
        elif mention or not direct:
            content_elements.append(ctx.author.mention)
        content = ' '.join(content_elements)
        if self.diagnostics_on and ctx.author.id == self.owner_id:
            processing_timedelta = dt.datetime.utcnow() - ctx.message.created_at
            now_also = ', '.join(
                (f'{command} ({number})' for command, number in self.commands_being_processed.items() if number > 0)
            )
            process = psutil.Process()
            virtual_memory = psutil.virtual_memory()
            swap_memory = psutil.swap_memory()
            process_memory = process.memory_full_info()
            try:
                process_swap = process_memory.swap
                swap_usage = f' + {process_swap / 1_048_576:n} MiB '
            except AttributeError:
                process_swap = 0.0
                swap_usage = ' '
            if content is None:
                content = ''
            content += (
                f'```Python\nużycie procesora: ogólnie {psutil.cpu_percent():n}%\n'
                f'użycie pamięci: {(process_memory.uss - process_swap) / 1_048_576:n} MiB{swap_usage}(ogólnie '
                f'{(virtual_memory.total - virtual_memory.available) / 1_048_576:n} MiB + '
                f'{swap_memory.used / 1_048_576:n} MiB) / {virtual_memory.total / 1_048_576:n} MiB + '
                f'{swap_memory.total / 1_048_576:n} MiB\nopóźnienie połączenia (przy uruchomieniu): '
                f'{round(self.latency, 2):n} s\nczas od wywołania komendy: '
                f'{round(processing_timedelta.total_seconds(), 2):n} s\nkomendy w tym momencie: {now_also or "brak"}```'
            )
        if direct and not isinstance(ctx.channel, discord.abc.PrivateChannel):
            try:
                await ctx.message.add_reaction('📫')
            except (discord.Forbidden, discord.NotFound):
                pass
        messages = []
        try:
            messages = [
                await destination.send(
                    content, embed=embeds[0] if embeds else None, file=file, files=files, delete_after=delete_after
                )
            ]
            for extra_embed in embeds[1:]:
                messages.append(await destination.send(embed=extra_embed, delete_after=delete_after))
        except (discord.Forbidden, discord.NotFound):
            if not direct and ctx.guild is not None and 'bot' not in ctx.guild.name.lower():
                try:
                    await ctx.message.add_reaction('⚠️')
                except (discord.Forbidden, discord.NotFound):
                    pass
                error_embed = self.generate_embed(
                    '⚠️',
                    f'Nie mogę wysłać odpowiedzi na komendę {ctx.invoked_with}',
                    f'Brak mi uprawnień na kanale #{ctx.channel} serwera {ctx.guild}.',
                )
                await self.send(ctx, direct=True, embed=error_embed)
            return None
        else:
            return messages[0] if len(messages) == 1 else messages

    def register_error(self, event_method: str, error: Exception, ctx: Optional[commands.Context] = None):
        if configuration['sentry_dsn'] is None:
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        else:
            with sentry_sdk.push_scope() as scope:
                scope.set_tag('event_method', event_method)
                if ctx is not None:
                    scope.user = {
                        'id': ctx.author.id,
                        'username': str(ctx.author),
                        'activities': (
                            ', '.join(filter(None, (activity.name for activity in ctx.author.activities)))
                            if ctx.guild is not None
                            else None
                        ),
                    }
                    scope.set_tag('full_command', ctx.command.qualified_name)
                    scope.set_tag('root_command', str(ctx.command.root_parent or ctx.command.qualified_name))
                    scope.set_context(
                        'message',
                        {
                            'prefix': ctx.prefix,
                            'content': ctx.message.content,
                            'attachments': ', '.join((attachment.url for attachment in ctx.message.attachments)),
                        },
                    )
                    scope.set_context('channel', {'id': ctx.channel.id, 'name': str(ctx.channel)})
                    if ctx.guild is not None:
                        scope.set_context('server', {'id': ctx.guild.id, 'name': str(ctx.guild)})
                sentry_sdk.capture_exception(error)

    def _get_prefix(self, bot: commands.Bot, message: discord.Message) -> List[str]:
        prefixes = [f'<@!{bot.user.id}> ', f'<@{bot.user.id}> ', f'{bot.user} ']
        if message.guild is not None:
            for extra_prefix in self.prefixes.get(message.guild.id) or (configuration['command_prefix'],):
                prefixes.append(extra_prefix + ' ')
                prefixes.append(extra_prefix)
        else:
            prefixes.append(configuration['command_prefix'] + ' ')
            prefixes.append(configuration['command_prefix'])
            prefixes.append('')
        if (
            message.content.lower().startswith(self.prefix_safe_aliases)
            and configuration['command_prefix'] not in prefixes
        ):
            prefixes.append(configuration['command_prefix'] + ' ')
            prefixes.append(configuration['command_prefix'])
        prefixes.sort(key=len, reverse=True)
        return prefixes
