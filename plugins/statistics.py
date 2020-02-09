# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Union
from collections import defaultdict, deque
import io
import datetime as dt
import calendar
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import discord
from discord.ext import commands
from core import Help, ServerRelated, ChannelRelated, UserRelated, somsiad
from configuration import configuration
from utilities import word_number_form, human_timedelta, rolling_average
import data


class MessageMetadata(data.Base, ServerRelated, ChannelRelated, UserRelated):
    __tablename__ = 'message_metadata_cache'

    id = data.Column(data.BigInteger, primary_key=True)
    word_count = data.Column(data.Integer, nullable=False)
    character_count = data.Column(data.Integer, nullable=False)
    hour = data.Column(data.SmallInteger, nullable=False)
    weekday = data.Column(data.SmallInteger, nullable=False)
    datetime = data.Column(data.DateTime, nullable=False)


class Report:
    """A statistics report. Can generate server, channel or member statistics."""
    COOLDOWN = max(float(configuration['command_cooldown_per_user_in_seconds']), 15.0)
    BACKGROUND_COLOR = '#2f3136'
    FOREGROUND_COLOR = '#ffffff'
    ROLL = 7

    queues = defaultdict(deque)

    plt.style.use('dark_background')

    def __init__(self, ctx: commands.Context, subject: Union[discord.Guild, discord.TextChannel]):
        self.ctx = ctx
        self.subject = subject
        if isinstance(subject, discord.Guild):
            start_date_naive_utc = subject.created_at
            self._generate_relevant_embed = self._generate_server_embed
        elif isinstance(subject, discord.TextChannel):
            # raise an exception if the requesting user doesn't have access to the channel
            if not subject.permissions_for(self.ctx.author).read_messages:
                raise commands.BadArgument
            start_date_naive_utc = subject.created_at
            self._generate_relevant_embed = self._generate_channel_embed
        elif isinstance(subject, discord.Member):
            start_date_naive_utc = subject.joined_at
            self._generate_relevant_embed = self._generate_member_embed
        self.start_date = start_date_naive_utc.replace(tzinfo=dt.timezone.utc).astimezone().date()
        self.seconds_in_queue = 0
        self.messages_cached = 0
        self.total_message_count = 0
        self.total_word_count = 0
        self.total_character_count = 0
        self.messages_over_hour = [0 for hour in range(24)]
        self.messages_over_weekday = [0 for weekday in range(7)]
        self.messages_over_date = defaultdict(int)
        self.active_user_stats = defaultdict(lambda: {'message_count': 0, 'word_count': 0, 'character_count': 0})
        self.relevant_channel_stats = defaultdict(
            lambda: {'message_count': 0, 'word_count': 0, 'character_count': 0}
        )
        self.embed = None
        self.activity_chart_file = None
        self.init_datetime = dt.datetime.now()
        self.out_of_queue_datetime = None
        self.initiated_queue_processing = False
        self.earliest_relevant_message_datetime = None
        self.days_of_subject_relevancy = None
        self.average_daily_message_count = None
        self.caching_progress_message = None

    @classmethod
    async def process_next_in_queue(cls, server_id: int):
        report = cls.queues[server_id][0]
        report.out_of_queue_datetime = dt.datetime.now()
        try:
            await report.analyze_subject()
        except:
            raise
        finally:
            cls.queues[server_id].popleft()
            if cls.queues[server_id]:
                somsiad.loop.create_task(cls.process_next_in_queue(server_id))
        if report.total_message_count:
            await somsiad.loop.run_in_executor(None, report.render_activity_chart)
        await report.send()

    async def enqueue(self):
        server_queue = self.queues[self.ctx.guild.id]
        self.initiated_queue_processing = not server_queue
        server_queue.append(self)
        if self.initiated_queue_processing:
            await self.process_next_in_queue(self.ctx.guild.id)

    async def send(self):
        await somsiad.send(self.ctx, embed=self.embed, file=self.activity_chart_file)

    async def analyze_subject(self) -> discord.Embed:
        """Selects the right type of analysis depending on the subject."""
        with data.session() as session:
            existent_channels = self.ctx.guild.text_channels
            existent_channel_ids = [channel.id for channel in existent_channels]
            # process subject type
            if isinstance(self.subject, discord.Guild):
                for channel in existent_channels:
                    await self._update_metadata_cache(channel, session)
                relevant_message_metadata = session.query(MessageMetadata).filter(
                    MessageMetadata.server_id == self.ctx.guild.id, MessageMetadata.channel_id.in_(existent_channel_ids)
                )
            elif isinstance(self.subject, discord.TextChannel):
                await self._update_metadata_cache(self.subject, session)
                relevant_message_metadata = session.query(MessageMetadata).filter(
                    MessageMetadata.channel_id == self.subject.id
                )
            elif isinstance(self.subject, discord.Member):
                for channel in existent_channels:
                    await self._update_metadata_cache(channel, session)
                relevant_message_metadata = session.query(MessageMetadata).filter(
                    MessageMetadata.server_id == self.ctx.guild.id, MessageMetadata.user_id == self.subject.id,
                    MessageMetadata.channel_id.in_(existent_channel_ids)
                )
            await self._finalize_progress()
            # generate statistics from metadata cache
            relevant_message_metadata = relevant_message_metadata.order_by(MessageMetadata.id.asc()).all()
            if relevant_message_metadata:
                self.earliest_relevant_message_datetime = relevant_message_metadata[0].datetime
                self.start_date = min(self.start_date, self.earliest_relevant_message_datetime.date())
                for message_metadata in relevant_message_metadata:
                    self._update_running_stats(message_metadata)
                self.days_of_subject_relevancy = (self.init_datetime.date() - self.start_date).days + 1
                self.average_daily_message_count = round(self.total_message_count / self.days_of_subject_relevancy, 1)
        self._generate_relevant_embed()
        self._embed_analysis_metastats()
        return self.embed

    def render_activity_chart(self) -> discord.File:
        """Renders a graph presenting activity of or in the subject over time."""
        if isinstance(self.subject, discord.Guild):
            title = f'Aktywność na serwerze {self.subject}'
            subject_identification = f'server-{self.subject.id}'
        elif isinstance(self.subject, discord.TextChannel):
            title = f'Aktywność na kanale #{self.subject.name}'
            subject_identification = f'server-{self.subject.guild.id}-channel-{self.subject.id}'
        elif isinstance(self.subject, discord.Member):
            title = f'Aktywność użytkownika {self.subject}'
            subject_identification = f'server-{self.subject.guild.id}-user-{self.subject.id}'

        if isinstance(self.subject, discord.TextChannel):
            # initialize the chart
            fig, [ax_by_hour, ax_by_weekday, ax_by_date] = plt.subplots(3, figsize=(12, 9))
            # plot
            ax_by_hour = self._plot_activity_by_hour(ax_by_hour)
            ax_by_weekday = self._plot_activity_by_weekday(ax_by_weekday)
            ax_by_date = self._plot_activity_by_date(ax_by_date)
        else:
            # initialize the chart
            fig, [ax_by_hour, ax_by_weekday, ax_by_date, ax_by_channel] = plt.subplots(4, figsize=(12, 12))
            # plot
            ax_by_hour = self._plot_activity_by_hour(ax_by_hour)
            ax_by_weekday = self._plot_activity_by_weekday(ax_by_weekday)
            ax_by_date = self._plot_activity_by_date(ax_by_date)
            ax_by_channel = self._plot_activity_by_channel(ax_by_channel)

        # make it look nice
        fig.set_tight_layout(True)
        ax_by_hour.set_title(title, color=self.FOREGROUND_COLOR, fontsize=13, fontweight='bold', y=1.04)

        # save as bytes
        chart_bytes = io.BytesIO()
        fig.savefig(chart_bytes, facecolor=self.BACKGROUND_COLOR, edgecolor=self.FOREGROUND_COLOR)
        plt.close(fig)
        chart_bytes.seek(0)

        # create a Discord file and embed it
        filename = f'activity-{subject_identification}-{self.init_datetime.strftime("%Y.%m.%dT%H.%M.%S")}.png'
        self.activity_chart_file = discord.File(
            fp=chart_bytes,
            filename=filename
        )
        self.embed.set_image(url=f'attachment://{filename}')

        return self.activity_chart_file

    async def _update_metadata_cache(self, channel: discord.TextChannel, session: data.RawSession):
        try:
            relevant_message_metadata = session.query(MessageMetadata).filter(
                MessageMetadata.channel_id == channel.id
            ).order_by(MessageMetadata.id.desc())
            last_cached_message_metadata = relevant_message_metadata.first()
            if last_cached_message_metadata is not None:
                after = discord.utils.snowflake_time(last_cached_message_metadata.id)
            else:
                after = None
            metadata_cache_update = []
            async for message in channel.history(limit=None, after=after):
                if message.type == discord.MessageType.default:
                    message_local_datetime = message.created_at.replace(tzinfo=dt.timezone.utc).astimezone()
                    message_metadata = MessageMetadata(
                        id=message.id, server_id=message.guild.id, channel_id=channel.id, user_id=message.author.id,
                        word_count=len(message.clean_content.split()), character_count= len(message.clean_content),
                        hour=message_local_datetime.hour, weekday=message_local_datetime.weekday(),
                        datetime=message_local_datetime
                    )
                    metadata_cache_update.append(message_metadata)
                    self.messages_cached += 1
                    if self.messages_cached % 10_000 == 0:
                        await self._send_or_update_progress()
            self.relevant_channel_stats[channel.id] = self.relevant_channel_stats.default_factory()
            metadata_cache_update.reverse()
            session.bulk_save_objects(metadata_cache_update)
            session.commit()
        except discord.Forbidden:
            pass

    def _update_running_stats(self, message: MessageMetadata):
        """Updates running message statistics."""
        self.total_message_count += 1
        self.total_word_count += message.word_count
        self.total_character_count += message.character_count
        self.messages_over_hour[message.hour] += 1
        self.messages_over_weekday[message.weekday] += 1
        self.messages_over_date[message.datetime.strftime('%Y-%m-%d')] += 1
        self.active_user_stats[message.user_id]['message_count'] += 1
        self.active_user_stats[message.user_id]['word_count'] += message.word_count
        self.active_user_stats[message.user_id]['character_count'] += message.character_count
        self.relevant_channel_stats[message.channel_id]['message_count'] += 1
        self.relevant_channel_stats[message.channel_id]['word_count'] += message.word_count
        self.relevant_channel_stats[message.channel_id]['character_count'] += message.character_count

    async def _send_or_update_progress(self):
        embed = somsiad.generate_embed(
            '⌛', f'Buforowanie nowych wiadomości, do tej pory {self.messages_cached:n}…',
            'Proces ten może trochę zająć z powodu limitów Discorda.'
        )
        if self.caching_progress_message is None:
            self.caching_progress_message = await somsiad.send(self.ctx, embed=embed)
        else:
            await self.caching_progress_message.edit(embed=embed)

    async def _finalize_progress(self):
        if self.caching_progress_message is not None:
            new_messages_form = word_number_form(
                self.messages_cached, 'nową wiadomość', 'nowe wiadomości', 'nowych wiadomości'
            )
            caching_progress_embed = somsiad.generate_embed('✅', f'Zbuforowano {new_messages_form}')
            await self.caching_progress_message.edit(embed=caching_progress_embed)

    def _generate_server_embed(self):
        """Analyzes the subject as a server."""
        self.embed = somsiad.generate_embed('✅', 'Przygotowano raport o serwerze')
        self.embed.add_field(name='Utworzono', value=human_timedelta(self.subject.created_at), inline=False)
        if self.earliest_relevant_message_datetime is not None:
            self.embed.add_field(
                name='Wysłano pierwszą wiadomość',
                value=human_timedelta(self.earliest_relevant_message_datetime, naive=False), inline=False
            )
        self.embed.add_field(name='Właściciel', value=self.subject.owner.mention)
        self.embed.add_field(name='Ról', value=f'{len(self.subject.roles):n}')
        self.embed.add_field(name='Emoji', value=f'{len(self.subject.emojis):n}')
        self.embed.add_field(name='Kanałów tekstowych', value=f'{len(self.subject.text_channels):n}')
        self.embed.add_field(name='Kanałów głosowych', value=f'{len(self.subject.voice_channels):n}')
        self.embed.add_field(name='Członków', value=f'{self.subject.member_count:n}')
        self._embed_general_message_stats()
        self._embed_top_visible_channel_stats()
        self._embed_top_active_user_stats()

    def _generate_channel_embed(self):
        """Analyzes the subject as a channel."""
        self.embed = somsiad.generate_embed('✅', f'Przygotowano raport o kanale #{self.subject}')
        self.embed.add_field(name='Utworzono', value=human_timedelta(self.subject.created_at), inline=False)
        if self.earliest_relevant_message_datetime is not None:
            self.embed.add_field(
                name='Wysłano pierwszą wiadomość',
                value=human_timedelta(self.earliest_relevant_message_datetime, naive=False), inline=False
            )
        if self.subject.category is not None:
            self.embed.add_field(name='Kategoria', value=self.subject.category.name)
        self.embed.add_field(name='Członków', value=f'{len(self.subject.members):n}')
        self._embed_general_message_stats()
        self._embed_top_active_user_stats()

    def _generate_member_embed(self):
        """Analyzes the subject as a member."""
        self.embed = somsiad.generate_embed('✅', f'Przygotowano raport o użytkowniku {self.subject}')
        self.embed.add_field(name='Utworzył konto', value=human_timedelta(self.subject.created_at), inline=False)
        self.embed.add_field(name='Ostatnio dołączył do serwera', value=human_timedelta(self.subject.joined_at), inline=False)
        if self.earliest_relevant_message_datetime is not None:
            self.embed.add_field(
                name='Wysłał pierwszą wiadomość na serwerze',
                value=human_timedelta(self.earliest_relevant_message_datetime, naive=False), inline=False
            )
        self._embed_general_message_stats()
        self._embed_top_visible_channel_stats()

    def _embed_general_message_stats(self):
        """Adds the usual message statistics to the report embed."""
        self.embed.add_field(name='Wysłanych wiadomości', value=f'{self.total_message_count:n}')
        self.embed.add_field(name='Wysłanych słów', value=f'{self.total_word_count:n}')
        self.embed.add_field(name='Wysłanych znaków', value=f'{self.total_character_count:n}')
        if self.total_message_count:
            max_daily_message_date_isoformat, max_daily_message_count = max(
                self.messages_over_date.items(), key=lambda pair: pair[1]
            )
            max_daily_message_date = dt.datetime.strptime(max_daily_message_date_isoformat, '%Y-%m-%d').date()
            self.embed.add_field(
                name='Maksymalnie wiadomości dziennie',
                value=f'{max_daily_message_count:n} ({max_daily_message_date.strftime("%-d %B %Y")})'
            )
            self.embed.add_field(name='Średnio wiadomości dziennie', value=f'{self.average_daily_message_count:n}')

    def _embed_top_visible_channel_stats(self):
        """Adds the list of top active channels to the report embed."""
        visible_channel_ids = [
            channel_id for channel_id in self.relevant_channel_stats
            if somsiad.get_channel(channel_id).permissions_for(self.ctx.author).read_messages and
            self.relevant_channel_stats[channel_id]['message_count']
        ]
        visible_channel_ids.sort(
            key=lambda channel_id: tuple(self.relevant_channel_stats[channel_id].values())
        )
        visible_channel_ids.reverse()
        top_visible_channel_stats = []
        for i, this_visible_channel_id in enumerate(visible_channel_ids[:5]):
            this_visible_channel_stats = self.relevant_channel_stats[this_visible_channel_id]
            top_visible_channel_stats.append(
                f'{i+1}. <#{this_visible_channel_id}> – '
                f'{word_number_form(this_visible_channel_stats["message_count"], "wiadomość", "wiadomości")}, '
                f'{word_number_form(this_visible_channel_stats["word_count"], "słowo", "słowa", "słów")}, '
                f'{word_number_form(this_visible_channel_stats["character_count"], "znak", "znaki", "znaków")}'
            )
        if top_visible_channel_stats:
            field_name = (
                'Najaktywniejszy na kanałach' if isinstance(self.subject, discord.Member) else 'Najaktywniejsze kanały'
            )
            self.embed.add_field(name=field_name, value='\n'.join(top_visible_channel_stats), inline=False)

    def _embed_top_active_user_stats(self):
        """Adds the list of top active users to the report embed."""
        active_user_ids = list(self.active_user_stats)
        active_user_ids.sort(
            key=lambda active_user: tuple(self.active_user_stats[active_user].values())
        )
        active_user_ids.reverse()
        top_active_user_stats = []
        for i, this_active_user_id in enumerate(active_user_ids[:5]):
            this_active_user_stats = self.active_user_stats[this_active_user_id]
            top_active_user_stats.append(
                f'{i+1}. <@{this_active_user_id}> – '
                f'{word_number_form(this_active_user_stats["message_count"], "wiadomość", "wiadomości")}, '
                f'{word_number_form(this_active_user_stats["word_count"], "słowo", "słowa", "słów")}, '
                f'{word_number_form(this_active_user_stats["character_count"], "znak", "znaki", "znaków")}'
            )
        if top_active_user_stats:
            self.embed.add_field(
                name='Najaktywniejsi użytkownicy', value='\n'.join(top_active_user_stats), inline=False
            )

    def _embed_analysis_metastats(self):
        """Adds information about analysis time as the report embed's footer."""
        completion_timedelta = dt.datetime.now() - self.init_datetime
        completion_seconds = round(completion_timedelta.total_seconds(), 1)
        new_messages_form = word_number_form(
            self.messages_cached, "nową wiadomość", "nowe wiadomości", "nowych wiadomości"
        )
        if not self.initiated_queue_processing:
            queue_timedelta = self.out_of_queue_datetime - self.init_datetime
            queue_seconds = round(queue_timedelta.total_seconds(), 1)
            footer_text = (
                f'Wygenerowano w {completion_seconds:n} s (z czego {queue_seconds:n} s w serwerowej kolejce analizy) '
                f'buforując {new_messages_form}'
            )
        else:
            footer_text = (
                f'Wygenerowano w {completion_seconds:n} s buforując {new_messages_form}'
            )
        self.embed.set_footer(text=footer_text)

    def _plot_activity_by_hour(self, ax):
        # plot the chart
        ax.bar(
            [f'{hour}:00'.zfill(5) for hour in list(range(6, 24)) + list(range(0, 6))],
            self.messages_over_hour[6:] + self.messages_over_hour[:6],
            color=self.BACKGROUND_COLOR,
            facecolor=self.FOREGROUND_COLOR,
            width=1,
            align='edge'
        )

        # set proper X axis formatting
        ax.set_xlim(0, 24)
        ax.set_xticklabels(
            [f'{hour}:00'.zfill(5) for hour in list(range(6, 24)) + list(range(0, 6))], rotation=30, ha='right'
        )

        # set proper ticker intervals on the Y axis accounting for the maximum number of messages
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins='auto', steps=[10], integer=True))
        if max(self.messages_over_hour) >= 10:
            ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(n=10))

        # make it look nice
        ax.set_facecolor(self.BACKGROUND_COLOR)
        ax.set_xlabel('Godzina', color=self.FOREGROUND_COLOR, fontsize=11, fontweight='bold')

        return ax

    def _plot_activity_by_weekday(self, ax):
        # plot the chart
        ax.bar(
            calendar.day_abbr,
            self.messages_over_weekday,
            color=self.BACKGROUND_COLOR,
            facecolor=self.FOREGROUND_COLOR,
            width=1
        )

        # set proper X axis formatting
        ax.set_xlim(-0.5, 6.5)
        ax.set_xticklabels(calendar.day_abbr, rotation=30, ha='right')

        # set proper ticker intervals on the Y axis accounting for the maximum number of messages
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins='auto', steps=[10], integer=True))
        if max(self.messages_over_weekday) >= 10:
            ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(n=10))

        # make it look nice
        ax.set_facecolor(self.BACKGROUND_COLOR)
        ax.set_xlabel('Dzień tygodnia', color=self.FOREGROUND_COLOR, fontsize=11, fontweight='bold')
        ax.set_ylabel('Wysłanych wiadomości', color=self.FOREGROUND_COLOR, fontsize=11, fontweight='bold')

        return ax

    def _plot_activity_by_date(self, ax):
        # calculate timeframe
        start_date = self.start_date
        end_date = self.init_datetime.date()
        day_difference = self.days_of_subject_relevancy - 1
        year_difference = end_date.year - start_date.year
        month_difference = 12 * year_difference + end_date.month - start_date.month

        # convert date strings provided to datetime objects
        dates = [start_date + dt.timedelta(n) for n in range(self.days_of_subject_relevancy)]
        messages = [self.messages_over_date[date.isoformat()] for date in dates]
        is_rolling_average = day_difference > 21
        if is_rolling_average:
            messages = rolling_average(messages, self.ROLL)

        # plot the chart
        ax.bar(
            dates,
            messages,
            color=self.BACKGROUND_COLOR,
            facecolor=self.FOREGROUND_COLOR,
            width=1
        )

        # set proper ticker intervals on the X axis accounting for the timeframe
        year_locator = mdates.YearLocator()
        month_locator = mdates.MonthLocator()
        quarter_locator = mdates.MonthLocator(bymonth=[1,4,7,10])
        week_locator = mdates.WeekdayLocator(byweekday=mdates.MO)
        day_locator = mdates.DayLocator()

        year_formatter = mdates.DateFormatter('%Y')
        month_formatter = mdates.DateFormatter('%b %Y')
        day_formatter = mdates.DateFormatter('%-d %b %Y')

        if month_difference > 48:
            ax.xaxis.set_major_locator(year_locator)
            ax.xaxis.set_major_formatter(year_formatter)
            ax.xaxis.set_minor_locator(quarter_locator)
        elif month_difference > 24:
            ax.xaxis.set_major_locator(quarter_locator)
            ax.xaxis.set_major_formatter(month_formatter)
            ax.xaxis.set_minor_locator(month_locator)
        elif day_difference > 70:
            ax.xaxis.set_major_locator(month_locator)
            ax.xaxis.set_major_formatter(month_formatter)
        elif day_difference > 21:
            ax.xaxis.set_major_locator(week_locator)
            ax.xaxis.set_major_formatter(day_formatter)
            ax.xaxis.set_minor_locator(day_locator)
        else:
            ax.xaxis.set_major_locator(day_locator)
            ax.xaxis.set_major_formatter(day_formatter)

        # set proper X axis formatting
        half_day = dt.timedelta(hours=12)
        ax.set_xlim(
            dt.datetime(start_date.year, start_date.month, start_date.day) - half_day,
            dt.datetime(end_date.year, end_date.month, end_date.day) + half_day
        )
        for tick in ax.get_xticklabels():
            tick.set_rotation(30)
            tick.set_horizontalalignment('right')

        # set proper ticker intervals on the Y axis accounting for the maximum number of messages
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins='auto', steps=[10]))
        if max(messages) >= 10:
            ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(n=10))

        # make it look nice
        ax.set_facecolor(self.BACKGROUND_COLOR)
        ax.set_xlabel(
            'Data (tygodniowa średnia ruchoma)' if is_rolling_average else 'Data',
            color=self.FOREGROUND_COLOR, fontsize=11, fontweight='bold'
        )

        return ax

    def _plot_activity_by_channel(self, ax):
        # plot the chart
        channel_names = [f'#{somsiad.get_channel(channel)}' for channel in self.relevant_channel_stats]
        message_counts = [channel_stats['message_count'] for channel_stats in self.relevant_channel_stats.values()]
        ax.bar(
            channel_names,
            message_counts,
            color=self.BACKGROUND_COLOR,
            facecolor=self.FOREGROUND_COLOR,
            width=1
        )

        # set proper X axis formatting
        ax.set_xlim(-0.5, len(channel_names)-0.5)
        ax.set_xticklabels(channel_names, rotation=30, ha='right')

        # set proper ticker intervals on the Y axis accounting for the maximum number of messages
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins='auto', steps=[10], integer=True))
        if max(message_counts) >= 10:
            ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(n=10))

        # make it look nice
        ax.set_facecolor(self.BACKGROUND_COLOR)
        ax.set_xlabel('Kanał', color=self.FOREGROUND_COLOR, fontsize=11, fontweight='bold')
        ax.set_ylabel('Wysłanych wiadomości', color=self.FOREGROUND_COLOR, fontsize=11, fontweight='bold')

        return ax


