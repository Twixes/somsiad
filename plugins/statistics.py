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
from typing import Union
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import discord
from somsiad import somsiad
from utilities import TextFormatter


class Report:
    """A statistics report. Can generate server, channel or member statistics."""
    COOLDOWN = (
        15 if int(somsiad.conf['command_cooldown_per_user_in_seconds']) < 15
        else somsiad.conf['command_cooldown_per_user_in_seconds']
    )
    BACKGROUND_COLOR = '#32363c'
    FOREGROUND_COLOR = '#ffffff'

    plt.style.use('dark_background')

    def __init__(self, requesting_user: discord.Member, subject: Union[discord.Guild, discord.TextChannel]):
        self.message_limit = 50000
        self.total_message_count = 0
        self.total_word_count = 0
        self.total_character_count = 0
        self.messages_over_date = {}
        self.messages_over_hour = [0 for hour in range(24)]
        self.active_users = {}
        self.active_channels = {}
        self.embed = None
        self.activity_chart_file = None

        self.datetime = dt.datetime.now()
        self.requesting_user = requesting_user
        self.subject = subject

        if isinstance(subject, discord.Guild):
            self.subject_type = 'server'
            self._prepare_messages_over_date(self.subject.created_at)
        elif isinstance(subject, discord.TextChannel):
            self.subject_type = 'channel'
            if not self.subject.permissions_for(self.requesting_user).read_messages:
                raise discord.ext.commands.BadArgument
            self._prepare_messages_over_date(self.subject.created_at)
        elif isinstance(subject, discord.Member):
            self.subject_type = 'member'
            self._prepare_messages_over_date(self.subject.joined_at)
            self.message_limit = 10000

    def _prepare_messages_over_date(self, start_utc_datetime: dt.datetime):
        """Updates the dictionary of messages over date."""
        subject_creation_date = start_utc_datetime.replace(tzinfo=dt.timezone.utc).astimezone().date()
        subject_existence_day_count = (dt.date.today() - subject_creation_date).days + 1
        subject_existence_days = [
            date for date in (
                subject_creation_date + dt.timedelta(n) for n in range(subject_existence_day_count)
            )
        ]
        for date in subject_existence_days:
            self.messages_over_date[date.isoformat()] = 0

    def _update_message_stats(
            self, message_sent_datetime: dt.datetime, message_word_count: int, message_character_count: int
    ):
        """Updates message statistics."""
        self.total_message_count += 1
        self.total_word_count += message_word_count
        self.total_character_count += message_character_count
        try:
            self.messages_over_date[message_sent_datetime.date().isoformat()] += 1
        except KeyError:
            pass
        self.messages_over_hour[message_sent_datetime.hour] += 1

    def _update_active_channels(
            self, channel: discord.TextChannel, message_word_count: int, message_character_count: int
    ):
        """Updates the dictionary of active channels."""
        if channel.id not in self.active_channels:
            self.active_channels[channel.id] = {
                'channel_object': channel, 'message_count': 0, 'word_count': 0, 'character_count': 0
            }
        self.active_channels[channel.id]['message_count'] += 1
        self.active_channels[channel.id]['word_count'] += message_word_count
        self.active_channels[channel.id]['character_count'] += message_character_count

    def _update_active_users(
            self, user: Union[discord.Member, discord.User], message_word_count: int, message_character_count: int
    ):
        """Updates the dictionary of active users."""
        if user.id not in self.active_users:
            self.active_users[user.id] = {
                'user_object': user, 'message_count': 0, 'word_count': 0, 'character_count': 0
            }
        self.active_users[user.id]['message_count'] += 1
        self.active_users[user.id]['word_count'] += message_word_count
        self.active_users[user.id]['character_count'] += message_character_count

    def _embed_message_stats(self):
        """Adds the usual message statistics to the report embed."""
        self.embed.add_field(
            name='Wysłanych wiadomości',
            value=(
                f'{self.total_message_count} (osiągnięto limit)' if self.total_message_count == self.message_limit
                else self.total_message_count
            )
        )
        self.embed.add_field(name='Wysłanych słów', value=self.total_word_count)
        self.embed.add_field(name='Wysłanych znaków', value=self.total_character_count)
        self.embed.add_field(
            name='Średnio wiadomości dziennie', value=int(self.total_message_count / len(self.messages_over_date))
        )

    def _embed_top_active_channels(self):
        """Adds the list of top active channels to the report embed."""
        sorted_active_channels = sorted(
            list(self.active_channels.values()), key=lambda active_channel: active_channel['message_count'],
            reverse=True
        )
        sorted_filtered_active_channels = [
            channel for channel in sorted_active_channels
            if channel['channel_object'].permissions_for(self.requesting_user).read_messages
        ]
        top_active_channels = []
        rank = 1

        for active_channel in sorted_filtered_active_channels[:5]:
            top_active_channels.append(
                f'{rank}. {active_channel["channel_object"].mention} – '
                f'{TextFormatter.noun_variant(active_channel["message_count"], "wiadomość", "wiadomości")}, '
                f'{TextFormatter.noun_variant(active_channel["word_count"], "słowo", "słów")}, '
                f'{TextFormatter.noun_variant(active_channel["character_count"], "znak", "znaków")}'
            )
            rank += 1
        field_name = 'Najaktywniejszy na kanałach' if self.subject_type == 'member' else 'Najaktywniejsze kanały'
        top_active_channels_string = '\n'.join(top_active_channels) if top_active_channels else 'Brak'
        self.embed.add_field(name=field_name, value=top_active_channels_string, inline=False)

    def _embed_top_active_users(self):
        """Adds the list of top active users to the report embed."""
        sorted_active_users = sorted(
            list(self.active_users.values()), key=lambda active_user: active_user['message_count'], reverse=True
        )
        top_active_users = []
        rank = 1
        for active_user in sorted_active_users[:5]:
            top_active_users.append(
                f'{rank}. {active_user["user_object"].mention} – '
                f'{TextFormatter.noun_variant(active_user["message_count"], "wiadomość", "wiadomości")}, '
                f'{TextFormatter.noun_variant(active_user["word_count"], "słowo", "słów")}, '
                f'{TextFormatter.noun_variant(active_user["character_count"], "znak", "znaków")}'
            )
            rank += 1
        top_active_users_string = '\n'.join(top_active_users) if top_active_users else 'Brak'
        self.embed.add_field(name='Najaktywniejsi użytkownicy', value=top_active_users_string, inline=False)

    async def _analyze_server(self):
        """Analyzes the subject as a server."""
        # Ensure that no more than message_limit messages will be downloaded by reducing the limit after each channel
        message_limit_left = self.message_limit
        for channel in self.subject.text_channels:
            async for message in channel.history(limit=message_limit_left):
                message_sent_datetime = message.created_at.replace(tzinfo=dt.timezone.utc).astimezone()
                message_word_count = len(message.clean_content.split())
                message_character_count = len(message.clean_content)

                self._update_message_stats(message_sent_datetime, message_word_count, message_character_count)
                self._update_active_channels(channel, message_word_count, message_character_count)
                self._update_active_users(message.author, message_word_count, message_character_count)

            message_limit_left = self.message_limit - self.total_message_count

        server_creation_datetime_information = TextFormatter.human_readable_time_ago(self.subject.created_at)

        self.embed = discord.Embed(
            title=f':white_check_mark: Przygotowano raport o serwerze {self.subject}',
            color=somsiad.color
        )
        self.embed.add_field(name='Utworzono', value=server_creation_datetime_information)
        self.embed.add_field(name='Właściciel', value=self.subject.owner.mention)
        self.embed.add_field(name='Ról', value=len(self.subject.roles))
        self.embed.add_field(name='Emoji', value=len(self.subject.emojis))
        self.embed.add_field(name='Kanałów tekstowych', value=len(self.subject.text_channels))
        self.embed.add_field(name='Kanałów głosowych', value=len(self.subject.voice_channels))
        self.embed.add_field(name='Członków', value=len(self.subject.members), inline=False)
        self._embed_message_stats()
        self._embed_top_active_channels()
        self._embed_top_active_users()

    async def _analyze_channel(self):
        """Analyzes the subject as a channel."""
        async for message in self.subject.history(limit=self.message_limit):
            message_sent_datetime = message.created_at.replace(tzinfo=dt.timezone.utc).astimezone()
            message_word_count = len(message.clean_content.split())
            message_character_count = len(message.clean_content)
            self._update_message_stats(message_sent_datetime, message_word_count, message_character_count)
            self._update_active_users(message.author, message_word_count, message_character_count)

        channel_creation_datetime_information = TextFormatter.human_readable_time_ago(self.subject.created_at)
        channel_category_name = self.subject.category.name if self.subject.category is not None else 'Brak'

        self.embed = discord.Embed(
            title=f':white_check_mark: Przygotowano raport o kanale #{self.subject}',
            color=somsiad.color
        )
        self.embed.add_field(name='Utworzono', value=channel_creation_datetime_information, inline=False)
        self.embed.add_field(name='Kategoria', value=channel_category_name, inline=False)
        self.embed.add_field(name='Członków', value=len(self.subject.members), inline=False)
        self._embed_message_stats()
        self._embed_top_active_users()

    async def _is_message_by_subject(self, message: discord.Message) -> bool:
        """Channel history filter predicate. Used for filtering out messages sent by users that are not our subject."""
        return message.author == self.subject

    async def _analyze_member(self):
        """Analyzes the subject as a member."""
        # Ensure that no more than message_limit messages will be downloaded by reducing the limit after each channel
        message_limit_left = self.message_limit
        for channel in self.subject.guild.text_channels:
            async for message in channel.history(limit=message_limit_left).filter(self._is_message_by_subject):
                message_sent_datetime = message.created_at.replace(tzinfo=dt.timezone.utc).astimezone()
                message_word_count = len(message.clean_content.split())
                message_character_count = len(message.clean_content)
                self._update_message_stats(message_sent_datetime, message_word_count, message_character_count)
                self._update_active_channels(message.channel, message_word_count, message_character_count)
            message_limit_left = self.message_limit - self.total_message_count

        member_account_creation_datetime_information = TextFormatter.human_readable_time_ago(self.subject.created_at)
        member_server_joining_datetime_information = TextFormatter.human_readable_time_ago(self.subject.joined_at)

        self.embed = discord.Embed(
            title=f':white_check_mark: Przygotowano raport o użytkowniku {self.subject}',
            color=somsiad.color
        )
        self.embed.add_field(name='Utworzył konto', value=member_account_creation_datetime_information, inline=False)
        self.embed.add_field(name='Dołączył do serwera', value=member_server_joining_datetime_information, inline=False)
        self._embed_message_stats()
        self._embed_top_active_channels()

    def _plot_activity_by_hour(self, ax):
        # Plot the chart
        ax.bar(
            [f'{hour}:00'.zfill(5) for hour in range(24)],
            self.messages_over_hour,
            color=self.BACKGROUND_COLOR,
            facecolor=self.FOREGROUND_COLOR,
            width=1,
            align='edge'
        )

        # Set proper X axis formatting
        ax.set_xlim(0, 24)
        ax.set_xticklabels([f'{hour}:00'.zfill(5) for hour in range(24)], rotation=30, ha='right')

        # Set proper ticker intervals on the Y axis accounting for the maximum number of messages
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins='auto', steps=[10], integer=True))
        if max(self.messages_over_hour) >= 10:
            ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(n=10))

        # Make it look nice
        ax.set_facecolor(self.BACKGROUND_COLOR)
        ax.set_xlabel('Godzina', color=self.FOREGROUND_COLOR, fontsize=11, fontweight='bold')
        ax.set_ylabel(
            'Liczba wysłanych wiadomości', color=self.FOREGROUND_COLOR, fontsize=11, fontweight='bold'
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
        day_formatter = mdates.DateFormatter('%d %b %Y')

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

        # Set proper ticker intervals on the Y axis accounting for the maximum number of messages
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins='auto', steps=[10], integer=True))
        if max(messages_over_date) >= 10:
            ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(n=10))

        # Make it look nice
        ax.set_facecolor(self.BACKGROUND_COLOR)
        ax.set_xlabel('Data', color=self.FOREGROUND_COLOR, fontsize=11, fontweight='bold')
        ax.set_ylabel(
            'Liczba wysłanych wiadomości', color=self.FOREGROUND_COLOR, fontsize=11, fontweight='bold'
        )

        return ax

    async def analyze_subject(self):
        """Selects the right type of analysis depending on the subject."""
        if self.subject_type == 'server':
            await self._analyze_server()
        elif self.subject_type == 'channel':
            await self._analyze_channel()
        elif self.subject_type == 'member':
            await self._analyze_member()

    def render_activity_chart(self) -> discord.File:
        """Renders a graph presenting activity of or in the subject over time."""
        if self.subject_type == 'server':
            title = f'Aktywność na serwerze {self.subject}'
        elif self.subject_type == 'channel':
            title = f'Aktywność na kanale #{self.subject.name}'
        elif self.subject_type == 'member':
            title = f'Aktywność użytkownika {self.subject}'

        # Initialize the chart
        fig, [ax_by_hour, ax_by_date] = plt.subplots(2)

        # Make it look nice
        fig.set_tight_layout(True)
        ax_by_hour.set_title(title, color=self.FOREGROUND_COLOR, fontsize=13, fontweight='bold', y=1.04)

        # Plot
        ax_by_hour = self._plot_activity_by_hour(ax_by_hour)
        ax_by_date = self._plot_activity_by_date(ax_by_date)

        # Save as bytes
        chart_bytes = io.BytesIO()
        fig.savefig(chart_bytes, facecolor=self.BACKGROUND_COLOR, edgecolor=self.FOREGROUND_COLOR)
        plt.close(fig)
        chart_bytes.seek(0)

        # Create a Discord file and embed it
        filename = f'activity-{self.datetime.now().strftime("%d.%m.%Y-%H.%M.%S")}.png'
        self.activity_chart_file = discord.File(
            fp=chart_bytes,
            filename=filename
        )
        self.embed.set_image(url=f'attachment://{filename}')

        return self.activity_chart_file


