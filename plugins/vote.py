# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import asyncio
from collections import defaultdict
import datetime as dt
import re
from typing import DefaultDict, List, Optional, Set

import discord
from discord.ext import commands

import data
from core import cooldown
from somsiad import Somsiad
from utilities import human_datetime, interpret_str_as_datetime, md_link, utc_to_naive_local, word_number_form


class Ballot(data.Base, data.ChannelRelated, data.UserRelated):
    urn_message_id = data.Column(data.BigInteger, primary_key=True)
    matter = data.Column(data.String(300), nullable=False)
    letters = data.Column(data.String(26))  # This has to be null if numeric_scale is non-null
    commenced_at = data.Column(data.DateTime, nullable=False)
    conclude_at = data.Column(data.DateTime, nullable=False)
    has_been_concluded = data.Column(data.Boolean, nullable=False, default=False)
    numeric_scale_max = data.Column(data.SmallInteger)  # This has to be null if letters is non-null


class Vote(commands.Cog):
    LETTER_REGEX = re.compile(r'\b([A-Z])[\.\?\:](?=\s|$)')
    DIGIT_REGEX = re.compile(r'\b([1-9])[\.\?\:](?=\s|$)')
    EMOJI_MAPPING = {
        'A': '🇦',
        'B': '🇧',
        'C': '🇨',
        'D': '🇩',
        'E': '🇪',
        'F': '🇫',
        'G': '🇬',
        'H': '🇭',
        'I': '🇮',
        'J': '🇯',
        'K': '🇰',
        'L': '🇱',
        'M': '🇲',
        'N': '🇳',
        'O': '🇴',
        'P': '🇵',
        'Q': '🇶',
        'R': '🇷',
        'S': '🇸',
        'T': '🇹',
        'U': '🇺',
        'V': '🇻',
        'W': '🇼',
        'X': '🇽',
        'Y': '🇾',
        'Z': '🇿',
        1: '1️⃣',
        2: '2️⃣',
        3: '3️⃣',
        4: '4️⃣',
        5: '5️⃣',
        6: '6️⃣',
        7: '7️⃣',
        8: '8️⃣',
        9: '9️⃣',
    }
    NUMERIC_VALUE_MAPPING = {
        '1️⃣': 1,
        '2️⃣': 2,
        '3️⃣': 3,
        '4️⃣': 4,
        '5️⃣': 5,
        '6️⃣': 6,
        '7️⃣': 7,
        '8️⃣': 8,
        '9️⃣': 9,
    }
    MAX_MATTER_LENGTH = 256 # Discord's embed title limit

    ballots_set_off: Set[int]
    ballot_reaction_cleanup_tasks: DefaultDict[int, List[asyncio.Task]]

    def __init__(self, bot: Somsiad):
        self.bot = bot
        self.ballots_set_off = set()
        self.ballot_reaction_cleanup_tasks = defaultdict(list)

    async def set_off_ballot(
        self,
        urn_message_id: int,
        channel_id: int,
        user_id: int,
        matter: str,
        letters: Optional[str],
        numeric_scale_max: Optional[int],
        commenced_at: dt.datetime,
        conclude_at: dt.datetime,
    ):
        if urn_message_id in self.ballots_set_off:
            return
        self.ballots_set_off.add(urn_message_id)
        await discord.utils.sleep_until(conclude_at.astimezone())  # Waiting till conclusion
        if urn_message_id not in self.ballots_set_off:
            return
        self.ballots_set_off.remove(urn_message_id)
        channel = await self.bot.fetch_channel(channel_id)
        try:
            urn_message = await channel.fetch_message(urn_message_id)
        except (AttributeError, discord.NotFound):
            pass
        else:
            emojis = self._list_answers(letters=letters, numeric_scale_max=numeric_scale_max)
            results = {
                reaction.emoji: reaction.count - 1 for reaction in urn_message.reactions if reaction.emoji in emojis
            }
            winning_emojis = []
            winning_count = 1  # 0 is never a winning count
            numeric_result = None  # Only used if numeric scale is used
            for emoji, count in results.items():
                if count > winning_count:
                    winning_emojis = [emoji]
                    winning_count = count
                elif count == winning_count:
                    winning_emojis.append(emoji)
            if not numeric_scale_max:
                winning_emoji = (
                    winning_emojis[0]
                    if len(winning_emojis) == 1
                    else (f'{"​".join(winning_emojis)} (ex aequo)' if winning_emojis and letters else '❓')
                )
            else:
                response_count = sum(results.values())
                if response_count > 0:
                    numeric_result = (
                        sum(self.NUMERIC_VALUE_MAPPING[emoji] * count for emoji, count in results.items()) / response_count
                    )
                    winning_emoji = self.EMOJI_MAPPING.get(round(numeric_result))
                else:
                    numeric_result = None
                    winning_emoji = '❓'

            results_description = md_link(
                f'Wyniki głosowania ogłoszonego {human_datetime(commenced_at)}.', urn_message.jump_url
            )
            urn_embed = self.bot.generate_embed(winning_emoji, matter)
            results_embed = self.bot.generate_embed(winning_emoji, matter, results_description)
            if letters:
                positions = (f'Opcja {letter}' for letter in letters)
            elif numeric_scale_max:
                positions = (f'Opcja {i}' for i in range(1, numeric_scale_max + 1))
            else:
                positions = ('Za', 'Przeciw')
            total_count = sum(results.values()) or 1  # guard against zero-division
            for position, emoji in zip(positions, emojis):
                this_count = results.get(emoji)
                if this_count is None:
                    continue
                this_percentage = this_count / total_count * 100
                count_presentation = f'{this_count:n} ({round(this_percentage):n}%)'
                if emoji in winning_emojis and winning_count > 0:
                    count_presentation = f'**{count_presentation}**'
                urn_embed.add_field(name=position, value=count_presentation)
                results_embed.add_field(name=position, value=count_presentation)
            if numeric_result is not None:
                numeric_result_presentation = f'{numeric_result:.2f}'
                urn_embed.add_field(name='Średnia', value=numeric_result_presentation, inline=False)
                results_embed.add_field(name='Średnia', value=numeric_result_presentation, inline=False)
            results_message = await channel.send(f'<@{user_id}>', embed=results_embed)
            urn_embed.description = md_link(
                f'Głosowanie zostało zakończone {human_datetime()}.', results_message.jump_url
            )
            await urn_message.edit(embed=urn_embed)
        with data.session(commit=True) as session:
            reminder = session.query(Ballot).get(urn_message_id)
            reminder.has_been_concluded = True

    @commands.Cog.listener()
    async def on_ready(self):
        with data.session() as session:
            for reminder in session.query(Ballot).filter(Ballot.has_been_concluded == False):
                self.bot.loop.create_task(
                    self.set_off_ballot(
                        reminder.urn_message_id,
                        reminder.channel_id,
                        reminder.user_id,
                        reminder.matter,
                        reminder.letters,
                        reminder.numeric_scale_max,
                        reminder.commenced_at,
                        reminder.conclude_at,
                    )
                )

    @cooldown()
    @commands.command(aliases=['głosowanie', 'glosowanie', 'poll', 'ankieta'])
    async def vote(
        self,
        ctx,
        conclude_at: Optional[interpret_str_as_datetime] = None,
        *,
        matter: commands.clean_content(fix_channel_mentions=True),
    ):
        if len(matter) > self.MAX_MATTER_LENGTH:
            raise commands.BadArgument
        letters = ''.join((match[0] for match in self.LETTER_REGEX.findall(matter)))
        numeric_scale_max = None
        if len(letters) < 2:
            letters = ''
            digits = [int(match[0]) for match in self.DIGIT_REGEX.findall(matter)]
            if len(digits) >= 2:
                numeric_scale_max = max(digits)
        description = 'Zagłosuj w tej sprawie przy użyciu reakcji.'
        if numeric_scale_max:
            description += ' Można zaznaczyć tylko jedną opcję.'
        if conclude_at is not None:
            description += (
                f'\n**Wyniki zostaną ogłoszone {human_datetime(conclude_at)}.**\n*Ogłoszenie wyników zostanie '
                'anulowane jeśli usuniesz tę wiadomość (możesz zrobić to komendą `nie`).*'
            )
        embed = self.bot.generate_embed('🗳', matter, description, timestamp=conclude_at)
        urn_message = await self.bot.send(ctx, embed=embed)
        if urn_message is None:
            return
        options = self._list_answers(letters=letters, numeric_scale_max=numeric_scale_max)
        try:
            for option in options:
                await urn_message.add_reaction(option)
            details = {
                'urn_message_id': urn_message.id,
                'channel_id': ctx.channel.id,
                'matter': matter,
                'letters': letters,
                'numeric_scale_max': numeric_scale_max,
                'user_id': ctx.author.id,
                'commenced_at': utc_to_naive_local(ctx.message.created_at),
                'conclude_at': conclude_at,
            }
            if conclude_at is not None:
                with data.session(commit=True) as session:
                    reminder = Ballot(**details)
                    session.add(reminder)
                    self.bot.loop.create_task(self.set_off_ballot(**details))
        except discord.Forbidden:
            await urn_message.delete()
            embed = self.bot.generate_embed('⚠️', 'Bot nie ma uprawnień do dodawania reakcji')
        except:
            await urn_message.delete()
            raise

    @vote.error
    async def vote_error(self, ctx, error):
        notice = None
        description = None
        if isinstance(error, commands.MissingRequiredArgument):
            notice = 'Nie podano sprawy w jakiej ma się odbyć głosowanie'
            description = (
                '↕️ Głosowania domyślnie odbywają się w trybie "za/przeciw".\n'
                '🔠 By głosować nad wieloma opcjami, użyj formatu "A. Opcja pierwsza, B. Opcja druga, ...". Rezultatem będzie opcja z największą liczbą głosów.\n'
                '🔢 By głosować w skali od 1 do n, użyj formatu "1. Opcja pierwsza, 2. Opcja druga, ..., n. Opcja n-ta". Rezultatem będzie uśredniona wartość odpowiedzi.'
            )
        elif isinstance(error, commands.BadArgument):
            character_form = word_number_form(self.MAX_MATTER_LENGTH, 'znak', 'znaki', 'znaków')
            notice = f'Tekst sprawy nie może być dłuższy niż {character_form}'
        if notice is not None:
            embed = self.bot.generate_embed('⚠️', notice, description)
            await self.bot.send(ctx, embed=embed)

    def _list_answers(self, *, letters: Optional[str], numeric_scale_max: Optional[int]) -> List[str]:
        if letters:
            return [self.EMOJI_MAPPING.get(letter.upper()) for letter in letters]
        if numeric_scale_max:
            return [self.EMOJI_MAPPING.get(i) for i in range(1, numeric_scale_max + 1)]
        return ['👍', '👎']

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """Ensure that users can only vote once on numeric ballots."""
        if user.bot or reaction.emoji not in self.NUMERIC_VALUE_MAPPING:
            return
        with data.session() as session:
            ballot = session.query(Ballot).get(reaction.message.id)
        if not ballot or ballot.numeric_scale_max is None or ballot.has_been_concluded:
            return
        for registered_task in self.ballot_reaction_cleanup_tasks[reaction.message.id]:
            registered_task.cancel()
        reactions_to_decrement = [
            other_reaction
            for other_reaction in reaction.message.reactions
            if other_reaction.emoji in self.NUMERIC_VALUE_MAPPING and other_reaction.emoji != reaction.emoji
        ]
        for other_reaction in reactions_to_decrement:
            self.ballot_reaction_cleanup_tasks[reaction.message.id].append(
                asyncio.create_task(other_reaction.remove(user))
            )

async def setup(bot: Somsiad):
    await bot.add_cog(Vote(bot))
