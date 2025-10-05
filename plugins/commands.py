# Copyright 2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from core import Invocation, is_user_opted_out_of_data_processing
import datetime as dt
import posthog
from somsiad import Somsiad, SomsiadMixin

from discord.ext import commands

import data
from utilities import text_snippet, utc_to_naive_local


class Commands(commands.Cog, SomsiadMixin):
    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        with data.session(commit=True) as session:
            if not ctx.command or is_user_opted_out_of_data_processing(session, ctx.author.id):
                return
            invocation = Invocation(
                id=discord.utils.time_snowflake(dt.datetime.now()),
                message_id=ctx.message.id,
                server_id=ctx.guild.id if ctx.guild is not None else None,
                channel_id=ctx.channel.id,
                user_id=ctx.author.id,
                prefix=ctx.prefix,
                full_command=ctx.command.qualified_name,
                root_command=str(ctx.command.root_parent or ctx.command.qualified_name),
                created_at=utc_to_naive_local(ctx.message.created_at),
            )
            session.add(invocation)

            # Track command invocation in PostHog
            posthog.capture(
                distinct_id=str(ctx.author.id),
                event='command_invoked',
                properties={
                    'command': ctx.command.qualified_name,
                    'root_command': ctx.command.root_parent or ctx.command.qualified_name,
                    'prefix': ctx.prefix,
                    'server_id': ctx.guild.id if ctx.guild else None,
                    'server_name': ctx.guild.name if ctx.guild else None,
                    'channel_id': ctx.channel.id,
                    'is_dm': ctx.guild is None,
                }
            )

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        with data.session(commit=True) as session:
            if is_user_opted_out_of_data_processing(session, ctx.author.id):
                return
            invocation = session.query(Invocation).get(ctx.message.id)
            if invocation is not None:
                invocation.exited_at = dt.datetime.now()

                # Track command completion in PostHog
                duration_ms = (invocation.exited_at - invocation.created_at).total_seconds() * 1000
                posthog.capture(
                    distinct_id=str(ctx.author.id),
                    event='command_completed',
                    properties={
                        'command': ctx.command.qualified_name,
                        'root_command': ctx.command.root_parent or ctx.command.qualified_name,
                        'duration_ms': duration_ms,
                        'server_id': ctx.guild.id if ctx.guild else None,
                    }
                )

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        with data.session(commit=True) as session:
            if is_user_opted_out_of_data_processing(session, ctx.author.id):
                return
            invocation = session.query(Invocation).get(ctx.message.id)
            if invocation is not None:
                invocation.exited_at = dt.datetime.now()
                error_message = text_snippet(
                    str(error).replace('Command raised an exception: ', ''), Invocation.MAX_ERROR_LENGTH
                )
                invocation.error = error_message

                # Track command error in PostHog
                posthog.capture(
                    distinct_id=str(ctx.author.id),
                    event='command_error',
                    properties={
                        'command': ctx.command.qualified_name if ctx.command else 'unknown',
                        'root_command': ctx.command.root_parent or ctx.command.qualified_name if ctx.command else 'unknown',
                        'error_type': type(error).__name__,
                        'error_message': error_message,
                        'server_id': ctx.guild.id if ctx.guild else None,
                    }
                )


async def setup(bot: Somsiad):
    await bot.add_cog(Commands(bot))
