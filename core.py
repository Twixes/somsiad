# Copyright 2018-2020 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Optional, Union, Sequence, Tuple, List
import os
import sys
import traceback
import asyncio
import platform
import random
import itertools
import datetime as dt
import sentry_sdk
import discord
from discord.ext import commands
from version import __version__, __copyright__
from utilities import word_number_form, human_amount_of_time
from configuration import configuration
import data


class Somsiad(commands.Bot):
    COLOR = 0x7289da
    USER_AGENT = f'SomsiadBot/{__version__}'
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
        commands.CommandOnCooldown
    )
    MESSAGE_AUTODESTRUCTION_TIME_IN_SECONDS = 5
    MESSAGE_AUTODESTRUCTION_NOTICE = (
        'Ta wiadomość ulegnie autodestrukcji w ciągu '
        f'{word_number_form(MESSAGE_AUTODESTRUCTION_TIME_IN_SECONDS, "sekundy", "sekund")} od wysłania.'
    )

    bot_dir_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    storage_dir_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'somsiad')
    cache_dir_path = os.path.join(os.path.expanduser('~'), '.cache', 'somsiad')

    def __init__(self):
        super().__init__(
            command_prefix=self._get_prefix, help_command=None, description='Zawsze pomocny Somsiad',
            case_insensitive=True
        )
        self.run_datetime = None
        if not os.path.exists(self.storage_dir_path):
            os.makedirs(self.storage_dir_path)
        if not os.path.exists(self.cache_dir_path):
            os.makedirs(self.cache_dir_path)
        self.prefix_safe_commands = tuple((
            variant
            for command in
            ('help', 'pomocy', 'pomoc', 'prefix', 'prefiks', 'przedrostek', 'info', 'informacje', 'ping')
            for variant in
            (f'{configuration["command_prefix"]} {command}', f'{configuration["command_prefix"]}{command}')
        ))

    async def on_ready(self):
        print(self.info())
        data.Server.register_all(self.guilds)
        await self.cycle_presence()

    async def on_error(self, event_method, *args, **kwargs):
        self.register_error(event_method, sys.exc_info()[1])

    async def on_command_error(self, ctx, error):
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
            if configuration['sentry_dsn'] is not None:
                description = 'Okoliczności zajścia zostały zarejestrowane do analizy.'
            self.register_error('on_command', error, ctx)
        if notice is not None:
            await self.send(ctx, embed=self.generate_embed('⚠️', notice, description))

    async def on_guild_join(self, server):
        data.Server.register(server)

    def controlled_run(self):
        self.run_datetime = dt.datetime.now()
        self.run(configuration['discord_token'], reconnect=True)

    def invite_url(self) -> str:
        """Return the invitation URL of the bot."""
        return discord.utils.oauth_url(self.user.id, discord.Permissions(305392727))

    def info(self) -> str:
        """Return a block of bot information."""
        number_of_users = len(set(self.get_all_members()))
        number_of_servers = len(self.guilds)
        info_lines = [
            f'Obudzono Somsiada (ID {self.user.id}).',
            '',
            f'Połączono '
            f'{word_number_form(number_of_users, "użytkownikiem", "użytkownikami", include_with=True)} '
            f'na {word_number_form(number_of_servers, "serwerze", "serwerach")}.',
            '',
            'Link do zaproszenia bota:',
            self.invite_url(),
            '',
            *map(str, configuration.settings.values()),
            '',
            f'Somsiad {__version__} • discord.py {discord.__version__} • Python {platform.python_version()}',
            '',
            __copyright__
        ]
        return '\n'.join(info_lines)

    async def cycle_presence(self):
        """Cycle through prefix safe commands in the presence."""
        prefix_safe_commands = ('pomocy', 'prefiks', 'info', 'ping')
        for command in itertools.cycle(prefix_safe_commands):
            await self.change_presence(
                activity=discord.Game(name=f'Kiedyś to było | {configuration["command_prefix"]}{command}')
            )
            await asyncio.sleep(15)

    def generate_embed(
            self, emoji: str, notice: str, description: str = discord.Embed.Empty,
            url: str = discord.Embed.Empty, timestamp: dt.datetime = discord.Embed.Empty
    ):
        return discord.Embed(
            title=f'{emoji} {notice}',
            url=url,
            timestamp=timestamp,
            description=description,
            color=self.COLOR
        )

    async def send(
            self, ctx: commands.Context, text: Optional[str] = None,
            *, direct: bool = False, embed: Optional[discord.Embed] = None,
            embeds: Optional[Sequence[discord.Embed]] = None, file: Optional[discord.File] = None,
            files: Optional[List[discord.File]] = None, delete_after: Optional[float] = None
    ):
        if embed is not None and embeds:
            raise ValueError('embed and embeds cannot be both passed at the same time')
        embeds = embeds or []
        if embed is not None:
            embeds.append(embed)
        if len(embeds) > 10:
            raise ValueError('no more than 10 embeds can be sent at the same time')
        destination = ctx.author if direct else ctx.channel
        content_elements = tuple(filter(None, (ctx.author.mention if not direct else None, text)))
        content = '\n'.join(content_elements) if content_elements else None
        if direct and not isinstance(ctx.channel, discord.abc.PrivateChannel):
            await ctx.message.add_reaction('📫')
        await destination.send(
            content, embed=embeds[0] if embeds else None, file=file, files=files, delete_after=delete_after
        )
        for extra_embed in embeds[1:]:
            await destination.send(embed=extra_embed, delete_after=delete_after)

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
                            ', '.join((activity.name for activity in ctx.author.activities))
                            if ctx.guild is not None else None
                        )
                    }
                    scope.set_tag('command', ctx.command.qualified_name)
                    scope.set_tag('root_command', ctx.command.root_parent or ctx.command.qualified_name)
                    scope.set_context('message', {
                        'prefix': ctx.prefix, 'content': ctx.message.content,
                        'attachments': ', '.join((attachment.url for attachment in ctx.message.attachments))
                    })
                    scope.set_context('channel', {'id': ctx.channel.id, 'name': str(ctx.channel)})
                    if ctx.guild is not None:
                        scope.set_context('server', {'id': ctx.guild.id, 'name': str(ctx.guild)})
                sentry_sdk.capture_exception(error)

    def _get_prefix(self, bot: commands.Bot, message: discord.Message) -> List[str]:
        user_id = bot.user.id
        prefixes = [f'<@!{user_id}> ', f'<@{user_id}> ']
        if message.guild is not None:
            with data.session() as session:
                data_server = session.query(data.Server).get(message.guild.id)
        else:
            data_server = None
        does_server_have_custom_command_prefix = data_server is not None and data_server.command_prefix is not None
        is_message_a_prefix_safe_command = message.content.startswith(self.prefix_safe_commands)
        if does_server_have_custom_command_prefix:
            prefixes.append(data_server.command_prefix + ' ')
            prefixes.append(data_server.command_prefix)
        if not does_server_have_custom_command_prefix or is_message_a_prefix_safe_command:
            prefixes.append(configuration['command_prefix'] + ' ')
            prefixes.append(configuration['command_prefix'])
        if data_server is None:
            prefixes.append('')
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
            self, commands: Sequence[Command], *,
            title: Optional[str] = None, description: Optional[str] = None, group: Optional[Command] = None
    ):
        self.group = group
        if group is not None and title is None:
            title = f'Dostępne podkomendy {" ".join(filter(None, (group.name, group.aliases)))}'
        if description is None:
            description = (
                '*Używając ich na serwerach pamiętaj o prefiksie (możesz zawsze sprawdzić go za pomocą '
                f'`{configuration["command_prefix"]}prefiks sprawdź`).\n'
                'W (nawiasach okrągłych) podane są aliasy komend.\n'
                'W <nawiasach ostrokątnych> podane są argumenty komend. Jeśli przed nazwą argumentu jest ?pytajnik, '
                'oznacza to, że jest to argument opcjonalny.*'
            )
        self.embeds = [discord.Embed(title=title, description=description, color=Somsiad.COLOR)]
        for command in commands:
            self.append(command)

    def append(self, command: Command):
        if len(self.embeds[-1].fields) >= 25:
            self.embeds.append(discord.Embed(color=Somsiad.COLOR))
        self.embeds[-1].add_field(
            name=str(command) if self.group is None else f'{self.group.name} {command}',
            value=command.description,
            inline=False
        )


