# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from discord.ext import commands
from core import somsiad
from configuration import configuration


class Invite(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['zaproś', 'zapros'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    @commands.guild_only()
    async def invite(self, ctx, *, argument = ''):
        is_user_permitted_to_invite = False
        for channel in ctx.guild.channels:
            if channel.permissions_for(ctx.author).create_instant_invite:
                is_user_permitted_to_invite = True
                break
        if 'somsiad' in argument or ctx.me in ctx.message.mentions:
            embed = self.bot.generate_embed(
                '🏠', 'Zapraszam do Somsiad Labs – mojego domu', 'http://discord.gg/xRCpDs7',
                url='http://discord.gg/xRCpDs7'
            )
        elif is_user_permitted_to_invite:
            max_uses = 0
            unique = False
            for word in argument.split():
                if 'now' in word.lower() or 'twórz' in word.lower() or 'tworz' in word.lower():
                    unique = True
                if 'jednoraz' in word.lower():
                    max_uses = 1
                else:
                    try:
                        max_uses = abs(int(word))
                    except ValueError:
                        pass
            channel = None
            if ctx.channel.permissions_for(ctx.me).create_instant_invite:
                channel = ctx.channel
            else:
                for current_channel in ctx.guild.channels:
                    if (current_channel.permissions_for(ctx.me).create_instant_invite
                            and current_channel.permissions_for(ctx.author).create_instant_invite
                            and not isinstance(current_channel, discord.CategoryChannel)):
                        channel = current_channel
                        break
            invite = await channel.create_invite(
                max_uses=max_uses,
                unique=unique,
                reason=str(ctx.author)
            )
            if channel is None:
                embed = self.bot.generate_embed(
                    '⚠️', 'Nie utworzono zaproszenia, bo bot nie ma do tego uprawnień na żadnym kanale, '
                    'na którym ty je masz'
                )
            else:
                if max_uses == 0:
                    max_uses_info = ' o nieskończonej liczbie użyć'
                elif max_uses == 1:
                    max_uses_info = ' jednorazowe'
                else:
                    max_uses_info = f' o {max_uses} użyciach'
                embed = self.bot.generate_embed(
                    '✅', f'Utworzono{max_uses_info if max_uses == 1 else ""} zaproszenie na kanał '
                    f'{"#" if isinstance(channel, discord.TextChannel) else ""}{channel}'
                    f'{max_uses_info if max_uses != 1 else ""}', invite.url, url=invite.url
                )
        else:
            embed = self.bot.generate_embed(
                '⚠️' 'Nie utworzono zaproszenia, bo nie masz do tego uprawnień na żadnym kanale'
            )
        await self.bot.send(ctx, embed=embed)


somsiad.add_cog(Invite(somsiad))
