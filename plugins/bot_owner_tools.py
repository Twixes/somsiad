# Copyright 2018-2021 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from somsiad import Somsiad, SomsiadMixin
from typing import Optional, cast
import discord
from discord.ext import commands


class BotOwnerTools(commands.Cog, SomsiadMixin):
    @commands.command(aliases=['opuść', 'opusc'])
    @commands.is_owner()
    async def leave(self, ctx, *, server_name_or_id):
        """Leaves the provided server."""
        server = None
        for this_server in ctx.bot.guilds:
            if server_name_or_id in (this_server.name, str(this_server.id)):
                server = this_server
                break
        if server is not None:
            await server.leave()
            await self.bot.send(ctx, '✅ Pomyślnie opuszczono serwer')
        else:
            await self.bot.send(ctx, '⚠️ Nie znaleziono podanego serwera')

    @commands.command(aliases=['wylistuj'])
    @commands.is_owner()
    async def list_servers(self, ctx):
        """Lists all servers the bot is in, by users descending, to 50."""
        servers = sorted(ctx.bot.guilds, key=lambda x: x.member_count, reverse=True)[:25]
        embed = self.bot.generate_embed('📜', 'Lista serwerów')
        for server in servers:
            embed.add_field(name=server.name, value=f'{server.member_count} użytkowników')
        await self.bot.send(ctx, embed=embed)


    @commands.command(aliases=['wejdź', 'wejdz'])
    @commands.is_owner()
    async def enter(self, ctx, *, server_name_or_id):
        """Generates an invite to the provided server."""
        server = None
        invite = None
        for this_server in ctx.bot.guilds:
            if server_name_or_id in (this_server.name, str(this_server.id)):
                server = this_server
                break
        if server is not None:
            for channel in server.channels:
                if (
                    not isinstance(channel, discord.CategoryChannel)
                    and cast(discord.abc.GuildChannel, channel).permissions_for(server.me).create_instant_invite
                ):
                    try:
                        invite = await channel.create_invite(max_uses=1)
                    except:
                        continue
                    else:
                        break
        else:
            await self.bot.send(ctx, '⚠️ Nie znaleziono podanego serwera')
        if invite is not None:
            await self.bot.send(ctx, invite.url)
        else:
            await self.bot.send(ctx, '⚠️ Nie udało się utworzyć zaproszenia')

    @commands.group(aliases=['ogłoś', 'oglos'], case_insensitive=True)
    @commands.is_owner()
    async def announce(self, _):
        pass

    @announce.command(aliases=['globalnie'])
    @commands.is_owner()
    async def announce_globally(self, ctx, *, raw_announcement):
        """Makes an announcement on all servers smaller than 10000 members not containing "bot" in their name."""
        announcement = raw_announcement.replace('\\n', '\n').strip(';').split(';')
        if announcement[0].startswith('!'):
            description = announcement[0].lstrip('!').strip()
            announcement = announcement[1:]
        else:
            description = None
        embed = self.bot.generate_embed('📢', 'Ogłoszenie somsiedzkie', description)
        for n in range(0, len(announcement) - 1, 2):
            embed.add_field(name=announcement[n].strip(), value=announcement[n + 1].strip(), inline=False)
        for server in ctx.bot.guilds:
            if not server.name or 'bot' not in server.name.lower():
                for channel in server.text_channels:
                    if not channel.is_news():
                        try:
                            await channel.send(embed=embed)
                        except:
                            continue
                        else:
                            break

    @announce.command(aliases=['lokalnie'])
    @commands.guild_only()
    @commands.is_owner()
    async def announce_locally(self, ctx, *, raw_announcement):
        """Makes an announcement only on the server where the command was invoked."""
        announcement = raw_announcement.replace('\\n', '\n').strip(';').split(';')
        if announcement[0].startswith('!'):
            description = announcement[0].lstrip('!').strip()
            announcement = announcement[1:]
        else:
            description = None

        embed = self.bot.generate_embed('📢', 'Ogłoszenie somsiedzkie', description)

        for n in range(0, len(announcement) - 1, 2):
            embed.add_field(name=announcement[n].strip(), value=announcement[n + 1].strip(), inline=False)
        for channel in ctx.guild.text_channels:
            if channel.permissions_for(ctx.me).send_messages:
                await channel.send(embed=embed)
                break

    @commands.command(aliases=['wyślij', 'wyslij', 'sudo'])
    @commands.is_owner()
    async def send(self, ctx, channel_id: Optional[int] = None, *, content):
        if channel_id is None:
            channel = ctx.channel
            await ctx.message.delete()
        else:
            channel = self.bot.get_channel(channel_id)
        if channel is not None:
            await channel.send(content)
        else:
            await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', f'Nie znaleziono kanału o ID {channel_id}'))


async def setup(bot: Somsiad):
    await bot.add_cog(BotOwnerTools(bot))
