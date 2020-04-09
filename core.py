#!/usr/bin/env python3

# Copyright 2018-2020 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.


from typing import Optional, Union, Sequence, Tuple, List
from collections import defaultdict
import os
import sys
import signal
import psutil
import traceback
import asyncio
import platform
import random
import itertools
import datetime as dt
import aiohttp
import sentry_sdk
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
import discord
from discord.ext import commands
from version import __version__, __copyright__
from utilities import GoogleClient, YouTubeClient, word_number_form, human_amount_of_time, setlocale, utc_to_naive_local
from configuration import configuration
import data


def cooldown(
        rate: int = 1, per: float = configuration['command_cooldown_per_user_in_seconds'],
        type: commands.BucketType = commands.BucketType.user
):
    def decorator(func):
        if isinstance(func, commands.Command):
            func._buckets = commands.CooldownMapping(commands.Cooldown(rate, per, type))
        else:
            func.__commands_cooldown__ = commands.Cooldown(rate, per, type)
        return func
    return decorator


class Somsiad(commands.Bot):
    COLOR = 0x7289da
    USER_AGENT = f'SomsiadBot/{__version__}'
    HEADERS = {'User-Agent': USER_AGENT}
    WEBSITE_URL = 'https://somsiad.net'
    EMOJIS = [
        '🐜', '🅱️', '🔥', '🐸', '🤔', '💥', '👌', '💩', '🐇', '🐰', '🦅', '🙃', '😎', '😩', '👹', '🤖', '✌️', '💭',
        '🙌', '👋', '💪', '👀', '👷', '🕵️', '💃', '🎩', '🤠', '🐕', '🐈', '🐹', '🐨', '🐽', '🐙', '🐧', '🐔', '🐎',
        '🦄', '🐝', '🐢', '🐬', '🐋', '🐐', '🌵', '🌻', '🌞', '☄️', '⚡', '🦆', '🦉', '🦊', '🍎', '🍉', '🍇', '🍑',
        '🍍', '🍆', '🍞', '🧀', '🍟', '🎂', '🍬', '🍭', '🍪', '🥑', '🥔', '🎨', '🎷', '🎺', '👾', '🎯', '🥁', '🚀',
        '🛰️', '⚓', '🏖️', '✨', '🌈', '💡', '💈', '🔭', '🎈', '🎉', '💯', '💝', '☢️', '🆘', '♨️'
    ]
    IGNORED_ERRORS = (
        commands.CommandNotFound,
        commands.MissingRequiredArgument,
        commands.BadArgument,
        commands.BadUnionArgument,
        commands.CommandOnCooldown,
        commands.NotOwner
    )
    PREFIX_SAFE_COMMANDS = ('prefix', 'ping', 'info', 'help')
    bot_dir_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    storage_dir_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'somsiad')
    cache_dir_path = os.path.join(os.path.expanduser('~'), '.cache', 'somsiad')

    def __init__(self):
        super().__init__(
            command_prefix=self._get_prefix, help_command=None, description='Zawsze pomocny Somsiad',
            case_insensitive=True
        )
        if not os.path.exists(self.storage_dir_path):
            os.makedirs(self.storage_dir_path)
        if not os.path.exists(self.cache_dir_path):
            os.makedirs(self.cache_dir_path)
        self.prefix_safe_aliases = ()
        self.prefixes = {}
        self.diagnostics_on = False
        self.commands_being_processed = defaultdict(int)
        self.run_datetime = None
        self.session = None
        self.google_client = GoogleClient(
            configuration['google_key'], configuration['google_custom_search_engine_id'], self.loop
        )
        self.youtube_client = YouTubeClient(configuration['google_key'], self.loop)

    async def on_ready(self):
        psutil.cpu_percent()
        setlocale()
        self.run_datetime = dt.datetime.now()
        self.session = aiohttp.ClientSession(loop=self.loop, headers=self.HEADERS)
        print('Przygotowywanie danych serwerów...')
        data.Server.register_all(self.guilds)
        with data.session(commit=True) as session:
            for server in session.query(data.Server):
                self.prefixes[server.id] = tuple(server.command_prefix.split('|')) if server.command_prefix else ()
                if server.joined_at is None:
                    discord_server = self.get_guild(server.id)
                    if discord_server is not None and discord_server.me is not None:
                        server.joined_at = utc_to_naive_local(discord_server.me.joined_at)
        self.loop.create_task(self.cycle_presence())
        self.print_info()

    async def on_error(self, event_method, *args, **kwargs):
        self.register_error(event_method, sys.exc_info()[1])

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

    def load_and_run(self):
        print('Ładowanie rozszerzeń...')
        self.add_cog(Essentials(self))
        self.add_cog(Prefix(self))
        for path in os.scandir('plugins'):
            if path.is_file() and path.name.endswith('.py'):
                self.load_extension(f'plugins.{path.name[:-3]}')
        self.prefix_safe_aliases = tuple((
            variant
            for command in self.PREFIX_SAFE_COMMANDS
            for alias in [self.get_command(command).name] + self.get_command(command).aliases
            for variant in (configuration['command_prefix'] + ' ' + command, configuration['command_prefix'] + alias)
        ))
        data.create_all_tables()
        print('Łączenie z Discordem...')
        self.run(configuration['discord_token'], reconnect=True)

    async def close(self):
        print('\nZatrzymywanie działania programu...')
        if self.session is not None:
            await self.session.close()
        await super().close()
        sys.exit(0)

    def signal_handler(self, _, __):
        asyncio.run(self.close())

    def invite_url(self) -> str:
        """Return the invitation URL of the bot."""
        return discord.utils.oauth_url(self.user.id, discord.Permissions(305392727))

    @property
    def server_count(self) -> int:
        return len([server.id for server in self.guilds if not server.name or 'bot' not in server.name.lower()])

    @property
    def user_count(self) -> int:
        return len({
            member.id for server in self.guilds for member in server.members
            if not server.name or 'bot' not in server.name.lower()
        })

    def print_info(self) -> str:
        """Return a block of bot information."""
        info_lines = [
            f'\nPołączono jako {self.user} (ID {self.user.id}). '
            f'{word_number_form(self.user_count, "użytkownik", "użytkownicy", "użytkowników")} '
            f'na {word_number_form(self.server_count, "serwerze", "serwerach")}.',
            '',
            self.invite_url(),
            '',
            *map(str, configuration.settings.values()),
            '',
            f'Somsiad {__version__} • discord.py {discord.__version__} • Python {platform.python_version()}',
            '',
            __copyright__
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
            self, emoji: Optional[str] = None, notice: Optional[str] = None, description: str = discord.Embed.Empty, *,
            url: str = discord.Embed.Empty, color: Optional[Union[discord.Color, int]] = None,
            timestamp: dt.datetime = discord.Embed.Empty
    ):
        title_parts = tuple(filter(None, (emoji, notice)))
        color = color or self.COLOR
        color_value = color.value if isinstance(color, discord.Color) else color
        color = color if color_value != 0xffffff else 0xfefefe # Discord treats pure white as no color at all
        return discord.Embed(
            title=' '.join(title_parts) if title_parts else None, url=url, timestamp=timestamp,
            color=color or self.COLOR, description=description
        )

    async def send(
            self, ctx: commands.Context, text: Optional[str] = None,
            *, direct: bool = False, embed: Optional[discord.Embed] = None,
            embeds: Optional[Sequence[discord.Embed]] = None, file: Optional[discord.File] = None,
            files: Optional[List[discord.File]] = None, delete_after: Optional[float] = None, mention: bool = True
    ) -> Optional[Union[discord.Message, List[discord.Message]]]:
        if embed is not None and embeds:
            raise ValueError('embed and embeds cannot be both passed at the same time')
        embeds = embeds or []
        if embed is not None:
            embeds.append(embed)
        if len(embeds) > 10:
            raise ValueError('no more than 10 embeds can be sent at the same time')
        destination = ctx.author if direct else ctx.channel
        content_elements = tuple(filter(None, (text, ctx.author.mention if not direct or not mention else None)))
        content = ' '.join(content_elements) if content_elements else None
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
            messages = [await destination.send(
                content, embed=embeds[0] if embeds else None, file=file, files=files, delete_after=delete_after
            )]
            for extra_embed in embeds[1:]:
                messages.append(await destination.send(embed=extra_embed, delete_after=delete_after))
        except (discord.Forbidden, discord.NotFound):
            if not direct and ctx.guild is not None and 'bot' not in ctx.guild.name.lower():
                try:
                    await ctx.message.add_reaction('⚠️')
                except (discord.Forbidden, discord.NotFound):
                    pass
                error_embed = self.generate_embed(
                    '⚠️', f'Nie mogę wysłać odpowiedzi na komendę {ctx.invoked_with}',
                    f'Brak mi uprawnień na kanale #{ctx.channel} serwera {ctx.guild}.'
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
                        'id': ctx.author.id, 'username': str(ctx.author),
                        'activities': (
                            ', '.join(filter(None, (activity.name for activity in ctx.author.activities)))
                            if ctx.guild is not None else None
                        )
                    }
                    scope.set_tag('full_command', ctx.command.qualified_name)
                    scope.set_tag('root_command', str(ctx.command.root_parent or ctx.command.qualified_name))
                    scope.set_context('message', {
                        'prefix': ctx.prefix, 'content': ctx.message.content,
                        'attachments': ', '.join((attachment.url for attachment in ctx.message.attachments))
                    })
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
                message.content.lower().startswith(self.prefix_safe_aliases) and
                configuration['command_prefix'] not in prefixes
        ):
            prefixes.append(configuration['command_prefix'] + ' ')
            prefixes.append(configuration['command_prefix'])
        prefixes.sort(key=len, reverse=True)
        return prefixes


