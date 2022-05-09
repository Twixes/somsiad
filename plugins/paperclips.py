# Copyright 2021 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import asyncio
from somsiad import Somsiad, SomsiadMixin
from typing import List
from discord_components import Button, Interaction, Component
from cache import redis_connection
import discord
from discord.ext import commands
import datetime as dt
from math import trunc

MACHINE_COST = 20
MACHINE_OUTPUT_PER_SECOND = 1


def calculate_current_inventory(clicks: int, machines: List[str]):
    now = dt.datetime.now()
    cumulative_machines_cost = len(machines) * MACHINE_COST
    cumulative_machines_output = sum(
        (
            trunc((now - dt.datetime.fromisoformat(machine)).total_seconds()) * MACHINE_OUTPUT_PER_SECOND
            for machine in machines
        )
    )
    return clicks - cumulative_machines_cost + cumulative_machines_output


class Paperclips(commands.Cog, SomsiadMixin):
    def generate_paperclips_embed(self, clicks: int, machines: List[str]) -> discord.Embed:
        embed = self.bot.generate_embed("👾", "Spinacze serwerowe")
        embed.add_field(name="Spinaczy w magazynie", value=calculate_current_inventory(clicks, machines), inline=False)
        if machines:
            embed.add_field(
                name="Tempo produkcji spinaczy", value=f"{len(machines)*MACHINE_OUTPUT_PER_SECOND}/s", inline=False
            )
            embed.add_field(name="Maszyn spinaczotworzących", value=len(machines), inline=False)
        return embed

    @commands.command(aliases=["spinacze"])
    async def paperclips(self, ctx: commands.Context):
        async def make_paperclip(interaction: Interaction):
            clicks = int(redis_connection.incr(f"somsiad/paperclips/{interaction.guild_id}/clicks"))
            machines = [
                x.decode('utf-8')
                for x in (redis_connection.lrange(f"somsiad/paperclips/{interaction.guild_id}/machines", 0, -1) or [])
            ]
            await interaction.edit_origin(
                embed=self.generate_paperclips_embed(clicks, machines), components=make_components(clicks, machines)
            )

        async def buy_paperclip_machine(interaction: Interaction):
            clicks = int(redis_connection.get(f"somsiad/paperclips/{interaction.guild_id}/clicks") or 0)
            machines = [
                x.decode('utf-8')
                for x in (redis_connection.lrange(f"somsiad/paperclips/{interaction.guild_id}/machines", 0, -1) or [])
            ]
            if calculate_current_inventory(clicks, machines) >= MACHINE_COST:
                now_string = dt.datetime.now().isoformat()
                redis_connection.rpush(f"somsiad/paperclips/{interaction.guild_id}/machines", now_string)
                machines.append(now_string)
                await interaction.edit_origin(
                    embed=self.generate_paperclips_embed(clicks, machines), components=make_components(clicks, machines)
                )
            else:
                await interaction.respond(
                    content=f"Nie masz wystarczająco spinaczy by zakupić maszynę! Jedna maszyna kosztuje {MACHINE_COST} spinaczy."
                )

        def make_components(clicks: int, machines: List[str]) -> List[Component]:
            current_inventory = calculate_current_inventory(clicks, machines)
            components = [
                self.bot.components_manager.add_callback(Button(emoji="📎", label="Zrób spinacz"), make_paperclip),
            ]
            if machines or current_inventory >= MACHINE_COST:
                components.append(
                    self.bot.components_manager.add_callback(
                        Button(
                            emoji="🛠",
                            label="Kup maszynę spinaczotworzącą (20 spinaczy)",
                            disabled=current_inventory < MACHINE_COST,
                        ),
                        buy_paperclip_machine,
                    )
                )
            return components

        clicks = int(redis_connection.get(f"somsiad/paperclips/{ctx.guild.id}/clicks") or 0)
        machines = [
            x.decode('utf-8')
            for x in (redis_connection.lrange(f"somsiad/paperclips/{ctx.guild.id}/machines", 0, -1) or [])
        ]
        message = await self.bot.send(
            ctx, embed=self.generate_paperclips_embed(clicks, machines), components=make_components(clicks, machines),
        )
        while True:
            await asyncio.sleep(5)
            clicks = int(redis_connection.get(f"somsiad/paperclips/{ctx.guild.id}/clicks") or 0)
            machines = [
                x.decode('utf-8')
                for x in (redis_connection.lrange(f"somsiad/paperclips/{ctx.guild.id}/machines", 0, -1) or [])
            ]
            await message.edit(
                embed=self.generate_paperclips_embed(clicks, machines), components=make_components(clicks, machines),
            )


def setup(bot: Somsiad):
    bot.add_cog(Paperclips(bot))
