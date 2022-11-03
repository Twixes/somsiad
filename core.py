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
import random
from typing import List, Optional, Sequence, Union

import discord
from discord.ext import commands, tasks
from sqlalchemy.sql import functions

import data
from cache import redis_connection
from configuration import configuration
from somsiad import Somsiad, SomsiadMixin, OptedOutOfDataProcessing
from utilities import human_amount_of_time, word_number_form
from version import __copyright__, __version__
from sqlalchemy.orm import Session


class Invocation(data.MemberRelated, data.ChannelRelated, data.Base):
    MAX_ERROR_LENGTH = 300

    message_id = data.Column(data.BigInteger, primary_key=True)
    prefix = data.Column(data.String(max(23, data.Server.COMMAND_PREFIX_MAX_LENGTH)), nullable=False)
    full_command = data.Column(data.String(100), nullable=False, index=True)
    root_command = data.Column(data.String(100), nullable=False, index=True)
    created_at = data.Column(data.DateTime, nullable=False)
    exited_at = data.Column(data.DateTime)
    error = data.Column(data.String(MAX_ERROR_LENGTH))


class DataProcessingOptOut(data.UserSpecific, data.Base):
    pass


def is_user_opted_out_of_data_processing(session: Session, user_id: int) -> bool:
    return session.query(DataProcessingOptOut).get(user_id) is not None


def cooldown(
    rate: int = 1,
    per: float = configuration['command_cooldown_per_user_in_seconds'],
    type: commands.BucketType = commands.BucketType.user,
):
    def decorator(func):
        if isinstance(func, commands.Command):
            func._buckets = commands.CooldownMapping(commands.Cooldown(rate, per), type)
        else:
            raise ValueError("Decorator must be applied to command, not the function")
        return func

    return decorator


def did_not_opt_out_of_data_processing():
    async def predicate(ctx):
        with data.session() as session:
            if is_user_opted_out_of_data_processing(session, ctx.author.id):
                await ctx.bot.send(ctx, embed=ctx.bot.generate_embed('👤', 'Ta komenda wymaga Twojej zgody na przetwarzanie Twoich danych', "Możesz wyrazić ją za pomocą komendy `przetwarzanie-danych zapisz`."))
                raise OptedOutOfDataProcessing
        return True

    return commands.check(predicate)


def has_permissions(**perms):
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError('Invalid permission(s): %s' % (', '.join(invalid)))

    async def predicate(ctx):
        permissions = ctx.channel.permissions_for(ctx.author)
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]
        if missing:
            if not await ctx.bot.is_owner(ctx.author):
                raise commands.MissingPermissions(missing)  # type: ignore

        return True

    return commands.check(predicate)


class Help:
    """A help message generator."""

    class Command:
        "A command model."
        __slots__ = ('_aliases', '_arguments', '_description', '_emoji', '_examples')

        _aliases: Sequence[str]
        _arguments: Sequence[str]
        _description: str
        _emoji: Optional[str]
        _examples: Optional[List[str]]

        def __init__(
            self,
            aliases: Union[Sequence[str], str],
            arguments: Union[Sequence[str], str],
            description: str,
            emoji: Optional[str] = None,
            examples: Optional[List[str]] = None,
        ):
            self._aliases = (aliases,) if isinstance(aliases, str) else aliases
            self._arguments = (arguments,) if isinstance(arguments, str) else arguments
            self._description = description
            self._emoji = emoji
            self._examples = examples

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
            if self._examples:
                examples_joined = ", ".join((f"`{example}`" for example in self._examples))
                example_word_form = 'Przykład' if len(self._examples) == 1 else 'Przykłady'
                return f"{self._description}\n_{example_word_form}:_ {examples_joined}"
            return self._description

        @property
        def emoji(self) -> Optional[str]:
            return self._emoji

    __slots__ = ('group', 'embeds')

    def __init__(
        self,
        commands: Sequence[Command],
        emoji: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        *,
        group: Optional[Command] = None,
        footer_text: Optional[str] = None,
        footer_icon_url: Optional[str] = None,
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
                inline=False,
            )
        if footer_text:
            self.embeds[-1].set_footer(text=footer_text, icon_url=footer_icon_url)  # type: ignore


