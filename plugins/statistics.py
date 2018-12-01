# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import io
import datetime as dt
import calendar
import locale
from typing import Union, Sequence
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import discord
from somsiad import somsiad
from utilities import TextFormatter


class Report:
    """A statistics report. Can generate server, channel or member statistics."""
    COOLDOWN = max(float(somsiad.conf['command_cooldown_per_user_in_seconds']), 15.0)
    BACKGROUND_COLOR = '#32363c'
    FOREGROUND_COLOR = '#ffffff'

    statistics_cache = {}

    plt.style.use('dark_background')

    class Message:
        def __init__(
                self, message_id: int, author_id: int, channel_id: int, local_datetime: dt.datetime, word_count: int,
                character_count: int
        ):
            self.message_id = message_id
            self.author_id = author_id
            self.channel_id = channel_id
            self.local_datetime = local_datetime
            self.word_count = word_count
            self.character_count = character_count

        def __eq__(self, other):
            return self.message_id == other.message_id


    def __init__(self, requesting_member: discord.Member, subject: Union[discord.Guild, discord.TextChannel]):
        self.messages_cached = 0
        self.total_message_count = 0
        self.total_word_count = 0
        self.total_character_count = 0
        self.messages_over_hour = [0 for hour in range(24)]
        self.messages_over_weekday = [0 for weekday in range(7)]
        self.messages_over_date = {}
        self.active_users = {}
        self.active_channels = {}
        self.embed = None
        self.activity_chart_file = None
        self.init_datetime = dt.datetime.now().astimezone()
        self.requesting_member = requesting_member
        self.subject = subject
        if isinstance(subject, discord.Guild):
            self._prepare_active_channels(self.subject)
            self._prepare_messages_over_date(self.subject.created_at)
        elif isinstance(subject, discord.TextChannel):
            # Raise a BadArgument exception if the requesting user doesn't have access to the channel
            if not self.subject.permissions_for(self.requesting_member).read_messages:
                raise discord.ext.commands.BadArgument
            self._prepare_active_channels(self.subject.guild, self.subject)
            self._prepare_messages_over_date(self.subject.created_at)
        elif isinstance(subject, discord.Member):
            self._prepare_active_channels(self.subject.guild)
            self._prepare_messages_over_date(self.subject.joined_at)

    async def analyze_subject(self) -> discord.Embed:
        """Selects the right type of analysis depending on the subject."""
        if isinstance(self.subject, discord.Guild):
            await self._analyze_server()
        elif isinstance(self.subject, discord.TextChannel):
            await self._analyze_channel()
        elif isinstance(self.subject, discord.Member):
            await self._analyze_member()
        self._embed_analysis_metastatistics()
        return self.embed

    def render_activity_chart(self) -> discord.File:
        """Renders a graph presenting activity of or in the subject over time."""
        if isinstance(self.subject, discord.Guild):
            title = f'Aktywność na serwerze {self.subject}'
        elif isinstance(self.subject, discord.TextChannel):
            title = f'Aktywność na kanale #{self.subject.name}'
        elif isinstance(self.subject, discord.Member):
            title = f'Aktywność użytkownika {self.subject}'

        # Initialize the chart
        fig, [ax_by_hour, ax_by_weekday, ax_by_date] = plt.subplots(3)

        # Make it look nice
        fig.set_tight_layout(True)
        ax_by_hour.set_title(title, color=self.FOREGROUND_COLOR, fontsize=13, fontweight='bold', y=1.04)

        # Plot
        ax_by_hour = self._plot_activity_by_hour(ax_by_hour)
        ax_by_weekday = self._plot_activity_by_weekday(ax_by_weekday)
        ax_by_date = self._plot_activity_by_date(ax_by_date)

        # Save as bytes
        chart_bytes = io.BytesIO()
        fig.savefig(chart_bytes, facecolor=self.BACKGROUND_COLOR, edgecolor=self.FOREGROUND_COLOR)
        plt.close(fig)
        chart_bytes.seek(0)

        # Create a Discord file and embed it
        filename = f'activity-{self.init_datetime.now().strftime("%d.%m.%Y-%H.%M.%S")}.png'
        self.activity_chart_file = discord.File(
            fp=chart_bytes,
            filename=filename
        )
        self.embed.set_image(url=f'attachment://{filename}')

        return self.activity_chart_file

    def _prepare_statistics_cache(self, server: discord.Guild, channel: discord.TextChannel = None):
        if server.id not in self.statistics_cache:
            self.statistics_cache[server.id] = {}

        if channel is None:
            # if no channel was specified prepare for caching all channels
            for server_channel in server.text_channels:
                if server_channel.id not in self.statistics_cache[server.id]:
                    self.statistics_cache[server.id][server_channel.id] = []
            # remove nonexistent channels from the cache
            existent_channels = tuple(map(lambda channel: channel.id, server.text_channels))
            nonexistent_channels = [
                server_id for server_id in self.statistics_cache[server.id].keys() if server_id not in existent_channels
            ]
            for nonexistent_channel in nonexistent_channels:
                self.statistics_cache[server.id].pop(nonexistent_channel)
        elif channel.id not in self.statistics_cache[server.id]:
            self.statistics_cache[server.id][channel.id] = []

    def _prepare_active_channels(self, server: discord.Guild, channel: discord.TextChannel = None):
        if channel is None:
            for server_channel in server.text_channels:
                self.active_channels[server_channel.id] = {
                    'channel': server_channel, 'message_count': 0, 'word_count': 0, 'character_count': 0
                }
        else:
            self.active_channels[channel.id] = {
                'channel': channel, 'message_count': 0, 'word_count': 0, 'character_count': 0
            }

    def _prepare_messages_over_date(self, start_utc_datetime: dt.datetime):
        """Prepares the dictionary of messages over date."""
        subject_creation_date = start_utc_datetime.replace(tzinfo=dt.timezone.utc).astimezone().date()
        subject_existence_day_count = (dt.date.today() - subject_creation_date).days + 1
        subject_existence_days = [
            date for date in (
                subject_creation_date + dt.timedelta(n) for n in range(subject_existence_day_count)
            )
        ]
        for date in subject_existence_days:
            self.messages_over_date[date.isoformat()] = 0

    async def _update_statistics_cache_for_channel(self, channel: discord.TextChannel):
        try:
            async for message in channel.history(limit=None):
                if message.type == discord.MessageType.default:
                    message_local_datetime = message.created_at.replace(tzinfo=dt.timezone.utc).astimezone()
                    message_object = self.Message(
                        message.id, message.author.id, message.channel.id, message_local_datetime,
                        len(message.clean_content.split()), len(message.clean_content)
                    )
                    if message_object in self.statistics_cache[channel.guild.id][channel.id]:
                        break
                    else:
                        self.statistics_cache[channel.guild.id][channel.id].append(message_object)
                        self.messages_cached += 1
        except discord.Forbidden:
            pass

    async def _update_statistics_cache(self, server: discord.Guild, channel: discord.TextChannel = None):
        """Updates the statistics cache."""
        self._prepare_statistics_cache(server, channel)
        if channel is None:
            for server_channel in server.text_channels:
                await self._update_statistics_cache_for_channel(server_channel)
        else:
            await self._update_statistics_cache_for_channel(channel)

    def _update_message_stats(self, message: Message):
        """Updates message statistics."""
        self.total_message_count += 1
        self.total_word_count += message.word_count
        self.total_character_count += message.character_count
        self.messages_over_hour[message.local_datetime.hour] += 1
        self.messages_over_weekday[message.local_datetime.weekday()] += 1
        try:
            self.messages_over_date[message.local_datetime.strftime('%Y-%m-%d')] += 1
        except KeyError:
            pass

    def _update_active_channels(self, message: Message):
        """Updates the dictionary of active channels."""
        self.active_channels[message.channel_id]['message_count'] += 1
        self.active_channels[message.channel_id]['word_count'] += message.word_count
        self.active_channels[message.channel_id]['character_count'] += message.character_count

    def _update_active_users(self, message: Message):
        """Updates the dictionary of active users."""
        if message.author_id not in self.active_users:
            self.active_users[message.author_id] = {
                'author_id': message.author_id, 'message_count': 0, 'word_count': 0, 'character_count': 0
            }
        self.active_users[message.author_id]['message_count'] += 1
        self.active_users[message.author_id]['word_count'] += message.word_count
        self.active_users[message.author_id]['character_count'] += message.character_count

    def _embed_message_stats(self):
        """Adds the usual message statistics to the report embed."""
        self.embed.add_field(
            name='Wysłanych wiadomości',
            value=self.total_message_count
        )
        self.embed.add_field(name='Wysłanych słów', value=self.total_word_count)
        self.embed.add_field(name='Wysłanych znaków', value=self.total_character_count)
        self.embed.add_field(
            name='Średnio wiadomości dziennie',
            value=int(round(self.total_message_count / len(self.messages_over_date)))
        )

    def _embed_top_active_channels(self):
        """Adds the list of top active channels to the report embed."""
        sorted_active_channels = sorted(
            list(self.active_channels.values()), key=lambda active_channel: active_channel['message_count'],
            reverse=True
        )
        filtered_sorted_active_channels = [
            channel for channel in sorted_active_channels
            if channel['channel'].permissions_for(self.requesting_member).read_messages
        ]

        top_active_channels = []
        for channel in enumerate(filtered_sorted_active_channels[:5]):
            if channel[1]['message_count'] > 0:
                top_active_channels.append(
                    f'{channel[0]+1}. {channel[1]["channel"].mention} – '
                    f'{TextFormatter.word_number_variant(channel[1]["message_count"], "wiadomość", "wiadomości")}, '
                    f'{TextFormatter.word_number_variant(channel[1]["word_count"], "słowo", "słowa", "słów")}, '
                    f'{TextFormatter.word_number_variant(channel[1]["character_count"], "znak", "znaki", "znaków")}'
                )
        if top_active_channels:
            field_name = (
                'Najaktywniejszy na kanałach' if isinstance(self.subject, discord.Member) else 'Najaktywniejsze kanały'
            )
            top_active_channels_string = '\n'.join(top_active_channels)
            self.embed.add_field(name=field_name, value=top_active_channels_string, inline=False)

    def _embed_top_active_users(self):
        """Adds the list of top active users to the report embed."""
        sorted_active_users = sorted(
            list(self.active_users.values()), key=lambda active_user: active_user['message_count'], reverse=True
        )
        top_active_users = []
        for active_user in enumerate(sorted_active_users[:5]):
            top_active_users.append(
                f'{active_user[0]+1}. <@{active_user[1]["author_id"]}> – '
                f'{TextFormatter.word_number_variant(active_user[1]["message_count"], "wiadomość", "wiadomości")}, '
                f'{TextFormatter.word_number_variant(active_user[1]["word_count"], "słowo", "słowa", "słów")}, '
                f'{TextFormatter.word_number_variant(active_user[1]["character_count"], "znak", "znaki", "znaków")}'
            )
        if top_active_users:
            top_active_users_string = '\n'.join(top_active_users)
            self.embed.add_field(name='Najaktywniejsi użytkownicy', value=top_active_users_string, inline=False)

    async def _analyze_server(self):
        """Analyzes the subject as a server."""
        await self._update_statistics_cache(self.subject)
        for channel in self.statistics_cache[self.subject.id].values():
            for message in channel:
                self._update_message_stats(message)
                self._update_active_channels(message)
                self._update_active_users(message)

        server_creation_datetime_information = TextFormatter.time_ago(self.subject.created_at)

        self.embed = discord.Embed(
            title=f':white_check_mark: Przygotowano raport o serwerze',
            color=somsiad.color
        )
        self.embed.add_field(name='Utworzono', value=server_creation_datetime_information)
        self.embed.add_field(name='Właściciel', value=self.subject.owner.mention)
        self.embed.add_field(name='Ról', value=len(self.subject.roles))
        self.embed.add_field(name='Emoji', value=len(self.subject.emojis))
        self.embed.add_field(name='Kanałów tekstowych', value=len(self.subject.text_channels))
        self.embed.add_field(name='Kanałów głosowych', value=len(self.subject.voice_channels))
        self.embed.add_field(name='Członków', value=self.subject.member_count, inline=False)
        self._embed_message_stats()
        self._embed_top_active_channels()
        self._embed_top_active_users()

    async def _analyze_channel(self):
        """Analyzes the subject as a channel."""
        await self._update_statistics_cache(self.subject.guild, self.subject)
        for message in self.statistics_cache[self.subject.guild.id][self.subject.id]:
            self._update_message_stats(message)
            self._update_active_channels(message)
            self._update_active_users(message)

        self.embed = discord.Embed(
            title=f':white_check_mark: Przygotowano raport o kanale #{self.subject}',
            color=somsiad.color
        )
        self.embed.add_field(name='Utworzono', value=TextFormatter.time_ago(self.subject.created_at), inline=False)
        if self.subject.category is not None:
            self.embed.add_field(name='Kategoria', value=self.subject.category.name, inline=False)
        self.embed.add_field(name='Członków', value=len(self.subject.members), inline=False)
        self._embed_message_stats()
        self._embed_top_active_users()

    async def _analyze_member(self):
        """Analyzes the subject as a member."""
        await self._update_statistics_cache(self.subject.guild)
        for channel in self.statistics_cache[self.subject.guild.id].values():
            for message in channel:
                if message.author_id == self.subject.id:
                    self._update_message_stats(message)
                    self._update_active_channels(message)
                    self._update_active_users(message)

        self.embed = discord.Embed(
            title=f':white_check_mark: Przygotowano raport o użytkowniku {self.subject}',
            color=somsiad.color
        )
        self.embed.add_field(name='Utworzył konto', value=TextFormatter.time_ago(self.subject.created_at), inline=False)
        self.embed.add_field(
            name='Dołączył do serwera', value=TextFormatter.time_ago(self.subject.joined_at), inline=False
        )
        self._embed_message_stats()
        self._embed_top_active_channels()

    def _embed_analysis_metastatistics(self):
        analysis_time = dt.datetime.now().astimezone() - self.init_datetime
        self.embed.set_footer(
            text=f'Wygenerowano w {locale.str(round(analysis_time.total_seconds(), 1))} s. Zbuforowano '
            f'''{TextFormatter.word_number_variant(
                self.messages_cached, "nową wiadomość", "nowe wiadomości", "nowych wiadomości"
            )}.'''
        )

    def _plot_activity_by_hour(self, ax):
        # Plot the chart
        ax.bar(
            [f'{hour}:00'.zfill(5) for hour in list(range(6, 24)) + list(range(0, 6))],
            self.messages_over_hour[6:] + self.messages_over_hour[:6],
            color=self.BACKGROUND_COLOR,
            facecolor=self.FOREGROUND_COLOR,
            width=1,
            align='edge'
        )

        # Set proper X axis formatting
        ax.set_xlim(0, 24)
        ax.set_xticklabels(
            [f'{hour}:00'.zfill(5) for hour in list(range(6, 24)) + list(range(0, 6))], rotation=30, ha='right'
        )

        # Set proper ticker intervals on the Y axis accounting for the maximum number of messages
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins='auto', steps=[10], integer=True))
        if max(self.messages_over_hour) >= 10:
            ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(n=10))

        # Make it look nice
        ax.set_facecolor(self.BACKGROUND_COLOR)
        ax.set_xlabel('Godzina', color=self.FOREGROUND_COLOR, fontsize=11, fontweight='bold')

        return ax

    def _plot_activity_by_weekday(self, ax):
        # Plot the chart
        ax.bar(
            calendar.day_abbr,
            self.messages_over_weekday,
            color=self.BACKGROUND_COLOR,
            facecolor=self.FOREGROUND_COLOR,
            width=1
        )

        # Set proper X axis formatting
        ax.set_xlim(-0.5, 6.5)
        ax.set_xticklabels(calendar.day_abbr, rotation=30, ha='right')

        # Set proper ticker intervals on the Y axis accounting for the maximum number of messages
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins='auto', steps=[10], integer=True))
        if max(self.messages_over_weekday) >= 10:
            ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(n=10))

        # Make it look nice
        ax.set_facecolor(self.BACKGROUND_COLOR)
        ax.set_xlabel('Dzień tygodnia', color=self.FOREGROUND_COLOR, fontsize=11, fontweight='bold')
        ax.set_ylabel(
            'Wysłanych wiadomości', color=self.FOREGROUND_COLOR, fontsize=11, fontweight='bold'
        )

        return ax

    def _plot_activity_by_date(self, ax):
        # Convert date strings provided to datetime objects
        sorted_messages_over_date = sorted(
            self.messages_over_date.items(), key=lambda date: dt.datetime.strptime(date[0], '%Y-%m-%d')
        )
        dates = [dt.datetime.strptime(date[0], '%Y-%m-%d') for date in sorted_messages_over_date]
        messages_over_date = [date[1] for date in sorted_messages_over_date]

        # Plot the chart
        ax.bar(
            dates,
            messages_over_date,
            color=self.BACKGROUND_COLOR,
            facecolor=self.FOREGROUND_COLOR,
            width=1
        )

        # Set proper ticker intervals on the X axis accounting for the range of time
        start_date = dates[0]
        end_date = dates[-1]
        year_difference = end_date.year - start_date.year
        month_difference = 12 * year_difference + end_date.month - start_date.month
        day_difference = (end_date - start_date).days

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

        for tick in ax.get_xticklabels():
            tick.set_rotation(30)
            tick.set_horizontalalignment('right')

        half_day = dt.timedelta(hours=12)
        ax.set_xlim((start_date - half_day, end_date + half_day))

        # Set proper ticker intervals on the Y axis accounting for the maximum number of messages
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins='auto', steps=[10], integer=True))
        if max(messages_over_date) >= 10:
            ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(n=10))

        # Make it look nice
        ax.set_facecolor(self.BACKGROUND_COLOR)
        ax.set_xlabel('Data', color=self.FOREGROUND_COLOR, fontsize=11, fontweight='bold')

        return ax