class ServerRelated:
    @data.declared_attr
    def server_id(cls):
        return data.Column(data.BigInteger, data.ForeignKey(data.Server.id), index=True)

    @data.declared_attr
    def server(self):
        return data.relationship(data.Server)

    @property
    def discord_server(self):
        return somsiad.get_guild(self.server_id) if self.server_id is not None else None


class ServerSpecific(ServerRelated):
    @data.declared_attr
    def server_id(cls):
        return data.Column(data.BigInteger, data.ForeignKey(data.Server.id), primary_key=True)

    @property
    def discord_server(self):
        return somsiad.get_guild(self.server_id)


class ChannelRelated:
    channel_id = data.Column(data.BigInteger, index=True)

    @property
    def discord_channel(self):
        return somsiad.get_channel(self.channel_id) if self.channel_id is not None else None


class ChannelSpecific(ChannelRelated):
    channel_id = data.Column(data.BigInteger, primary_key=True)

    @property
    def discord_channel(self):
        return somsiad.get_channel(self.channel_id)


class UserRelated:
    user_id = data.Column(data.BigInteger, index=True)

    @property
    def discord_user(self) -> Optional[discord.Guild]:
        return somsiad.get_user(self.user_id) if self.user_id is not None else None


class UserSpecific(UserRelated):
    user_id = data.Column(data.BigInteger, primary_key=True)

    @property
    def discord_user(self) -> Optional[discord.Guild]:
        return somsiad.get_user(self.user_id)