@somsiad.client.group(invoke_without_command=True)
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def stat(ctx):
    embed = discord.Embed(
        title=f'Dostępne podkomendy {somsiad.conf["command_prefix"]}{ctx.invoked_with}',
        description=f'Użycie: {somsiad.conf["command_prefix"]}{ctx.invoked_with} <podkomenda>',
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
        value='Wysyła raport o użytkowniku. Jeśli nie podano użytkownika, przyjmuje użytkownika, który użył komendy.',
        inline=False
    )

    await ctx.send(ctx.author.mention, embed=embed)


@stat.command(aliases=['server', 'serwer'])
@discord.ext.commands.cooldown(
    1, Report.COOLDOWN, discord.ext.commands.BucketType.channel
)
@discord.ext.commands.guild_only()
async def stat_server(ctx):
    async with ctx.channel.typing():
        report = Report(ctx.author, ctx.guild)
        await report.analyze_subject()
        report.render_activity_chart()

    await ctx.send(ctx.author.mention, embed=report.embed, file=report.activity_chart_file)


@stat_server.error
async def stat_server_error(ctx, error):
    if isinstance(error, discord.ext.commands.CommandOnCooldown):
        embed = discord.Embed(
            title=':warning: Dopiero co poproszono na tym kanale o wygenerowanie raportu o serwerze!',
            description=f'Spróbuj ponownie za {round(error.retry_after, 2)} s. '
            'Wtedy też ta wiadomość ulegnie autodestrukcji.',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed, delete_after=error.retry_after)