class Help:
    """A help message generator."""
    class Command:
        "A command model."
        __slots__ = ('_aliases', '_arguments', '_description')

        def __init__(self, aliases: Union[Tuple[str], str], arguments: Union[Tuple[str], str], description: str):
            self._aliases = aliases if isinstance(aliases, tuple) else (aliases,)
            self._arguments = arguments if isinstance(arguments, tuple) else (arguments,)
            self._description = description

        def __str__(self) -> str:
            return ' '.join(filter(None, (self.name, self.aliases, self.arguments)))

        @property
        def name(self) -> str:
            return self._aliases[0]

        @property
        def aliases(self) -> Optional[str]:
            return f'({", ".join(self._aliases[1:])})' if len(self._aliases) > 1 else None

        @property
        def arguments(self) -> Optional[str]:
            return " ".join(f"<{argument}>" for argument in self._arguments) if self._arguments else None

        @property
        def description(self) -> str:
            return self._description

    __slots__ = ('group', 'embeds')

    def __init__(
            self, commands: Sequence[Command],
            emoji: str, title: Optional[str] = None, description: Optional[str] = None, *,
            group: Optional[Command] = None, footer_text: Optional[str] = None, footer_icon_url: Optional[str] = None
    ):
        self.group = group
        title_parts = [emoji]
        if title is None:
            if group is not None:
                title_parts.append('Grupa')
                title_parts.extend(filter(None, (group.name, group.aliases)))
        else:
            title_parts.append(title)
        if description is None:
            description_parts = []
            if group is not None and group.description:
                description_parts.append(group.description)
            description_parts.append(
                '*Używając komend na serwerach pamiętaj o prefiksie (możesz zawsze sprawdzić go za pomocą '
                f'`{configuration["command_prefix"]}prefiks sprawdź`).\n'
                'W (nawiasach okrągłych) podane są aliasy komend.\n'
                'W <nawiasach ostrokątnych> podane są argumenty komend. Jeśli przed nazwą argumentu jest ?pytajnik, '
                'oznacza to, że jest to argument opcjonalny.*'
            )
            description = '\n\n'.join(description_parts)
        self.embeds = [discord.Embed(title=' '.join(title_parts), description=description, color=Somsiad.COLOR)]
        for command in commands:
            if len(self.embeds[-1].fields) >= 25:
                self.embeds.append(discord.Embed(color=Somsiad.COLOR))
            self.embeds[-1].add_field(
                name=str(command) if self.group is None else f'{self.group.name} {command}',
                value=command.description,
                inline=False
            )
        if footer_text:
            self.embeds[-1].set_footer(text=footer_text, icon_url=footer_icon_url)