class Statistics(commands.Cog):
    GROUP = Help.Command('stat', (), 'Grupa komend związanych ze statystykami na serwerze.')
    COMMANDS = (
        Help.Command('serwer', (), 'Wysyła raport o serwerze.'),
        Help.Command(('kanał', 'kanal'), '?kanał', 'Wysyła raport o kanale. Jeśli nie podano kanału, przyjmuje kanał na którym użyto komendy.'),
        Help.Command(
            ('użytkownik', 'uzytkownik', 'user'), '?użytkownik',
            'Wysyła raport o użytkowniku. Jeśli nie podano użytkownika, przyjmuje użytkownika, który użył komendy.'
        )
    )
    HELP = Help(COMMANDS, group=GROUP)

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, case_insensitive=True)
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def stat(self, ctx, *, subject: Union[discord.Member, discord.TextChannel] = None):
        if subject is None:
            await self.bot.send(ctx, embeds=self.HELP.embeds)
        else:
            async with ctx.typing():
                report = Report(ctx, subject)
                await report.enqueue()

    @stat.error
    async def stat_error(self, ctx, error):
        if isinstance(error, commands.BadUnionArgument):
            await self.bot.send(
                ctx, embed=somsiad.generate_embed('⚠️', 'Nie znaleziono na serwerze pasującego użytkownika ani kanału')
            )

    @stat.command(aliases=['server', 'serwer'])
    @commands.cooldown(
        1, Report.COOLDOWN, commands.BucketType.channel
    )
    @commands.guild_only()
    async def stat_server(self, ctx):
        async with ctx.typing():
            report = Report(ctx, ctx.guild)
            await report.enqueue()

    @stat.command(aliases=['channel', 'kanał', 'kanal'])
    @commands.cooldown(
        1, Report.COOLDOWN, commands.BucketType.user
    )
    @commands.guild_only()
    async def stat_channel(self, ctx, *, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        async with ctx.typing():
            report = Report(ctx, channel)
            await report.enqueue()

    @stat_channel.error
    async def stat_channel_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await self.bot.send(
                ctx, embed=somsiad.generate_embed('⚠️', 'Nie znaleziono na serwerze pasującego kanału')
            )

    @stat.command(aliases=['user', 'member', 'użytkownik', 'członek'])
    @commands.cooldown(
        1, Report.COOLDOWN, commands.BucketType.user
    )
    @commands.guild_only()
    async def stat_member(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        async with ctx.typing():
            report = Report(ctx, member)
            await report.enqueue()

    @stat_member.error
    async def stat_member_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await self.bot.send(
                ctx, embed=somsiad.generate_embed('⚠️', 'Nie znaleziono na serwerze pasującego użytkownika')
            )


somsiad.add_cog(Statistics(somsiad))