@stat.command(aliases=['channel', 'kanał', 'kanal'])
@discord.ext.commands.cooldown(
    1, Report.COOLDOWN, discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def stat_channel(ctx, channel: discord.TextChannel = None):
    if channel is None:
        channel = ctx.channel

    async with ctx.channel.typing():
        report = Report(ctx.author, channel)
        await report.analyze_subject()
        report.render_activity_chart()

    await ctx.send(ctx.author.mention, embed=report.embed, file=report.activity_chart_file)


@stat_channel.error
async def stat_channel_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=f':warning: Nie znaleziono podanego kanału na serwerze!',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)
    elif isinstance(error, discord.ext.commands.CommandOnCooldown):
        embed = discord.Embed(
            title=':warning: Dopiero co poprosiłeś o wygenerowanie raportu o kanale!',
            description=f'Spróbuj ponownie za {round(error.retry_after, 2)} s. '
            'Wtedy też ta wiadomość ulegnie autodestrukcji.',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed, delete_after=error.retry_after)


@stat.command(aliases=['user', 'member', 'użytkownik', 'członek'])
@discord.ext.commands.cooldown(
    1, Report.COOLDOWN, discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def stat_member(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    async with ctx.channel.typing():
        report = Report(ctx.author, member)
        await report.analyze_subject()
        report.render_activity_chart()

    await ctx.send(ctx.author.mention, embed=report.embed, file=report.activity_chart_file)


@stat_member.error
async def stat_member_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Nie znaleziono podanego użytkownika na serwerze!',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)
    elif isinstance(error, discord.ext.commands.CommandOnCooldown):
        embed = discord.Embed(
            title=':warning: Dopiero co poprosiłeś o wygenerowanie raportu o użytkowniku!',
            description=f'Spróbuj ponownie za {round(error.retry_after, 2)} s. '
            'Wtedy też ta wiadomość ulegnie autodestrukcji.',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed, delete_after=error.retry_after)
