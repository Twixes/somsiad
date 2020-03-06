# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import sys
import discord
from discord.ext import commands
from core import cooldown


class BotOwnerTools(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['wejdź'])
    @cooldown()
    @commands.is_owner()
    async def enter(self, ctx, *, server_name):
        """Generates an invite to the provided server."""
        invite = None
        for server in ctx.bot.guilds:
            if server.name == server_name:
                for channel in server.channels:
                    if (
                            not isinstance(channel, discord.CategoryChannel)
                            and server.me.permissions_in(channel).create_instant_invite
                    ):
                        invite = await channel.create_invite(max_uses=1)
                        break
                break

        if invite is not None:
            await self.bot.send(ctx, invite.url)

    @commands.group(aliases=['ogłoś', 'oglos'], case_insensitive=True)
    @cooldown()
    @commands.is_owner()
    async def announce(self, _):
        pass

    @announce.command(aliases=['globalnie'])
    @cooldown()
    @commands.is_owner()
    async def announce_globally(self, ctx, *, raw_announcement):
        """Makes an announcement on all servers smaller than 10000 members not containing "bot" in their name."""
        announcement = raw_announcement.replace('\\n','\n').strip(';').split(';')
        if announcement[0].startswith('!'):
            description = announcement[0].lstrip('!').strip()
            announcement = announcement[1:]
        else:
            description = None

        embed = self.bot.generate_embed('📢', 'Ogłoszenie somsiedzkie', description)

        for n in range(0, len(announcement) - 1, 2):
            embed.add_field(name=announcement[n].strip(), value=announcement[n+1].strip(), inline=False)

        for server in ctx.bot.guilds:
            if 'bot' not in server.name.lower():
                for channel in server.text_channels:
                    if not channel.is_news():
                        try:
                            await channel.send(embed=embed)
                        except:
                            pass
                        else:
                            break

    @announce.command(aliases=['lokalnie'])
    @cooldown()
    @commands.is_owner()
    @commands.guild_only()
    async def announce_locally(self, ctx, *, raw_announcement):
        """Makes an announcement only on the server where the command was invoked."""
        announcement = raw_announcement.replace('\\n','\n').strip(';').split(';')
        if announcement[0].startswith('!'):
            description = announcement[0].lstrip('!').strip()
            announcement = announcement[1:]
        else:
            description = None

        embed = self.bot.generate_embed('📢', 'Ogłoszenie somsiedzkie', description)

        for n in range(0, len(announcement) - 1, 2):
            embed.add_field(name=announcement[n].strip(), value=announcement[n+1].strip(), inline=False)

        if ctx.guild.system_channel is not None and ctx.guild.system_channel.permissions_for(ctx.me).send_messages:
            await ctx.guild.system_channel.send(embed=embed)
        else:
            for channel in ctx.guild.text_channels:
                if channel.permissions_for(ctx.me).send_messages:
                    await channel.send(embed=embed)
                    break

    @commands.command(aliases=['wyłącz', 'wylacz', 'stop'])
    @cooldown()
    @commands.is_owner()
    async def shutdown(self, ctx):
        """Shuts down the bot."""
        embed = self.bot.generate_embed('🛑', 'Wyłączanie bota…')
        await self.bot.send(ctx, embed=embed)
        print(f'\nZatrzymuję działanie programu na żądanie {ctx.author}…')
        await ctx.bot.close()
        sys.exit()

    @commands.command(aliases=['błąd', 'blad', 'błont', 'blont'])
    @cooldown()
    @commands.is_owner()
    async def error(self, ctx):
        """Causes an error."""
        await self.bot.send(ctx, 1 / 0)


def setup(bot: commands.Bot):
    bot.add_cog(BotOwnerTools(bot))