class Essentials(commands.Cog, SomsiadMixin):
    async def cog_load(self):
        self.heartbeat.start()

    def cog_unload(self):
        self.heartbeat.cancel()

    @tasks.loop(seconds=5)
    async def heartbeat(self):
        redis_connection.set('somsiad/heartbeat', dt.datetime.now().isoformat(), ex=15)
        redis_connection.set('somsiad/server_count', self.bot.server_count)
        redis_connection.set('somsiad/user_count', self.bot.user_count)
        redis_connection.set('somsiad/version', __version__)

    @cooldown()
    @commands.command(aliases=['wersja', 'v'])
    async def version(self, ctx, *, x=None):
        """Responds with current version of the bot."""
        if x and 'fccchk' in x.lower():
            emoji = '👺'
            notice = f'??? 6.6.6s'
            footer = '© 1963 👺'
        else:
            emoji = self.bot.get_random_emoji()
            notice = f'Somsiad {__version__}'
            footer = __copyright__
        embed = self.bot.generate_embed(emoji, notice, url=self.bot.WEBSITE_URL)
        embed.set_footer(text=footer)
        await self.bot.send(ctx, embed=embed)

    @cooldown()
    @commands.command(aliases=['informacje'])
    async def info(self, ctx, *, x: str = ''):
        """Responds with current version of the bot."""
        if 'fccchk' in x.lower():
            emoji = '👺'
            notice = f'??? 6.6.6'
            footer = '© 1963 👺'
            server_count = 193
            user_count = 7_802_385_004 + int((dt.datetime.now() - dt.datetime(2020, 1, 1)).total_seconds() * 2.5)
            mau_count = 1_323_519_222 + int((dt.datetime.now() - dt.datetime(2020, 1, 1)).total_seconds())
            sau_count = 194
            shard_count = 8
            runtime = human_amount_of_time(dt.datetime.now() - dt.datetime(1963, 11, 22))
            instance_owner = '👺'
            invite_url = 'https:///////////////////////////////'
        else:
            emoji = 'ℹ️'
            notice = f'Somsiad {__version__}'
            footer = __copyright__
            server_count = self.bot.server_count
            user_count = self.bot.user_count
            with data.session() as session:
                thirty_days_ago = dt.datetime.now() - dt.timedelta(30)
                mau_count = (
                    session.query(functions.count(Invocation.user_id.distinct()))
                    .filter(Invocation.created_at > thirty_days_ago)
                    .scalar()
                )
            shard_count = self.bot.shard_count or 1
            runtime = (
                'nieznany'
                if self.bot.ready_datetime is None
                else human_amount_of_time(dt.datetime.now() - self.bot.ready_datetime)
            )
            application_info = await self.bot.application_info()
            instance_owner = application_info.owner.mention
            invite_url = self.bot.invite_url()
        embed = self.bot.generate_embed(emoji, notice, url=self.bot.WEBSITE_URL)
        embed.add_field(name='Liczba serwerów', value=f'{server_count:n}')
        embed.add_field(name='Liczba użytkowników', value=f'{user_count:n}')
        embed.add_field(name='Liczba aktywnych użytkowników miesięcznie', value=f'{mau_count:n}')
        embed.add_field(name='Liczba shardów', value=f'{shard_count:n}')
        embed.add_field(name='Czas pracy', value=runtime)
        embed.add_field(name='Właściciel instancji', value=instance_owner)
        embed.add_field(name='Link zaproszeniowy bota', value=invite_url, inline=False)
        embed.set_footer(text=footer)
        await self.bot.send(ctx, embed=embed)

    @commands.command()
    async def ping(self, ctx, delay: Optional[float] = 0):
        """Pong!"""
        if delay is not None and delay > 0:
            await asyncio.sleep(delay)
        await self.bot.send(ctx, embed=self.bot.generate_embed('🏓', 'Pong!'))

    @commands.command()
    async def pińg(self, ctx, delay: Optional[float] = 0):
        """Pońg!"""
        if delay is not None and delay > 0:
            await asyncio.sleep(delay)
        await self.bot.send(ctx, embed=self.bot.generate_embed('🏓', 'Pońg!'))

    @cooldown()
    @commands.command(aliases=['nope', 'nie'])
    async def no(self, ctx, member: discord.Member = None):
        """Removes the last message sent by the bot in the channel on the requesting user's request."""
        member = member or ctx.author
        if member == ctx.author or ctx.channel.permissions_for(ctx.author).manage_messages:
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
        embed = self.bot.generate_embed('🛑', 'Wyłączam się…')
        await self.bot.send(ctx, embed=embed)
        await ctx.bot.close()

    @shutdown.error
    async def shutdown_error(self, ctx, error):
        """HAL 9000"""
        if isinstance(error, commands.NotOwner):
            embed = self.bot.generate_embed('🔴', f"I'm sorry, {ctx.author.display_name}, I'm afraid I can't do that")
            return await self.bot.send(ctx, embed=embed)
        raise error

    @commands.command(aliases=['restartuj', 'zrestartuj'])
    @commands.is_owner()
    async def restart(self, ctx):
        """Shuts down the bot."""
        embed = self.bot.generate_embed('🔁', 'Restartuję się…')
        await self.bot.send(ctx, embed=embed)
        await self.bot.close(1)

    restart.error(shutdown_error)

    @commands.command(aliases=['błąd', 'blad', 'błont', 'blont'])
    @commands.is_owner()
    async def error(self, ctx):
        """Causes an error."""
        1 / 0


