# Copyright 2018-2021 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import asyncio
import calendar
import dataclasses
import datetime as dt
import aiohttp
import enum
import functools
import io
import data
from collections import defaultdict, deque
from typing import (
    Any,
    DefaultDict,
    Deque,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

import discord
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from aiochclient.records import Record
from discord.ext import commands

from configuration import configuration
from core import DataProcessingOptOut, Help, cooldown
from somsiad import Somsiad, SomsiadMixin
from utilities import human_datetime, md_link, rolling_average, utc_to_naive_local, word_number_form


@dataclasses.dataclass
class MessageMetadata:
    id: int
    server_id: int
    channel_id: int
    user_id: int
    word_count: int
    character_count: int
    created_at: dt.datetime


@dataclasses.dataclass
class MaterializedMessageMetadata(MessageMetadata):
    hour: int
    weekday: int
    date: str


class MetadataCache(SomsiadMixin):
    async def prepare(self):
        await self.bot.ch_client.execute(
            '''
            CREATE TABLE IF NOT EXISTS message_metadata_cache (
                id UInt64 Codec(DoubleDelta, LZ4),
                server_id UInt64 Codec(T64, LZ4),
                channel_id UInt64 Codec(T64, LZ4),
                user_id UInt64 Codec(T64, LZ4),
                word_count UInt16 Codec(T64, LZ4),
                character_count UInt16 Codec(T64, LZ4),
                created_at DateTime64(3) Codec(DoubleDelta, LZ4),
                hour UInt8 MATERIALIZED toHour(created_at),
                weekday UInt8 MATERIALIZED toDayOfWeek(created_at) - 1,
                date FixedString(10) MATERIALIZED formatDateTime(created_at, '%F'),
                INDEX server_channel (server_id, channel_id) TYPE set(200) GRANULARITY 3,
                INDEX server_member (server_id, user_id) TYPE set(200) GRANULARITY 3
            ) ENGINE = ReplacingMergeTree
            ORDER BY (id,)
            PARTITION BY (server_id,)
        '''
        )

    async def insert(self, metadata_batch: Sequence[MessageMetadata]):
        try:
            await self.bot.ch_client.execute(
                "INSERT INTO message_metadata_cache VALUES",
                *map(dataclasses.astuple, metadata_batch),
            )
        except (aiohttp.ClientOSError, aiohttp.ServerDisconnectedError):
            # Retry once
            await self.bot.ch_client.execute(
                "INSERT INTO message_metadata_cache VALUES",
                *map(dataclasses.astuple, metadata_batch),
            )

    async def fetch_edge_message(
        self,
        *,
        server_id: int,
        channel_id: Optional[int] = None,
        user_id: Optional[int] = None,
        after: Optional[dt.datetime] = None,
        latest: bool,
    ) -> Optional[MessageMetadata]:
        constraints, params = self._build_constraints_and_params(
            server_id=server_id, channel_id=channel_id, user_id=user_id, after=after
        )
        order_part = f'id {"DESC" if latest else "ASC"}'
        where_part = self._build_where(constraints, params)
        row = await self.bot.ch_client.fetchrow(
            f'''
            SELECT * FROM message_metadata_cache
            WHERE {where_part}
            ORDER BY {order_part}
            LIMIT 1
        ''',
            params=params,
        )
        return None if row is None else MessageMetadata(**row)

    async def fetch_activity_by_hour(
        self,
        *,
        server_id: int,
        channel_id: Optional[int] = None,
        user_id: Optional[int] = None,
        after: Optional[dt.datetime] = None,
    ) -> List[Record]:
        constraints, params = self._build_constraints_and_params(
            server_id=server_id, channel_id=channel_id, user_id=user_id, after=after
        )
        where_part = self._build_where(constraints, params)
        rows = await self.bot.ch_client.fetch(
            f'''
            SELECT COUNT(*) AS message_count, hour
            FROM message_metadata_cache
            WHERE {where_part}
            GROUP BY hour
            ORDER BY hour
        ''',
            params=params,
        )
        return rows

    async def fetch_activity_by_weekday(
        self,
        *,
        server_id: int,
        channel_id: Optional[int] = None,
        user_id: Optional[int] = None,
        after: Optional[dt.datetime] = None,
    ) -> List[Record]:
        constraints, params = self._build_constraints_and_params(
            server_id=server_id, channel_id=channel_id, user_id=user_id, after=after
        )
        where_part = self._build_where(constraints, params)
        rows = await self.bot.ch_client.fetch(
            f'''
            SELECT COUNT(*) AS message_count, weekday
            FROM message_metadata_cache
            WHERE {where_part}
            GROUP BY weekday
            ORDER BY weekday
        ''',
            params=params,
        )
        return rows

    async def fetch_activity_by_date(
        self,
        *,
        server_id: int,
        channel_id: Optional[int] = None,
        user_id: Optional[int] = None,
        after: Optional[dt.datetime] = None,
    ) -> List[Record]:
        constraints, params = self._build_constraints_and_params(
            server_id=server_id, channel_id=channel_id, user_id=user_id, after=after
        )
        where_part = self._build_where(constraints, params)
        rows = await self.bot.ch_client.fetch(
            f'''
            SELECT COUNT(*) AS message_count, date
            FROM message_metadata_cache
            WHERE {where_part}
            GROUP BY date
            ORDER BY date
        ''',
            params=params,
        )
        return rows

    async def fetch_total_counts(
        self,
        *,
        server_id: int,
        channel_id: Optional[int] = None,
        user_id: Optional[int] = None,
        after: Optional[dt.datetime] = None,
    ) -> Record:
        constraints, params = self._build_constraints_and_params(
            server_id=server_id, channel_id=channel_id, user_id=user_id, after=after
        )
        where_part = self._build_where(constraints, params)
        row = await self.bot.ch_client.fetchrow(
            f'''
            SELECT
                COUNT(*) AS total_message_count,
                SUM(word_count) AS total_word_count,
                SUM(character_count) AS total_character_count
            FROM message_metadata_cache
            WHERE {where_part}
        ''',
            params=params,
        )
        return row

    async def fetch_users_ranking(
        self,
        *,
        server_id: int,
        channel_id: Optional[int] = None,
        user_id: Optional[int] = None,
        after: Optional[dt.datetime] = None,
    ) -> List[Record]:
        constraints, params = self._build_constraints_and_params(
            server_id=server_id, channel_id=channel_id, user_id=user_id, after=after
        )
        where_part = self._build_where(constraints, params)
        rows = await self.bot.ch_client.fetch(
            f'''
            SELECT
                COUNT(*) AS message_count,
                SUM(word_count) AS word_count,
                SUM(character_count) AS character_count,
                user_id
            FROM message_metadata_cache
            WHERE {where_part}
            GROUP BY user_id
            ORDER BY message_count DESC
        ''',
            params=params,
        )
        return rows

    async def fetch_channels_ranking(
        self,
        *,
        server_id: int,
        channel_id: Optional[int] = None,
        user_id: Optional[int] = None,
        after: Optional[dt.datetime] = None,
    ) -> List[Record]:
        constraints, params = self._build_constraints_and_params(
            server_id=server_id, channel_id=channel_id, user_id=user_id, after=after
        )
        where_part = self._build_where(constraints, params)
        rows = await self.bot.ch_client.fetch(
            f'''
            SELECT
                COUNT(*) AS message_count,
                SUM(word_count) AS word_count,
                SUM(character_count) AS character_count,
                channel_id
            FROM message_metadata_cache
            WHERE {where_part}
            GROUP BY channel_id
            ORDER BY message_count DESC
        ''',
            params=params,
        )
        return rows

    @staticmethod
    def _build_constraints_and_params(
        *,
        server_id: int,
        channel_id: Optional[Union[int, Sequence[int]]] = None,
        user_id: Optional[Union[int, Sequence[int]]] = None,
        after: Optional[dt.datetime] = None,
    ) -> Tuple[Dict[str, str], Dict[str, Any]]:
        constraints: Dict[str, str] = {"server_id": "="}
        params: Dict[str, Any] = {"server_id": server_id}
        if channel_id is not None:
            constraints["channel_id"] = "=" if isinstance(channel_id, int) else "IN"
            params["channel_id"] = channel_id
        if user_id is not None:
            constraints["user_id"] = "=" if isinstance(user_id, int) else "IN"
            params["user_id"] = user_id
        if after is not None:
            constraints["created_at"] = ">"
            params["created_at"] = after
        return constraints, params

    @staticmethod
    def _build_where(constraints: Dict[str, str], params: Dict[str, Any]) -> str:
        return ' AND '.join((f'{column} {operator} {{{column}}}' for column, operator in constraints.items()))


class Report:
    """A statistics report. Can generate server, channel, category or member statistics."""

    COOLDOWN = max(float(configuration['command_cooldown_per_user_in_seconds']), 15.0)
    BACKGROUND_COLOR = '#2b2d31'
    FOREGROUND_COLOR = '#ffffff'
    ROLL = 7
    CACHE_INSERT_BATCH_SIZE = 1000

    queues: DefaultDict[int, Deque["Report"]] = defaultdict(deque)

    metadata_cache: MetadataCache
    ctx: commands.Context
    bot: Somsiad
    user_by_id: bool
    subject: Optional[
        Union[discord.Guild, discord.TextChannel, discord.CategoryChannel, discord.Member, discord.User, discord.Role]
    ]
    subject_id: int
    seconds_in_queue: float
    messages_cached: int
    total_message_count: int
    total_word_count: int
    total_character_count: int
    messages_over_hour: List[int]
    messages_over_weekday: List[int]
    messages_over_date: DefaultDict[str, int]
    active_user_stats: DefaultDict[int, Dict[str, int]]
    relevant_channel_stats: DefaultDict[int, Dict[str, int]]
    embed: Optional[discord.Embed]
    activity_chart_file: Optional[discord.File]
    init_datetime: dt.datetime
    out_of_queue_datetime: Optional[dt.datetime]
    initiated_queue_processing: bool
    earliest_relevant_message: Optional[MessageMetadata]
    latest_relevant_message: Optional[MessageMetadata]
    subject_relevancy_length: Optional[int]
    average_daily_message_count: Optional[float]
    caching_progress_message: Optional[discord.Message]
    last_days: Optional[int]
    days_presentation: Optional[str]
    description: Optional[str]
    timeframe_start_date: Optional[dt.date]
    timeframe_end_date: dt.date

    plt.style.use('dark_background')

    class Type(enum.Enum):
        SERVER = enum.auto()
        CHANNEL = enum.auto()
        CATEGORY = enum.auto()
        MEMBER = enum.auto()
        USER = enum.auto()
        DELETED_USER = enum.auto()
        ROLE = enum.auto()

    def __init__(
        self,
        ctx: commands.Context,
        subject: Union[
            discord.Guild, discord.TextChannel, discord.CategoryChannel, discord.Member, discord.User, discord.Role, int
        ],
        *,
        metadata_cache: MetadataCache,
        last_days: Optional[int] = None,
    ):
        self.metadata_cache = metadata_cache
        self.ctx = ctx
        self.bot = cast(Somsiad, ctx.bot)
        if isinstance(subject, int):
            self.user_by_id = True
            self.subject = None
            self.subject_id = subject
        else:
            self.user_by_id = False
            self.subject = subject
            self.subject_id = subject.id
        self.seconds_in_queue = 0
        self.messages_cached = 0
        self.total_message_count = 0
        self.total_word_count = 0
        self.total_character_count = 0
        self.messages_over_hour = [0 for hour in range(24)]
        self.messages_over_weekday = [0 for weekday in range(7)]
        self.messages_over_date = defaultdict(int)
        self.active_user_stats = defaultdict(lambda: {'message_count': 0, 'word_count': 0, 'character_count': 0})
        self.relevant_channel_stats = defaultdict(lambda: {'message_count': 0, 'word_count': 0, 'character_count': 0})
        self.embed = None
        self.activity_chart_file = None
        self.init_datetime = dt.datetime.now()
        self.out_of_queue_datetime = None
        self.initiated_queue_processing = False
        self.earliest_relevant_message = None
        self.latest_relevant_message = None
        self.subject_relevancy_length = None
        self.average_daily_message_count = None
        self.caching_progress_message = None
        self.last_days = last_days
        if last_days:
            if last_days < 1:
                raise ValueError('last_days must be a 1 or larger')
            elif last_days == 1:
                self.days_presentation = 'z dzisiaj'
            else:
                self.days_presentation = f'z ostatnich {last_days} dni (licząc dzisiejszy)'
            self.description = f'Wzięto pod uwagę aktywność {self.days_presentation}.'
        else:
            self.days_presentation = None
            self.description = None
        self.timeframe_start_date = None
        self.timeframe_end_date = self.init_datetime.date()

    async def process_next_in_queue(self, server_id: int):
        report = self.queues[server_id][0]
        report.out_of_queue_datetime = dt.datetime.now()
        try:
            await report.analyze_subject()
        except:
            raise
        finally:
            self.queues[server_id].popleft()
            if self.queues[server_id]:
                self.bot.loop.create_task(self.process_next_in_queue(server_id))
        if report.total_message_count:
            await report.render_activity_chart()
        await report.send()

    async def enqueue(self):
        server_queue = self.queues[self.ctx.guild.id]
        self.initiated_queue_processing = not server_queue
        server_queue.append(self)
        if self.initiated_queue_processing:
            await self.process_next_in_queue(self.ctx.guild.id)
        else:
            embed = self.bot.generate_embed(
                '⏳', 'Zakolejkowano raport…', f'{len(server_queue)}. w serwerowej kolejce analizy.'
            )
            await self.bot.send(self.ctx, embed=embed)

    async def send(self):
        await self.bot.send(self.ctx, embed=self.embed, file=self.activity_chart_file)

    async def analyze_subject(self) -> discord.Embed:
        """Selects the right type of analysis depending on the subject."""
        await self._fill_in_details()
        existent_channels = [
            channel
            for channel in cast(discord.Guild, self.ctx.guild).text_channels
            if channel.permissions_for(cast(discord.Member, self.ctx.me)).read_messages
        ]
        constraints: Dict[str, Any] = {"server_id": self.ctx.guild.id}
        # process subject type
        if self.type == self.Type.SERVER:
            constraints["channel_id"] = [channel.id for channel in existent_channels]
        elif self.type == self.Type.CHANNEL:
            self.subject = cast(discord.TextChannel, self.subject)
            existent_channels = [self.subject]
            constraints["channel_id"] = self.subject_id
        elif self.type == self.Type.CATEGORY:
            existent_channels = [
                cast(discord.TextChannel, channel)
                for channel in cast(discord.CategoryChannel, self.subject).channels
                if channel in existent_channels
            ]
            constraints["channel_id"] = [channel.id for channel in existent_channels]
        elif self.type in (self.Type.MEMBER, self.Type.USER, self.Type.DELETED_USER):
            constraints["channel_id"] = [channel.id for channel in existent_channels]
            constraints["user_id"] = self.subject_id
        elif self.type == self.Type.ROLE:
            constraints["user_id"] = [member.id for member in cast(discord.Role, self.subject).members]
        else:
            raise Exception(f'invalid analysis type {self.type}!')
        for channel in existent_channels:
            await self._update_metadata_cache(channel)
        if self.last_days:
            constraints["after"] = dt.datetime(
                self.init_datetime.year, self.init_datetime.month, self.init_datetime.day
            ) - dt.timedelta(self.last_days - 1)
        await self._finalize_progress()
        (
            self.earliest_relevant_message,
            self.latest_relevant_message,
            total_counts,
            activity_by_date,
            activity_by_weekday,
            activity_by_hour,
            users_ranking,
            channels_ranking,
        ) = await asyncio.gather(
            self.metadata_cache.fetch_edge_message(**constraints, latest=False),
            self.metadata_cache.fetch_edge_message(**constraints, latest=True),
            self.metadata_cache.fetch_total_counts(**constraints),
            self.metadata_cache.fetch_activity_by_date(**constraints),
            self.metadata_cache.fetch_activity_by_weekday(**constraints),
            self.metadata_cache.fetch_activity_by_hour(**constraints),
            self.metadata_cache.fetch_users_ranking(**constraints),
            self.metadata_cache.fetch_channels_ranking(**constraints),
        )
        self.total_message_count, self.total_word_count, self.total_character_count = total_counts.values()
        for row in activity_by_date:
            self.messages_over_date[row["date"]] = row["message_count"]
        for row in activity_by_weekday:
            self.messages_over_weekday[row["weekday"]] = row["message_count"]
        for row in activity_by_hour:
            self.messages_over_hour[row["hour"]] = row["message_count"]
        for row in users_ranking:
            self.active_user_stats[row["user_id"]] = row
        for row in channels_ranking:
            self.relevant_channel_stats[row["channel_id"]] = row
        was_user_found = True
        if self.total_message_count > 0:
            if constraints.get("after") is not None:
                self.timeframe_start_date = cast(dt.datetime, constraints["after"]).date()
            else:
                if self.timeframe_start_date is not None:
                    self.timeframe_start_date = min(
                        self.timeframe_start_date, self.earliest_relevant_message.created_at.date()
                    )
                else:
                    self.timeframe_start_date = self.earliest_relevant_message.created_at.date()
            self.subject_relevancy_length = (self.init_datetime.date() - self.timeframe_start_date).days + 1
            self.average_daily_message_count = round(self.total_message_count / self.subject_relevancy_length, 1)
        elif self.type == self.Type.DELETED_USER:
            was_user_found = False
        if was_user_found:
            self._generate_relevant_embed()
        else:
            self.embed = self.bot.generate_embed('⚠️', 'Nie znaleziono na serwerze pasującego użytkownika')
        return cast(discord.Embed, self.embed)

    async def render_activity_chart(self, *, set_embed_image: bool = True) -> discord.File:
        """Renders a graph presenting activity of or in the subject over time."""
        show_by_weekday_and_date = self.subject_relevancy_length is not None and self.subject_relevancy_length > 1
        show_by_channels = True
        title = 'Aktywność'
        if self.type == self.Type.CHANNEL:
            title += f' na kanale #{self.subject.name}'
            subject_identification = f'server-{self.ctx.guild.id}-channel-{self.subject_id}'
            show_by_channels = False
        else:
            if self.type == self.Type.SERVER:
                title += f' na serwerze {self.subject}'
                subject_identification = f'server-{self.subject_id}'
            if self.type == self.Type.ROLE:
                title += f' użytkowników z rolą {self.subject} na serwerze {self.subject.guild}'
                subject_identification = f'server-{cast(discord.Role, self.subject).guild.id}-role-{self.subject_id}'
            elif self.type == self.Type.CATEGORY:
                title += f' w kategorii {self.subject}'
                subject_identification = f'server-{self.ctx.guild.id}-category-{self.subject_id}'
            else:
                subject_identification = f'server-{self.ctx.guild.id}-user-{self.subject_id}'
                if self.type in (self.Type.MEMBER, self.Type.USER):
                    title += f' użytkownika {self.subject}'
                elif self.type == self.Type.DELETED_USER:
                    title += f' usuniętego użytkownika ID {self.subject_id}'
        if self.days_presentation:
            title += f' {self.days_presentation}'

        # initialize the chart
        subplots = 1 + 2 * show_by_weekday_and_date + show_by_channels
        fig, ax_or_axes = plt.subplots(subplots, figsize=(12, subplots * 3))

        # plot
        ax_by_hour = self._plot_activity_by_hour(ax_or_axes[0] if subplots > 1 else ax_or_axes)
        if show_by_weekday_and_date:
            self._plot_activity_by_weekday(ax_or_axes[1])
            self._plot_activity_by_date(ax_or_axes[2])
        if show_by_channels:
            self._plot_activity_by_channel(ax_or_axes[3 if show_by_weekday_and_date else 1])

        # make it look nice
        fig.set_tight_layout(True)
        ax_by_hour.set_title(title, color=self.FOREGROUND_COLOR, fontsize=13, fontweight='bold', y=1.04)

        # save as bytes
        chart_bytes = io.BytesIO()
        await self.bot.loop.run_in_executor(
            None,
            functools.partial(
                fig.savefig, chart_bytes, facecolor=self.BACKGROUND_COLOR, edgecolor=self.FOREGROUND_COLOR
            ),
        )

        plt.close(fig)
        chart_bytes.seek(0)

        # create a Discord file and embed it
        filename = f'activity-{subject_identification}-{self.init_datetime.strftime("%Y.%m.%dT%H.%M.%S")}.png'
        self.activity_chart_file = discord.File(fp=chart_bytes, filename=filename)
        if set_embed_image:
            if self.embed is None:
                raise Exception(
                    'There is no report embed to save the chart to! First generate an embed with method analyze_subject() or pass set_embed_image=False to this method.'
                )
            self.embed.set_image(url=f'attachment://{filename}')

        return self.activity_chart_file

    def _generate_relevant_embed(self, *args, **kwargs):
        if self.type == self.Type.DELETED_USER:
            self._generate_deleted_user_embed(*args, **kwargs)
        elif self.type == self.Type.USER:
            self._generate_user_embed(*args, **kwargs)
        elif self.type == self.Type.SERVER:
            self._generate_server_embed(*args, **kwargs)
        elif self.type == self.Type.CHANNEL:
            self._generate_channel_embed(*args, **kwargs)
        elif self.type == self.Type.CATEGORY:
            self._generate_category_embed(*args, **kwargs)
        elif self.type == self.Type.MEMBER:
            self._generate_member_embed(*args, **kwargs)
        elif self.type == self.Type.ROLE:
            self._generate_role_embed(*args, **kwargs)
        self._embed_analysis_metastats()

    async def _fill_in_details(self):
        timeframe_start_date_utc = None
        if self.user_by_id:
            try:
                self.subject = await self.bot.fetch_user(self.subject_id)
            except discord.NotFound:
                self.type = self.Type.DELETED_USER
            else:
                self.type = self.Type.USER
        elif isinstance(self.subject, discord.Guild):
            self.type = self.Type.SERVER
            timeframe_start_date_utc = self.subject.created_at
        elif isinstance(self.subject, discord.TextChannel):
            self.type = self.Type.CHANNEL
            # raise an exception if the requesting user doesn't have access to the channel
            if not self.subject.permissions_for(cast(discord.Member, self.ctx.author)).read_messages:
                raise commands.BadArgument
            timeframe_start_date_utc = self.subject.created_at
        elif isinstance(self.subject, discord.CategoryChannel):
            self.type = self.Type.CATEGORY
            # raise an exception if the requesting user doesn't have access to the channel
            if not self.subject.permissions_for(cast(discord.Member, self.ctx.author)).read_messages:
                raise commands.BadArgument
            timeframe_start_date_utc = self.subject.created_at
        elif isinstance(self.subject, discord.Member):
            self.type = self.Type.MEMBER
            timeframe_start_date_utc = self.subject.joined_at
        elif isinstance(self.subject, discord.User):
            self.type = self.Type.USER
        elif isinstance(self.subject, discord.Role):
            self.type = self.Type.ROLE
        if timeframe_start_date_utc is not None:
            self.timeframe_start_date = utc_to_naive_local(timeframe_start_date_utc).date()

    async def _update_metadata_cache(self, channel: discord.TextChannel):
        try:
            self.relevant_channel_stats[channel.id] = self.relevant_channel_stats.default_factory()  # type: ignore
            metadata_cache_update = []
            latest_cached_message = await self.metadata_cache.fetch_edge_message(
                server_id=channel.guild.id, channel_id=channel.id, latest=True
            )
            after: Optional[dt.datetime] = (
                latest_cached_message.created_at if latest_cached_message is not None else None
            )
            with data.session() as session:
                users_opted_out_of_data_processing_ids: List[int] = [r.user_id for r in session.query(DataProcessingOptOut).all()]
            while True:
                try:
                    async for message in channel.history(limit=None, after=after):
                        if message.author.id in users_opted_out_of_data_processing_ids:
                            continue  # User opted out of data processing
                        if message.type != discord.MessageType.default:
                            continue
                        message_datetime = utc_to_naive_local(message.created_at)
                        content_parts: List[Union[str, discord.embeds._EmptyEmbed]] = [message.clean_content]
                        for embed in message.embeds:
                            content_parts.append(embed.title)
                            content_parts.append(embed.description)
                            for field in embed.fields:
                                content_parts.append(field.name)
                                content_parts.append(field.value)
                            if embed.footer:
                                content_parts.append(embed.footer.text)
                            if embed.author:
                                content_parts.append(embed.author.name)
                        content = ' '.join(cast(List[str], filter(None, content_parts)))
                        message_metadata = MessageMetadata(
                            id=message.id,
                            server_id=message.guild.id,
                            channel_id=channel.id,
                            user_id=message.author.id,
                            word_count=len(tuple(filter(None, content.split()))),
                            character_count=len(content),
                            created_at=message_datetime,
                        )
                        metadata_cache_update.append(message_metadata)
                        after = message_metadata.created_at
                        self.messages_cached += 1
                        if self.messages_cached % 10_000 == 0:
                            await self._send_or_update_progress()
                        if len(metadata_cache_update) >= self.CACHE_INSERT_BATCH_SIZE:
                            await self.metadata_cache.insert(metadata_cache_update)
                            metadata_cache_update = []
                except discord.HTTPException:
                    continue
                else:
                    break
            await self.metadata_cache.insert(metadata_cache_update)
        except discord.Forbidden:
            pass

    async def _send_or_update_progress(self):
        embed = self.bot.generate_embed(
            '⌛',
            f'Buforowanie metadanych nowych wiadomości, do tej pory {self.messages_cached:n}…',
            'Proces ten może trochę zająć z powodu limitów Discorda.',
        )
        if self.caching_progress_message is None:
            self.caching_progress_message = await self.bot.send(self.ctx, embed=embed)
        else:
            self.caching_progress_message = await self.caching_progress_message.edit(embed=embed)

    async def _finalize_progress(self):
        if self.caching_progress_message is not None:
            new_messages_form = word_number_form(
                self.messages_cached, 'nową wiadomość', 'nowe wiadomości', 'nowych wiadomości'
            )
            caching_progress_embed = self.bot.generate_embed('✅', f'Zbuforowano {new_messages_form}')
            self.caching_progress_message = await self.caching_progress_message.edit(embed=caching_progress_embed)

    def _generate_server_embed(self):
        """Analyzes the subject as a server."""
        self.embed = self.bot.generate_embed('📈', 'Przygotowano raport o serwerze', self.description)
        self.embed.add_field(name='Utworzono', value=human_datetime(self.subject.created_at, utc=True), inline=False)
        if self.total_message_count:
            earliest = self.earliest_relevant_message
            self.embed.add_field(
                name=f'Wysłano pierwszą wiadomość {"w przedziale czasowym" if self.last_days else ""}',
                value=md_link(
                    human_datetime(earliest.created_at),
                    f'https://discordapp.com/channels/{earliest.server_id}/{earliest.channel_id}/{earliest.id}',
                ),
                inline=False,
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
        self.embed = self.bot.generate_embed('📈', f'Przygotowano raport o kanale #{self.subject}', self.description)
        self.embed.add_field(name='Utworzono', value=human_datetime(self.subject.created_at, utc=True), inline=False)
        if self.total_message_count:
            earliest = self.earliest_relevant_message
            self.embed.add_field(
                name=f'Wysłano pierwszą wiadomość {"w przedziale czasowym" if self.last_days else ""}',
                value=md_link(
                    human_datetime(earliest.created_at),
                    f'https://discordapp.com/channels/{earliest.server_id}/{earliest.channel_id}/{earliest.id}',
                ),
                inline=False,
            )
        if self.subject.category is not None:
            self.embed.add_field(name='Kategoria', value=self.subject.category.name)
        self.embed.add_field(name='Członków', value=f'{len(self.subject.members):n}')
        self._embed_general_message_stats()
        self._embed_top_active_user_stats()

    def _generate_category_embed(self):
        """Analyzes the subject as a category."""
        self.embed = self.bot.generate_embed('📈', f'Przygotowano raport o kategorii {self.subject}', self.description)
        self.embed.add_field(name='Utworzono', value=human_datetime(self.subject.created_at, utc=True), inline=False)
        if self.total_message_count:
            earliest = self.earliest_relevant_message
            self.embed.add_field(
                name=f'Wysłano pierwszą wiadomość {"w przedziale czasowym" if self.last_days else ""}',
                value=md_link(
                    human_datetime(earliest.created_at),
                    f'https://discordapp.com/channels/{earliest.server_id}/{earliest.channel_id}/{earliest.id}',
                ),
                inline=False,
            )
        self.embed.add_field(name='Kanałów tekstowych', value=f'{len(self.subject.text_channels):n}')
        self.embed.add_field(name='Kanałów głosowych', value=f'{len(self.subject.voice_channels):n}')
        self._embed_general_message_stats()
        self._embed_top_visible_channel_stats()
        self._embed_top_active_user_stats()

    def _generate_member_embed(self):
        """Analyzes the subject as a member."""
        self.embed = self.bot.generate_embed('📈', f'Przygotowano raport o użytkowniku {self.subject}', self.description)
        self.embed.add_field(
            name='Utworzył konto', value=human_datetime(self.subject.created_at, utc=True), inline=False
        )
        self.embed.add_field(
            name='Ostatnio dołączył do serwera', value=human_datetime(self.subject.joined_at, utc=True), inline=False
        )
        self._embed_personal_stats()

    def _generate_user_embed(self):
        """Analyzes the subject as a user."""
        self.embed = self.bot.generate_embed('📈', f'Przygotowano raport o użytkowniku {self.subject}')
        self.embed.add_field(
            name='Utworzył konto', value=human_datetime(self.subject.created_at, utc=True), inline=False
        )
        self._embed_personal_stats()

    def _generate_deleted_user_embed(self):
        """Analyzes the subject as a user."""
        self.embed = self.bot.generate_embed('📈', f'Przygotowano raport o usuniętym użytkowniku ID {self.subject_id}')
        self._embed_personal_stats()

    def _generate_role_embed(self):
        """Analyzes the subject as a member."""
        self.embed = self.bot.generate_embed('📈', f'Przygotowano raport o roli {self.subject}', self.description)
        self.embed.add_field(name='Członków', value=f'{len(cast(discord.Role, self.subject).members):n}')
        self._embed_general_message_stats()
        self._embed_top_visible_channel_stats()
        self._embed_top_active_user_stats()
        self.embed.color = cast(discord.Role, self.subject).color

    def _embed_personal_stats(self):
        if self.total_message_count:
            earliest = self.earliest_relevant_message
            latest = self.latest_relevant_message
            self.embed.add_field(
                name=f'Wysłał pierwszą wiadomość na serwerze {"w przedziale czasowym" if self.last_days else ""}',
                value=md_link(
                    human_datetime(earliest.created_at),
                    f'https://discordapp.com/channels/{earliest.server_id}/{earliest.channel_id}/{earliest.id}',
                ),
                inline=False,
            )
            if self.ctx.author != self.subject:
                self.embed.add_field(
                    name='Wysłał ostatnią wiadomość na serwerze',
                    value=md_link(
                        human_datetime(latest.created_at),
                        f'https://discordapp.com/channels/{latest.server_id}/{latest.channel_id}/{latest.id}',
                    ),
                    inline=False,
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
            max_daily_message_date = dt.date.fromisoformat(max_daily_message_date_isoformat)
            self.embed.add_field(
                name='Maksymalnie wiadomości dziennie',
                value=f'{max_daily_message_count:n} ({max_daily_message_date.strftime("%-d %B %Y")})',
            )
            self.embed.add_field(name='Średnio wiadomości dziennie', value=f'{self.average_daily_message_count:n}')

    def _embed_top_visible_channel_stats(self):
        """Adds the list of top active channels to the report embed."""
        visible_channel_ids = [
            channel_id
            for channel_id in self.relevant_channel_stats
            if self.bot.get_channel(channel_id)
            and self.bot.get_channel(channel_id).permissions_for(self.ctx.author).read_messages
            and self.relevant_channel_stats[channel_id]['message_count']
        ]
        visible_channel_ids.sort(key=lambda channel_id: tuple(self.relevant_channel_stats[channel_id].values()))
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
            if self.type in (self.Type.MEMBER, self.Type.USER, self.Type.DELETED_USER):
                field_name = 'Najaktywniejszy na kanałach'
            else:
                field_name = 'Najaktywniejsze kanały'
            self.embed.add_field(name=field_name, value='\n'.join(top_visible_channel_stats), inline=False)

    def _embed_top_active_user_stats(self):
        """Adds the list of top active users to the report embed."""
        active_user_ids = list(self.active_user_stats)
        active_user_ids.sort(key=lambda active_user: tuple(self.active_user_stats[active_user].values()))
        active_user_ids.reverse()
        top_active_user_stats = []
        for i, this_active_user_id in enumerate(active_user_ids[:10]):
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
        completion_seconds = round(completion_timedelta.total_seconds(), 2)
        new_messages_form = word_number_form(self.messages_cached, "nowej wiadomości", "nowych wiadomości")
        if not self.initiated_queue_processing:
            queue_timedelta = self.out_of_queue_datetime - self.init_datetime
            queue_seconds = round(queue_timedelta.total_seconds(), 2)
            footer_text = (
                f'Wygenerowano w {completion_seconds:n} s (z czego {queue_seconds:n} s w serwerowej kolejce analizy) '
                f'buforując metadane {new_messages_form}'
            )
        else:
            footer_text = f'Wygenerowano w {completion_seconds:n} s buforując metadane {new_messages_form}'
        self.embed.set_footer(text=footer_text)

    def _plot_activity_by_hour(self, ax):
        # plot the chart
        ax.bar(
            [f'{hour}:00'.zfill(5) for hour in list(range(6, 24)) + list(range(0, 6))],
            self.messages_over_hour[6:] + self.messages_over_hour[:6],
            color=self.BACKGROUND_COLOR,
            facecolor=self.FOREGROUND_COLOR,
            width=1,
            align='edge',
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
        ax.set_ylabel('Wysłanych wiadomości', color=self.FOREGROUND_COLOR, fontsize=11, fontweight='bold')

        return ax

    def _plot_activity_by_weekday(self, ax):
        # plot the chart
        ax.bar(
            calendar.day_abbr,
            self.messages_over_weekday,
            color=self.BACKGROUND_COLOR,
            facecolor=self.FOREGROUND_COLOR,
            width=1,
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
        timeframe_start_date = self.timeframe_start_date
        timeframe_end_date = self.timeframe_end_date
        day_difference = self.subject_relevancy_length - 1
        year_difference = timeframe_end_date.year - timeframe_start_date.year
        month_difference = 12 * year_difference + timeframe_end_date.month - timeframe_start_date.month

        # convert date strings provided to datetime objects
        dates = [timeframe_start_date + dt.timedelta(n) for n in range(self.subject_relevancy_length or 0)]
        messages = [self.messages_over_date[date.isoformat()] for date in dates]
        is_rolling_average = day_difference > 21
        if is_rolling_average:
            messages = rolling_average(messages, self.ROLL)

        # plot the chart
        ax.bar(dates, messages, color=self.BACKGROUND_COLOR, facecolor=self.FOREGROUND_COLOR, width=1)

        # set proper ticker intervals on the X axis accounting for the timeframe
        year_locator = mdates.YearLocator()
        month_locator = mdates.MonthLocator()
        quarter_locator = mdates.MonthLocator(bymonth=[1, 4, 7, 10])
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
            dt.datetime(timeframe_start_date.year, timeframe_start_date.month, timeframe_start_date.day) - half_day,
            dt.datetime(timeframe_end_date.year, timeframe_end_date.month, timeframe_end_date.day) + half_day,
        )
        for tick in ax.get_xticklabels():
            tick.set_rotation(30)
            tick.set_horizontalalignment('right')

        # set proper ticker intervals on the Y axis accounting for the maximum number of messages
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins='auto', steps=[10], integer=True))
        if max(messages) >= 10:
            ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(n=10))

        # make it look nice
        ax.set_facecolor(self.BACKGROUND_COLOR)
        ax.set_xlabel(
            'Data (tygodniowa średnia ruchoma)' if is_rolling_average else 'Data',
            color=self.FOREGROUND_COLOR,
            fontsize=11,
            fontweight='bold',
        )
        ax.set_ylabel('Wysłanych wiadomości', color=self.FOREGROUND_COLOR, fontsize=11, fontweight='bold')

        return ax

    def _plot_activity_by_channel(self, ax):
        # plot the chart
        channels = tuple(filter(None, map(self.bot.get_channel, self.relevant_channel_stats)))
        channel_names = [f'#{channel}' for channel in channels]
        channel_existence_lengths = (
            (self.timeframe_end_date - utc_to_naive_local(channel.created_at).date()).days + 1 for channel in channels
        )
        if self.last_days:
            channel_existence_lengths = (
                min(self.last_days, channel_existence_length) for channel_existence_length in channel_existence_lengths
            )
        average_daily_message_counts = [
            channel_stats['message_count'] / channel_existence_length
            for channel_stats, channel_existence_length in zip(
                self.relevant_channel_stats.values(), channel_existence_lengths
            )
        ]
        ax.bar(
            channel_names,
            average_daily_message_counts,
            color=self.BACKGROUND_COLOR,
            facecolor=self.FOREGROUND_COLOR,
            width=1,
        )

        # set proper X axis formatting
        ax.set_xlim(-0.5, len(channel_names) - 0.5)
        ax.set_xticklabels(channel_names, rotation=30, ha='right')

        # set proper ticker intervals on the Y axis accounting for the maximum number of messages
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins='auto', steps=[10], integer=True))
        if max(average_daily_message_counts) >= 10:
            ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(n=10))

        # make it look nice
        ax.set_facecolor(self.BACKGROUND_COLOR)
        ax.set_xlabel('Kanał', color=self.FOREGROUND_COLOR, fontsize=11, fontweight='bold')
        ax.set_ylabel(
            'Średnio wysłanych\nwiadomości dziennie', color=self.FOREGROUND_COLOR, fontsize=11, fontweight='bold'
        )

        return ax


