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
import random
import colorsys
import discord
from discord.ext import commands
from core import Help, somsiad
from configuration import configuration


class Colors(commands.Cog):
    GROUP = Help.Command(
        ('kolory', 'kolor', 'kolorki', 'kolorek'), (),
        'Komendy związane z kolorami nicków samodzielnie wybieranymi przez użytkowników. '
        'Odbywa się to z użyciem ról o nazwie zaczynającej się prefiksem "🎨 ".'
    )
    COMMANDS = (
        Help.Command(('role', 'lista'), (), 'Zwraca listę dostępnych kolorów–ról.'),
        Help.Command('ustaw', 'kolor–rola', 'Ustawia ci wybrany <kolor–rolę>.'),
        Help.Command(
            'pokaż', '?użytkownik/kolor–rola', 'Pokazuje kolor–rolę <użytkownika> lub <kolor–rolę>. '
            'Jeśli nie podano <?użytkownika/koloru–roli>, pokazuje twój kolor–rolę.'
        ),
        Help.Command(('wyczyść', 'wyczysc'), (), 'Wyczyszcza twój kolor.')
    )
    HELP = Help(COMMANDS, '🎨', group=GROUP)
    GRAY = 0xcdd7de

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
        relevant_roles = list(filter(lambda role: role.name.startswith('🎨 '), ctx.guild.roles))
        roles_counter = Counter((role for member in ctx.guild.members for role in member.roles))
        sorted_roles = sorted(relevant_roles, key=lambda role: colorsys.rgb_to_hsv(*role.color.to_rgb()))
        role_parts = (
            f'{role.mention} – `{str(role.color).upper()}` – 👥 {roles_counter[role]}' for role in sorted_roles
        )
        if relevant_roles:
            emoji, notice = '🎨', 'Dostępne kolory–role'
            description = '\n'.join(role_parts)
            color = random.choice(relevant_roles).color
        else:
            emoji, notice = '❔', 'Brak kolorów–ról'
            description = None
            color = self.GRAY
        embed = self.bot.generate_embed(emoji, notice, description, color=color)
        await self.bot.send(ctx, embed=embed)

    @colors.command(aliases=['ustaw'])
    @commands.cooldown(1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default)
    @commands.guild_only()
    async def set(self, ctx, *, role_candidate: Union[discord.Role, str]):
        role = None
        description = None
        if isinstance(role_candidate, str):
            role_name = role_candidate.lstrip('🎨').lstrip().lower()
            for this_role in ctx.guild.roles:
                if this_role.name.startswith('🎨 ') and this_role.name.lstrip('🎨').lstrip().lower() == role_name:
                    role = this_role
                    break
        elif isinstance(role_candidate, discord.Role) and role_candidate.name.startswith('🎨 '):
            role = role_candidate
        if role is None:
            emoji, notice = '⚠️', 'Nie znaleziono pasującego koloru–roli'
            color = self.GRAY
        else:
            role_name = role.name.lstrip('🎨').lstrip()
            color = role.color
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
                roles_counter = Counter((role for member in ctx.guild.members for role in member.roles))
                description = f'{role.mention} – `{str(role.color).upper()}` – 👥 {roles_counter[role]}'
            except discord.Forbidden:
                emoji, notice = '⚠️', 'Bot nie ma wymaganych do tego uprawnień (zarządzanie rolami)'
        embed = self.bot.generate_embed(emoji, notice, description, color=color)
        await self.bot.send(ctx, embed=embed)

    @set.error
    async def set_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = self.bot.generate_embed('⚠️', 'Nie podano koloru–roli')
            await self.bot.send(ctx, embed=embed)

    @colors.command(aliases=['pokaż', 'pokaz'])
    @commands.cooldown(1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default)
    @commands.guild_only()
    async def show(self, ctx, *, subject_candidate: Union[discord.Member, discord.Role, str] = None):
        subject_candidate = subject_candidate or ctx.author
        role = None
        about_member = None
        if isinstance(subject_candidate, discord.Member):
            for this_role in subject_candidate.roles:
                if this_role.name.startswith('🎨 '):
                    role = this_role
                    break
            about_member = subject_candidate
        elif isinstance(subject_candidate, discord.Role) and subject_candidate.name.startswith('🎨 '):
            role = subject_candidate
        elif isinstance(subject_candidate, str):
            role_name = subject_candidate.lstrip('🎨').lstrip().lower()
            for this_role in ctx.guild.roles:
                if this_role.name.startswith('🎨 ') and this_role.name.lstrip('🎨').lstrip().lower() == role_name:
                    role = this_role
                    break
        if role is not None:
            roles_counter = Counter((role for member in ctx.guild.members for role in member.roles))
            description = f'{role.mention} – `{str(role.color).upper()}` – 👥 {roles_counter[role]}'
            color = role.color
            if about_member is not None:
                address = 'Masz' if about_member == ctx.author else f'{about_member} ma'
                emoji, notice = '🎨', f'{address} kolor–rolę {role.name.lstrip("🎨").lstrip()}'
            else:
                emoji, notice = '🎨', f'Kolor–rola {role.name.lstrip("🎨").lstrip()}'
        else:
            description = None
            if about_member is not None:
                address = 'Nie masz' if about_member == ctx.author else f'{about_member} nie ma'
                emoji, notice = '❔', f'{address} koloru–roli'
                color = self.GRAY
            else:
                emoji, notice = '⚠️', 'Nie znaleziono pasującego użytkownika ani koloru–roli'
                color = None
        embed = self.bot.generate_embed(emoji, notice, description, color=color)
        await self.bot.send(ctx, embed=embed)

    @colors.command(aliases=['wyczyść', 'wyczysc'])
    @commands.cooldown(1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default)
    @commands.guild_only()
    async def clear(self, ctx):
        roles_for_removal = [role for role in ctx.author.roles if role.name.startswith('🎨 ')]
        color = self.GRAY
        if roles_for_removal:
            try:
                await ctx.author.remove_roles(*roles_for_removal)
            except discord.Forbidden:
                emoji, notice = '⚠️', 'Bot nie ma wymaganych do tego uprawnień (zarządzanie rolami)'
                color = None
            else:
                emoji, notice = '✅', 'Usunięto twój kolor–rolę'
        else:
            emoji, notice = 'ℹ️', 'Nie masz koloru–roli do usunięcia'
        embed = self.bot.generate_embed(emoji, notice, color=color)
        await self.bot.send(ctx, embed=embed)


somsiad.add_cog(Colors(somsiad))