@somsiad.bot.group(invoke_without_command=True, case_insensitive=True)
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def stat(ctx, *, subject: Union[discord.Member, discord.TextChannel] = None):
    if subject is None:
        embed = discord.Embed(
            title=f'Dostępne podkomendy {somsiad.conf["command_prefix"]}{ctx.invoked_with}',
            description=f'Użycie: {somsiad.conf["command_prefix"]}{ctx.invoked_with} <podkomenda> lub '
            f'{somsiad.conf["command_prefix"]}{ctx.invoked_with} <użytkownik/kanał>',
            color=somsiad.color
        )
        embed.add_field(
            name=f'serwer',
            value='Wysyła raport o serwerze.',
            inline=False
        )
        embed.add_field(
            name=f'kanał <?kanał>',
            value='Wysyła raport o kanale. Jeśli nie podano kanału, przyjmuje kanał na którym użyto komendy.',
            inline=False
        )
        embed.add_field(
            name=f'użytkownik <?użytkownik>',
            value='Wysyła raport o użytkowniku. '
            'Jeśli nie podano użytkownika, przyjmuje użytkownika, który użył komendy.',
            inline=False
        )
        await ctx.send(ctx.author.mention, embed=embed)
    else:
        async with ctx.typing():
            report = Report(ctx.author, subject)
            await report.analyze_subject()
            report.render_activity_chart()

        await ctx.send(ctx.author.mention, embed=report.embed, file=report.activity_chart_file)