class Activity(commands.Cog):
    GROUP = Help.Command(
        'stat',
        (),
        'Komendy związane ze statystykami serwerowymi. '
        'Użyj <?użytkownika/kanału/kategorii> zamiast <?podkomendy>, by otrzymać raport statystyczny.',
    )
    COMMANDS = (
        Help.Command('serwer', (), 'Wysyła raport o serwerze.'),
        Help.Command(
            ('kanał', 'kanal'),
            '?kanał',
            'Wysyła raport o kanale. Jeśli nie podano kanału, przyjmuje kanał na którym użyto komendy.',
        ),
        Help.Command(
            'kategoria',
            '?kategoria',
            'Wysyła raport o kategorii. Jeśli nie podano kategorii, przyjmuje kategorię do której należy kanał, '
            'na którym użyto komendy.',
        ),
        Help.Command(
            ('użytkownik', 'uzytkownik', 'user'),
            '?użytkownik',
            'Wysyła raport o użytkowniku. Jeśli nie podano użytkownika, przyjmuje użytkownika, który użył komendy.',
        ),
    )
    HELP = Help(COMMANDS, '📈', group=GROUP)

    def __init__(self, bot: Somsiad):
        self.bot = bot
        self.metadata_cache = MetadataCache(bot)

    async def cog_load(self):
        await self.metadata_cache.prepare()

    @cooldown()
    @commands.group(
        aliases=['staty', 'stats', 'activity', 'aktywność', 'aktywnosc'],
        invoke_without_command=True,
        case_insensitive=True,
    )
    async def stat(
        self,
        ctx,
        subject: Union[
            discord.TextChannel, discord.CategoryChannel, discord.Member, discord.User, discord.Role, int
        ] = None,
        last_days: int = None,
    ):
        if subject is None:
            await self.bot.send(ctx, embed=self.HELP.embeds)
        else:
            async with ctx.typing():
                report = Report(ctx, subject, metadata_cache=self.metadata_cache, last_days=last_days)
                await report.enqueue()

    @stat.error
    async def stat_error(self, ctx, error):
        if isinstance(error, commands.BadUnionArgument):
            await self.bot.send(
                ctx,
                embed=self.bot.generate_embed(
                    '⚠️', 'Nie znaleziono na serwerze pasującego użytkownika, kanału, kategorii ani roli'
                ),
            )

    @cooldown()
    @stat.command(aliases=['server', 'serwer'])
    @commands.guild_only()
    async def stat_server(self, ctx, last_days: int = None):
        async with ctx.typing():
            report = Report(ctx, ctx.guild, metadata_cache=self.metadata_cache, last_days=last_days)
            await report.enqueue()

    @cooldown()
    @stat.command(aliases=['channel', 'kanał', 'kanal'])
    @commands.guild_only()
    async def stat_channel(self, ctx, channel: discord.TextChannel = None, last_days: int = None):
        channel = channel or ctx.channel
        async with ctx.typing():
            report = Report(ctx, channel, metadata_cache=self.metadata_cache, last_days=last_days)
            await report.enqueue()

    @stat_channel.error
    async def stat_channel_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await self.bot.send(
                ctx, embed=self.bot.generate_embed('⚠️', 'Nie znaleziono na serwerze pasującego kanału')
            )

    @cooldown()
    @stat.command(aliases=['category', 'kategoria'])
    @commands.guild_only()
    async def stat_category(self, ctx, category: discord.CategoryChannel = None, last_days: int = None):
        if category is None:
            if ctx.channel.category_id is None:
                raise commands.BadArgument
            category = cast(discord.CategoryChannel, self.bot.get_channel(ctx.channel.category_id))
        async with ctx.typing():
            report = Report(ctx, category, metadata_cache=self.metadata_cache, last_days=last_days)
            await report.enqueue()

    @stat_category.error
    async def stat_category_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await self.bot.send(
                ctx, embed=self.bot.generate_embed('⚠️', 'Nie znaleziono na serwerze pasującej kategorii')
            )

    @cooldown()
    @stat.command(aliases=['user', 'member', 'uzytkownik', 'użytkownik', 'członek'])
    @commands.guild_only()
    async def stat_member(self, ctx, member: Union[discord.Member, discord.User, int] = None, last_days: int = None):
        member = member or ctx.author
        async with ctx.typing():
            report = Report(ctx, member, metadata_cache=self.metadata_cache, last_days=last_days)
            await report.enqueue()

    @stat_member.error
    async def stat_member_error(self, ctx, error):
        if isinstance(error, commands.BadUnionArgument):
            await self.bot.send(
                ctx, embed=self.bot.generate_embed('⚠️', 'Nie znaleziono na serwerze pasującego użytkownika')
            )

    @cooldown()
    @stat.command(aliases=['role', 'rola', 'ranga', 'grupa'])
    @commands.guild_only()
    async def stat_role(self, ctx, role: discord.Role, last_days: int = None):
        async with ctx.typing():
            report = Report(ctx, role, metadata_cache=self.metadata_cache, last_days=last_days)
            await report.enqueue()

    @stat_role.error
    async def stat_role_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', 'Nie znaleziono na serwerze pasującej roli'))


async def setup(bot: Somsiad):
    await bot.add_cog(Activity(bot))