class Essentials(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['wersja', 'v'])
    @cooldown()
    async def version(self, ctx, *, x = None):
        """Responds with current version of the bot."""
        if x and 'fccchk' in x.lower():
            emoji = '👺'
            notice = f'??? {random.randint(1, 9)}.{random.randint(1, 9)}.{random.randint(1, 9)}'
            footer = '© ???-??? ???'
        else:
            emoji = random.choice(self.bot.EMOJIS)
            notice = f'Somsiad {__version__}'
            footer = __copyright__
        embed = self.bot.generate_embed(emoji, notice, url=self.bot.WEBSITE_URL)
        embed.set_footer(text=footer)
        await self.bot.send(ctx, embed=embed)

    @commands.command(aliases=['informacje'])
    @cooldown()
    async def info(self, ctx, *, x = None):
        """Responds with current version of the bot."""
        if x and 'fccchk' in x.lower():
            emoji = '👺'
            notice = f'??? {random.randint(1, 9)}.{random.randint(1, 9)}.{random.randint(1, 9)}'
            footer = '© ???-??? ???'
            psi = 2**18
            omega = psi * psi
            server_count = random.randint(0, psi)
            user_count = server_count * random.randint(0, psi)
            runtime = human_amount_of_time(random.randint(0, omega))
            instance_owner = '???'
        else:
            emoji = 'ℹ️'
            notice = f'Somsiad {__version__}'
            footer = __copyright__
            server_count = self.bot.server_count
            user_count = self.bot.user_count
            runtime = human_amount_of_time(dt.datetime.now() - self.bot.run_datetime)
            application_info = await self.bot.application_info()
            instance_owner = application_info.owner.mention
        embed = self.bot.generate_embed(emoji, notice, url=self.bot.WEBSITE_URL)
        embed.add_field(name='Liczba serwerów', value=f'{server_count:n}')
        embed.add_field(name='Liczba użytkowników', value=f'{user_count:n}')
        embed.add_field(name='Czas pracy', value=runtime)
        embed.add_field(name='Właściciel instancji', value=instance_owner)
        embed.set_footer(text=footer)
        await self.bot.send(ctx, embed=embed)

    @commands.command(aliases=['pińg'])
    async def ping(self, ctx):
        """Pong!"""
        await self.bot.send(ctx, embed=self.bot.generate_embed('🏓', 'Pong!'))

    @commands.command(aliases=['nope', 'nie'])
    @cooldown()
    async def no(self, ctx, member: discord.Member = None):
        """Removes the last message sent by the bot in the channel on the requesting user's request."""
        member = member or ctx.author
        if member == ctx.author or ctx.author.permissions_in(ctx.channel).manage_messages:
            async for message in ctx.history(limit=10):
                if message.author == ctx.me and member in message.mentions:
                    await message.delete()
                    break

    @commands.command(aliases=['diag', 'diagnostyka'])
    @commands.is_owner()
    async def diagnostics(self, ctx):
        """Causes an error."""
        if not self.bot.diagnostics_on:
            self.bot.diagnostics_on = True
            embed = self.bot.generate_embed('🚦', 'Diagnostyka włączona')
        else:
            self.bot.diagnostics_on = False
            embed = self.bot.generate_embed('🚥', 'Diagnostyka wyłączona')
        await self.bot.send(ctx, embed=embed)

    @commands.command(aliases=['wyłącz', 'wylacz'])
    @commands.is_owner()
    async def shutdown(self, ctx):
        """Shuts down the bot."""
        embed = self.bot.generate_embed('🛑', 'Wyłączanie bota…')
        await self.bot.send(ctx, embed=embed)
        await ctx.bot.close()

    @commands.command(aliases=['błąd', 'blad', 'błont', 'blont'])
    @commands.is_owner()
    async def error(self, ctx):
        """Causes an error."""
        await self.bot.send(ctx, 1 / 0)