@stat.error
async def stat_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadUnionArgument):
        embed = discord.Embed(
            title=f':warning: Nie znaleziono pasującego użytkownika ani kanału!',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)


@stat.command(aliases=['server', 'serwer'])
@discord.ext.commands.cooldown(
    1, Report.COOLDOWN, discord.ext.commands.BucketType.channel
)
@discord.ext.commands.guild_only()
async def stat_server(ctx):
    async with ctx.typing():
        report = Report(ctx.author, ctx.guild)
        await report.analyze_subject()
        report.render_activity_chart()

    await ctx.send(ctx.author.mention, embed=report.embed, file=report.activity_chart_file)


@stat.command(aliases=['channel', 'kanał', 'kanal'])
@discord.ext.commands.cooldown(
    1, Report.COOLDOWN, discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def stat_channel(ctx, *, channel: discord.TextChannel = None):
    if channel is None:
        channel = ctx.channel

    async with ctx.typing():
        report = Report(ctx.author, channel)
        await report.analyze_subject()
        report.render_activity_chart()

    await ctx.send(ctx.author.mention, embed=report.embed, file=report.activity_chart_file)


@stat_channel.error
async def stat_channel_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=f':warning: Nie znaleziono pasującego kanału!',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)


@stat.command(aliases=['user', 'member', 'użytkownik', 'członek'])
@discord.ext.commands.cooldown(
    1, Report.COOLDOWN, discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def stat_member(ctx, *, member: discord.Member = None):
    if member is None:
        member = ctx.author

    async with ctx.typing():
        report = Report(ctx.author, member)
        await report.analyze_subject()
        report.render_activity_chart()

    await ctx.send(ctx.author.mention, embed=report.embed, file=report.activity_chart_file)


@stat_member.error
async def stat_member_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Nie znaleziono na serwerze pasującego użytkownika!',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)