class MemberSpecific(ServerSpecific, UserSpecific):
    @property
    def discord_member(self) -> Optional[discord.Member]:
        server = self.discord_server
        return server.get_member(self.user_id) if server is not None else None


class Essentials(discord.ext.commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['wersja', 'v'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
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
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
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
            server_count = len([server.id for server in self.bot.guilds if 'bot' not in server.name.lower()])
            user_count = len({
                member.id for server in self.bot.guilds for member in server.members if 'bot' not in server.name.lower()
            })
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

    @commands.command()
    async def ping(self, ctx):
        """Pong!"""
        await self.bot.send(ctx, embed=self.bot.generate_embed('🏓', 'Pong!'))

    @commands.command(aliases=['nope', 'nie'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def no(self, ctx, member: discord.Member = None):
        """Removes the last message sent by the bot in the channel on the requesting user's request."""
        member = member or ctx.author
        if member == ctx.author or ctx.author.permissions_in(ctx.channel).manage_messages:
            async for message in ctx.history(limit=10):
                if message.author == ctx.me and member in message.mentions:
                    await message.delete()
                    break


class Prefix(discord.ext.commands.Cog):
    GROUP = Help.Command(('prefiks', 'prefix', 'przedrostek'), (), 'Grupa komend związanych z prefiksem.')
    COMMANDS = (
        Help.Command(('sprawdź', 'sprawdz'), (), 'Pokazuje obowiązujący prefiks.'),
        Help.Command(('ustaw'), (), 'Ustawia na serwerze podany prefiks. Wymaga uprawnień administratora.'),
        Help.Command(
            ('przywróć', 'przywroc'), (), 'Przywraca na serwerze domyślny prefiks. Wymaga uprawnień administratora.'
        )
    )
    HELP = Help(COMMANDS, group=GROUP)

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def prefix_usage_example(example_prefix: str) -> str:
        return (
            f'Przykład użycia: `{example_prefix}wersja` lub `{example_prefix} oof`.\n'
            'W wiadomościach prywatnych prefiks jest opcjonalny.'
        )

    @commands.group(aliases=['prefiks', 'przedrostek'], invoke_without_command=True)
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def prefix(self, ctx):
        """Command prefix commands."""
        await self.bot.send(ctx, embeds=self.HELP.embeds)

    @prefix.command(aliases=['sprawdź', 'sprawdz'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default
    )
    async def prefix_check(self, ctx):
        """Presents the current command prefix."""
        with data.session() as session:
            data_server = session.query(data.Server).get(ctx.guild.id) if ctx.guild is not None else None
            is_prefix_custom = data_server is not None and data_server.command_prefix is not None
            current_prefix = data_server.command_prefix if is_prefix_custom else configuration["command_prefix"]
            notice = f'Obowiązujący prefiks to "{current_prefix}"{" (wartość domyślna)" if not is_prefix_custom else ""}'
        await self.bot.send(ctx, embed=self.bot.generate_embed('🔧', notice, self.prefix_usage_example(current_prefix)))

    @prefix.command(aliases=['ustaw'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def prefix_set(self, ctx, *, new_prefix: str):
        """Sets a new command prefix."""
        with data.session(commit=True) as session:
            data_server = session.query(data.Server).get(ctx.guild.id)
            if len(new_prefix) > data.Server.COMMAND_PREFIX_MAX_LENGTH:
                raise commands.BadArgument
            data_server.command_prefix = new_prefix
        notice = f'Ustawiono nowy prefiks "{new_prefix}"'
        await self.bot.send(ctx, embed=self.bot.generate_embed('✅', notice, self.prefix_usage_example(new_prefix)))

    @prefix_set.error
    async def prefix_set_error(self, ctx, error):
        """Handles new command prefix setting errors."""
        notice = None
        if isinstance(error, commands.MissingRequiredArgument):
            notice = 'Nie podano nowego prefiksu'
        elif isinstance(error, commands.BadArgument):
            character_form = word_number_form(data.Server.COMMAND_PREFIX_MAX_LENGTH, "znak", "znaki", "znaków")
            notice = f'Nowy prefiks nie może być dłuższy niż {character_form}'
        if notice is not None:
            await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', notice))

    @prefix.command(aliases=['przywróć', 'przywroc'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def prefix_restore(self, ctx):
        """Reverts to the default command prefix."""
        with data.session(commit=True) as session:
            data_server = session.query(data.Server).get(ctx.guild.id)
            data_server.command_prefix = None
            new_prefix = configuration['command_prefix']
        await self.bot.send(ctx, embed=self.bot.generate_embed(
            '✅', f'Przywrócono domyślny prefiks "{new_prefix}"', self.prefix_usage_example(new_prefix)
        ))


somsiad = Somsiad()
somsiad.add_cog(Essentials(somsiad))
somsiad.add_cog(Prefix(somsiad))