class Prefix(commands.Cog):
    GROUP = Help.Command(
        ('prefiks', 'prefix', 'przedrostek'), (), 'Komendy związane z własnymi serwerowymi prefiksami komend.'
    )
    COMMANDS = (
        Help.Command(('sprawdź', 'sprawdz'), (), 'Pokazuje obowiązujący prefiks bądź obowiązujące prefiksy.'),
        Help.Command(
            ('ustaw'), (), 'Ustawia na serwerze podany prefiks bądź podane prefiksy oddzielone " lub ". '
            'Wymaga uprawnień administratora.'
        ),
        Help.Command(
            ('przywróć', 'przywroc'), (), 'Przywraca na serwerze domyślny prefiks. Wymaga uprawnień administratora.'
        )
    )
    HELP = Help(COMMANDS, '🔧', group=GROUP)

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(
        aliases=['prefixes', 'prefixy', 'prefiks', 'prefiksy', 'przedrostek', 'przedrostki'],
        invoke_without_command=True
    )
    @cooldown()
    async def prefix(self, ctx):
        """Command prefix commands."""
        await self.bot.send(ctx, embeds=self.HELP.embeds)

    @prefix.command(aliases=['sprawdź', 'sprawdz'])
    @cooldown()
    async def check(self, ctx):
        """Presents the current command prefix."""
        if not self.bot.prefixes.get(ctx.guild.id):
            extra_prefixes = (configuration['command_prefix'],)
            extra_prefixes_presentation = f'domyślna `{configuration["command_prefix"]}`'
            notice = 'Obowiązuje domyślny prefiks'
        else:
            extra_prefixes = self.bot.prefixes[ctx.guild.id]
            applies_form = word_number_form(
                len(extra_prefixes), 'Obowiązuje', 'Obowiązują', 'Obowiązuje', include_number=False
            )
            prefix_form = word_number_form(
                len(extra_prefixes), 'własny prefiks serwerowy', 'własne prefiksy serwerowe',
                'własnych prefiksów serwerowych'
            )
            notice = f'{applies_form} {prefix_form}'
            extra_prefixes_presentation = ' lub '.join((f'`{prefix}`' for prefix in reversed(extra_prefixes)))
        embed = self.bot.generate_embed('🔧', notice)
        embed.add_field(
            name='Wartość' if len(extra_prefixes) == 1 else 'Wartości', value=extra_prefixes_presentation, inline=False
        )
        embed.add_field(
            name='Przykłady wywołań',
            value=f'`{random.choice(extra_prefixes)}wersja` lub `{random.choice(extra_prefixes)} oof` '
            f'lub `{ctx.me} urodziny`',
            inline=False
        )
        await self.bot.send(ctx, embed=embed)

    @prefix.command(aliases=['ustaw'])
    @cooldown()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def set(self, ctx, *, new_prefixes_raw: str):
        """Sets a new command prefix."""
        new_prefixes = tuple(sorted(
            filter(None, (prefix.strip() for prefix in new_prefixes_raw.split(' lub '))), key=len, reverse=True
        ))
        if not new_prefixes:
            raise commands.BadArgument('no valid prefixes')
        new_prefixes_processed = '|'.join(new_prefixes)
        if len(new_prefixes_processed) > data.Server.COMMAND_PREFIX_MAX_LENGTH:
            raise commands.BadArgument('too long')
        self.bot.prefixes[ctx.guild.id] = new_prefixes
        with data.session(commit=True) as session:
            data_server = session.query(data.Server).get(ctx.guild.id)
            previous_prefixes = data_server.command_prefix.split('|') if data_server.command_prefix else ()
            data_server.command_prefix = new_prefixes_processed
        if previous_prefixes:
            previous_prefixes_presentation = ' lub '.join((f'`{prefix}`' for prefix in reversed(previous_prefixes)))
        else:
            previous_prefixes_presentation = f'domyślna `{configuration["command_prefix"]}`'
        if set(previous_prefixes) == set(new_prefixes):
            embed = self.bot.generate_embed(
                'ℹ️', f'Nie wprowadzono zmian w {"prefiksie" if len(previous_prefixes) == 1 else "prefiksach"}'
            )
            embed.add_field(
                name='Wartości' if len(previous_prefixes) > 1 else 'Wartość',
                value=' lub '.join((f'`{prefix}`' for prefix in reversed(previous_prefixes))), inline=False
            )
        else:
            embed = self.bot.generate_embed('✅', f'Ustawiono {"prefiks" if len(new_prefixes) == 1 else "prefiksy"}')
            embed.add_field(
                name='Nowe wartości' if len(new_prefixes) > 1 else 'Nowa wartość',
                value=' lub '.join((f'`{prefix}`' for prefix in reversed(new_prefixes))), inline=False
            )
            embed.add_field(
                name='Poprzednie wartości' if len(previous_prefixes) > 1 else 'Poprzednia wartość',
                value=previous_prefixes_presentation, inline=False
            )
        embed.add_field(
            name='Przykłady wywołań',
            value=f'`{random.choice(new_prefixes)}wersja` lub `{random.choice(new_prefixes)} oof` '
            f'lub `{ctx.me} urodziny`',
            inline=False
        )
        await self.bot.send(ctx, embed=embed)

    @set.error
    async def set_error(self, ctx, error):
        """Handles new command prefix setting errors."""
        notice = None
        if isinstance(error, commands.MissingRequiredArgument):
            notice = 'Nie podano prefiksu bądź prefiksów oddzielonych " lub "'
        elif isinstance(error, commands.BadArgument):
            if str(error) == 'no valid prefixes':
                notice = 'Nie podano prefiksu bądź prefiksów oddzielonych " lub "'
            elif str(error) == 'too long':
                notice = 'Przekroczono maksymalną długość'
        if notice is not None:
            await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', notice))

    @prefix.command(aliases=['przywróć', 'przywroc'])
    @cooldown()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def restore(self, ctx):
        """Reverts to the default command prefix."""
        self.bot.prefixes[ctx.guild.id] = ()
        with data.session(commit=True) as session:
            data_server = session.query(data.Server).get(ctx.guild.id)
            previous_prefixes = data_server.command_prefix.split('|') if data_server.command_prefix else ()
            data_server.command_prefix = None
        if not previous_prefixes:
            embed = self.bot.generate_embed('ℹ️', 'Już ustawiony jest prefiks domyślny')
            embed.add_field(name='Wartość', value=f'domyślna `{configuration["command_prefix"]}`')
        else:
            embed = self.bot.generate_embed('✅', 'Przywrócono domyślny prefiks')
            embed.add_field(name='Nowa wartość', value=f'domyślna `{configuration["command_prefix"]}`')
            embed.add_field(
                name='Poprzednia wartość' if len(previous_prefixes) == 1 else 'Poprzednie wartości',
                value=' lub '.join((f'`{prefix}`' for prefix in reversed(previous_prefixes))), inline=False
            )
        embed.add_field(
            name='Przykłady wywołań',
            value=f'`{configuration["command_prefix"]}wersja` lub `{configuration["command_prefix"]} oof` '
            f'lub `{ctx.me} urodziny`',
            inline=False
        )
        await self.bot.send(ctx, embed=embed)


somsiad = Somsiad()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, somsiad.signal_handler)
    if configuration['sentry_dsn']:
        print('Inicjowanie połączenia z Sentry...')
        sentry_sdk.init(
            configuration['sentry_dsn'], release=f'{configuration["sentry_proj"] or "somsiad"}@{__version__}',
            integrations=[SqlalchemyIntegration(), AioHttpIntegration()]
        )
    somsiad.load_and_run()
