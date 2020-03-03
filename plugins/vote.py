# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Optional
import re
import datetime as dt
import discord
from discord.ext import commands
from core import ChannelRelated, UserRelated, somsiad
from configuration import configuration
from utilities import utc_to_naive_local, human_timedelta, interpret_str_as_datetime, md_link
import data


class Ballot(data.Base, ChannelRelated, UserRelated):
    urn_message_id = data.Column(data.BigInteger, primary_key=True)
    matter = data.Column(data.String(50), nullable=False)
    letters = data.Column(data.String(26))
    commenced_at = data.Column(data.DateTime, nullable=False)
    conclude_at = data.Column(data.DateTime, nullable=False)
    has_been_concluded = data.Column(data.Boolean, nullable=False, default=False)


class Vote(commands.Cog):
    LETTER_REGEX = re.compile(r'\b([A-Z])[\.\?\:](?=\s|$)')
    LETTER_EMOJIS = {
        'A': '🇦', 'B': '🇧', 'C': '🇨', 'D': '🇩', 'E': '🇪', 'F': '🇫', 'G': '🇬', 'H': '🇭', 'I': '🇮', 'J': '🇯',
        'K': '🇰', 'L': '🇱', 'M': '🇲', 'N': '🇳', 'O': '🇴', 'P': '🇵', 'Q': '🇶', 'R': '🇷', 'S': '🇸', 'T': '🇹',
        'U': '🇺', 'V': '🇻', 'W': '🇼', 'X': '🇽', 'Y': '🇾', 'Z': '🇿'
    }

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def set_off_ballot(
            self, urn_message_id: int, channel_id: int, user_id: int, matter: str, letters: Optional[str],
            commenced_at: dt.datetime, conclude_at: dt.datetime
    ):
        await discord.utils.sleep_until(conclude_at.astimezone())
        channel = self.bot.get_channel(channel_id)
        try:
            urn_message = await channel.fetch_message(urn_message_id)
        except discord.NotFound:
            pass
        else:
            emojis = ('👍', '👎') if letters is None else tuple(map(self.LETTER_EMOJIS.get, letters))
            results = {
                reaction.emoji: reaction.count - 1 for reaction in urn_message.reactions if reaction.emoji in emojis
            }
            winning_emojis = []
            winning_count = -1
            for option in results.items():
                if option[1] > winning_count:
                    winning_emojis = [option[0]]
                    winning_count = option[1]
                elif option[1] == winning_count:
                    winning_emojis.append(option[0])
            winning_emoji = '❓' if len(winning_emojis) != 1 else winning_emojis[0]
            results_description = md_link(
                f'Wyniki głosowania ogłoszonego {human_timedelta(commenced_at)}.', urn_message.jump_url
            )
            urn_embed = self.bot.generate_embed(winning_emoji, matter)
            results_embed = self.bot.generate_embed(winning_emoji, matter, results_description)
            positions = ('Za', 'Przeciw') if letters is None else (f'Opcja {letter}' for letter in letters)
            for position, emoji in zip(positions, emojis):
                if emoji in winning_emojis and winning_count > 0:
                    count_presentation = f'**{results[emoji]}**'
                else:
                    count_presentation = results[emoji]
                urn_embed.add_field(name=position, value=count_presentation)
                results_embed.add_field(name=position, value=count_presentation)
            results_message = await channel.send(f'<@{user_id}>', embed=results_embed)
            urn_embed.description = md_link(
                f'Głosowanie zostało zakończone {human_timedelta()}.', results_message.jump_url
            )
            await urn_message.edit(embed=urn_embed)
        with data.session(commit=True) as session:
            reminder = session.query(Ballot).get(urn_message_id)
            reminder.has_been_concluded = True

    @commands.Cog.listener()
    async def on_ready(self):
        with data.session() as session:
            for reminder in session.query(Ballot).filter(Ballot.has_been_concluded == False):
                self.bot.loop.create_task(self.set_off_ballot(
                    reminder.urn_message_id, reminder.channel_id, reminder.user_id, reminder.matter,
                    reminder.letters, reminder.commenced_at, reminder.conclude_at
                ))

    @commands.command(aliases=['głosowanie', 'glosowanie', 'poll', 'ankieta'])
    @commands.cooldown(1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default)
    async def vote(
            self, ctx, conclude_at: Optional[interpret_str_as_datetime] = None,
            *, matter: commands.clean_content(fix_channel_mentions=True)
    ):
        letters = ''.join({match[0]: None for match in self.LETTER_REGEX.findall(matter)})
        #''.join([
        #    letter for letter in self.LETTER_EMOJIS if f'{letter}.' in matter or f'{letter}:' in matter
        #])
        if len(letters) < 2:
            letters = None
        description = 'Zagłosuj w tej sprawie przy użyciu reakcji.'
        if conclude_at is not None:
            description += f'\nWynik zostanie ogłoszony {human_timedelta(conclude_at)}.'
        embed = self.bot.generate_embed('🗳', matter, description)
        urn_message = await self.bot.send(ctx, embed=embed)
        options = ('👍', '👎') if letters is None else tuple(map(self.LETTER_EMOJIS.get, letters))
        for option in options:
            await urn_message.add_reaction(option)
        try:
            details = {
                'urn_message_id': urn_message.id, 'channel_id': ctx.channel.id, 'matter': matter, 'letters': letters,
                'user_id': ctx.author.id, 'commenced_at': utc_to_naive_local(ctx.message.created_at),
                'conclude_at': conclude_at
            }
            if conclude_at is not None:
                with data.session(commit=True) as session:
                    reminder = Ballot(**details)
                    session.add(reminder)
                    self.bot.loop.create_task(self.set_off_ballot(**details))
        except:
            await urn_message.delete()
            raise

    @vote.error
    async def vote_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = self.bot.generate_embed('⚠️', 'Nie podano sprawy w jakiej ma się odbyć głosowanie')
            await self.bot.send(ctx, embed=embed)


somsiad.add_cog(Vote(somsiad))