class Prefix(commands.Cog, SomsiadMixin):
    GROUP = Help.Command(
        ('prefiks', 'prefix', 'przedrostek'), (), 'Komendy związane z własnymi serwerowymi prefiksami komend.'
    )
    COMMANDS = (
        Help.Command(('sprawdź', 'sprawdz'), (), 'Pokazuje obowiązujący prefiks bądź obowiązujące prefiksy.'),
        Help.Command(
            ('ustaw'),
            (),
            'Ustawia na serwerze podany prefiks bądź podane prefiksy oddzielone " lub ". '
            'Wymaga uprawnień administratora.',
        ),
        Help.Command(
            ('przywróć', 'przywroc'), (), 'Przywraca na serwerze domyślny prefiks. Wymaga uprawnień administratora.'
        ),
    )
    HELP = Help(COMMANDS, '🔧', group=GROUP)

    @cooldown()
    @commands.group(
        aliases=['prefixes', 'prefixy', 'prefiks', 'prefiksy', 'przedrostek', 'przedrostki'],
        invoke_without_command=True,
    )
    async def prefix(self, ctx):
        """Command prefix commands."""
        await self.bot.send(ctx, embed=self.HELP.embeds)

    @cooldown()
    @prefix.command(aliases=['sprawdź', 'sprawdz'])
    async def check(self, ctx):
        """Presents the current command prefix."""
        if not ctx.guild:
            extra_prefixes = ('', configuration['command_prefix'])
            extra_prefixes_presentation = f'brak lub domyślna `{configuration["command_prefix"]}`'
            notice = 'W wiadomościach prywatnych prefiks jest zbędny (choć obowiązuje też domyślny)'
        elif not self.bot.prefixes.get(ctx.guild.id):
            extra_prefixes = (configuration['command_prefix'],)
            extra_prefixes_presentation = f'domyślna `{configuration["command_prefix"]}`'
            notice = 'Obowiązuje domyślny prefiks'
        else:
            extra_prefixes = self.bot.prefixes[ctx.guild.id]
            applies_form = word_number_form(
                len(extra_prefixes), 'Obowiązuje', 'Obowiązują', 'Obowiązuje', include_number=False
            )
            prefix_form = word_number_form(
                len(extra_prefixes),
                'własny prefiks serwerowy',
                'własne prefiksy serwerowe',
                'własnych prefiksów serwerowych',
            )
            notice = f'{applies_form} {prefix_form}'
            extra_prefixes_presentation = ' lub '.join((f'`{prefix}`' for prefix in reversed(extra_prefixes)))
        embed = self.bot.generate_embed('🔧', notice)
        embed.add_field(
            name='Wartość' if len(extra_prefixes) == 1 else 'Wartości', value=extra_prefixes_presentation, inline=False
        )
        embed.add_field(
            name='Przykłady wywołań',
            value=(
                f'`{random.choice(extra_prefixes)}wersja` lub `{random.choice(extra_prefixes)} oof` lub `{ctx.me} urodziny`'
                if ctx.guild
                else f'`wersja` lub `{configuration["command_prefix"]} oof` lub `{ctx.me} urodziny`'
            ),
            inline=False,
        )
        await self.bot.send(ctx, embed=embed)

    @cooldown()
    @prefix.command(aliases=['ustaw'])
    @commands.guild_only()
    @has_permissions(administrator=True)
    async def set(self, ctx, *, new_prefixes_raw: str):
        """Sets a new command prefix."""
        new_prefixes = tuple(
            sorted(filter(None, (prefix.strip() for prefix in new_prefixes_raw.split(' lub '))), key=len, reverse=True)
        )
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
                value=' lub '.join((f'`{prefix}`' for prefix in reversed(previous_prefixes))),
                inline=False,
            )
        else:
            embed = self.bot.generate_embed('✅', f'Ustawiono {"prefiks" if len(new_prefixes) == 1 else "prefiksy"}')
            embed.add_field(
                name='Nowe wartości' if len(new_prefixes) > 1 else 'Nowa wartość',
                value=' lub '.join((f'`{prefix}`' for prefix in reversed(new_prefixes))),
                inline=False,
            )
            embed.add_field(
                name='Poprzednie wartości' if len(previous_prefixes) > 1 else 'Poprzednia wartość',
                value=previous_prefixes_presentation,
                inline=False,
            )
        embed.add_field(
            name='Przykłady wywołań',
            value=f'`{random.choice(new_prefixes)}wersja` lub `{random.choice(new_prefixes)} oof` '
            f'lub `{ctx.me} urodziny`',
            inline=False,
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

    @cooldown()
    @prefix.command(aliases=['przywróć', 'przywroc'])
    @commands.guild_only()
    @has_permissions(administrator=True)
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
                value=' lub '.join((f'`{prefix}`' for prefix in reversed(previous_prefixes))),
                inline=False,
            )
        embed.add_field(
            name='Przykłady wywołań',
            value=f'`{configuration["command_prefix"]}wersja` lub `{configuration["command_prefix"]} oof` '
            f'lub `{ctx.me} urodziny`',
            inline=False,
        )
        await self.bot.send(ctx, embed=embed)


somsiad = Somsiad()
