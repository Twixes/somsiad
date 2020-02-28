# Copyright 2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Union
from collections import Counter
import colorsys
import discord
from discord.ext import commands
from core import Help, somsiad
from configuration import configuration


class Colors(commands.Cog):
    GROUP = Help.Command(
        ('kolory', 'kolor', 'kolorki', 'kolorek'), (),
        'Komendy związane z kolorami nicków samodzielnie wybieranymi przez użytkowników. '
        'Odbywa się to z użyciem kolorów–ról, tzn. ról zaczynających się prefiksem "🎨 ".'
    )
    COMMANDS = (
        Help.Command(('role', 'lista'), (), 'Zwraca listę dostępnych kolorów–ról.'),
        Help.Command('ustaw', 'kolor–rola', 'Ustawia ci wybrany <kolor–rolę>.'),
        Help.Command(('wyczyść', 'wyczysc'), (), 'Wyczyszcza twój kolor.')
    )
    HELP = Help(COMMANDS, group=GROUP)

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(
        invoke_without_command=True, case_insensitive=True, aliases=['kolory', 'kolor', 'kolorki', 'kolorek']
    )
    @commands.cooldown(1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default)
    @commands.guild_only()
    async def colors(self, ctx):
        await self.bot.send(ctx, embeds=self.HELP.embeds)

    @colors.command(aliases=['role', 'lista'])
    @commands.cooldown(1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default)
    @commands.guild_only()
    async def roles(self, ctx):
        relevant_roles = filter(lambda role: role.name.startswith('🎨 '), ctx.guild.roles)
        roles_counter = Counter((role for member in ctx.guild.members for role in member.roles))
        sorted_roles = sorted(relevant_roles, key=lambda role: colorsys.rgb_to_hsv(*role.color.to_rgb()))
        role_parts = (f'{role.mention} – `{str(role.color).upper()}` – {roles_counter[role]}' for role in sorted_roles)
        embed = somsiad.generate_embed('🎨', 'Dostępne role kolorowe', '\n'.join(role_parts))
        await self.bot.send(ctx, embed=embed)

    @colors.command(aliases=['ustaw'])
    @commands.cooldown(1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default)
    @commands.guild_only()
    async def set(self, ctx, *, role_candidate: Union[discord.Role, str]):
        role = None
        if isinstance(role_candidate, str):
            role_name = role_candidate.lstrip('🎨').lstrip().lower()
            for this_role in ctx.guild.roles:
                if this_role.name.startswith('🎨 ') and this_role.name.lstrip('🎨').lstrip().lower() == role_name:
                    role = this_role
                    break
        elif isinstance(role_candidate, discord.Role) and role_candidate.name.startswith('🎨 '):
            role = role_candidate
        if role is None:
            embed = somsiad.generate_embed('⚠️', 'Nie znaleziono pasującego koloru–roli')
        else:
            role_name = role.name.lstrip('🎨').lstrip()
            already_present = False
            roles_for_removal = []
            for this_role in ctx.author.roles:
                if this_role.name.startswith('🎨 '):
                    if this_role == role:
                        already_present = True
                    else:
                        roles_for_removal.append(this_role)
            try:
                if roles_for_removal:
                    await ctx.author.remove_roles(*roles_for_removal)
                if not already_present:
                    await ctx.author.add_roles(role)
                    emoji, notice = '✅', f'Ustawiono ci kolor–rolę {role_name}'
                else:
                    emoji, notice = 'ℹ️', f'Już masz kolor–rolę {role_name}'
                description = f'{role.mention} – `{str(role.color).upper()}`'
            except discord.Forbidden:
                emoji, notice, description = '⚠️', 'Bot nie ma wymaganych do tego uprawnień (zarządzanie rolami)', None
            embed = somsiad.generate_embed(emoji, notice, description)
        await self.bot.send(ctx, embed=embed)

    @set.error
    async def set_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = somsiad.generate_embed('⚠️', 'Nie podano koloru–roli')
            await self.bot.send(ctx, embed=embed)

    @colors.command(aliases=['wyczyść', 'wyczysc'])
    @commands.cooldown(1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default)
    @commands.guild_only()
    async def clear(self, ctx):
        roles_for_removal = [role for role in ctx.author.roles if role.name.startswith('🎨 ')]
        if roles_for_removal:
            try:
                await ctx.author.remove_roles(*roles_for_removal)
            except discord.Forbidden:
                emoji, notice = '⚠️', 'Bot nie ma wymaganych do tego uprawnień (zarządzanie rolami)'
            else:
                emoji, notice = '✅', 'Usunięto twój kolor–rolę'
        else:
            emoji, notice = 'ℹ️', 'Nie masz koloru–roli do usunięcia'
        embed = somsiad.generate_embed(emoji, notice)
        await self.bot.send(ctx, embed=embed)


somsiad.add_cog(Colors(somsiad))
