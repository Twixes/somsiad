# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Optional, Sequence, List
from collections import namedtuple
import asyncio
import random
import itertools
import datetime as dt
import discord
from discord.ext import commands
from core import somsiad, Help, ServerSpecific, UserSpecific, ChannelRelated
from utilities import word_number_form, calculate_age
from configuration import configuration
import data


class BirthdayPublicnessLink(data.Base, ServerSpecific):
    born_person_user_id = data.Column(data.BigInteger, data.ForeignKey('born_persons.user_id'), primary_key=True)


class BornPerson(data.Base, UserSpecific):
    EDGE_YEAR = 1900
    birthday = data.Column(data.Date)
    birthday_public_servers = data.relationship(
        'Server', secondary='birthday_publicness_links', backref='birthday_public_born_persons'
    )

    def age(self) -> int:
        return None if self.birthday is None or self.birthday.year == self.EDGE_YEAR else calculate_age(self.birthday)

    def is_birthday_today(self) -> bool:
        today = dt.date.today()
        return (self.birthday.day, self.birthday.month) == (today.day, today.month)

    def is_birthday_public(self, session: data.RawSession, server: Optional[discord.Guild]) -> bool:
        if server is None:
            return True
        return session.query(data.Server).get(server.id) in self.birthday_public_servers

    def birthday_public_servers_presentation(self, *, on_server_id: Optional[int] = None, period: bool = True) -> str:
        if self.birthday is None:
            return f'Nie ustawiłeś swojej daty urodzin, więc nie ma czego upubliczniać{"." if period else ""}', None
        extra = None
        if not self.birthday_public_servers:
            info = 'nigdzie'
        else:
            number_of_other_servers = len(self.birthday_public_servers)
            if on_server_id:
                public_here = any((server.id == on_server_id for server in self.birthday_public_servers))
                if public_here:
                    number_of_other_servers -= 1
                if number_of_other_servers == 0:
                    info = 'tylko tutaj'
                else:
                    other_servers_number_form = word_number_form(
                        number_of_other_servers, 'innym serwerze', 'innych serwerach'
                    )
                    if public_here:
                        info = f'tutaj i na {other_servers_number_form}'
                    else:
                        info = f'na {other_servers_number_form}'
                    these_servers_number_form = word_number_form(
                        number_of_other_servers, 'Nazwę tego serwera', 'Nazwy tych serwerów', include_number=False
                    )
                    extra = f'{these_servers_number_form} otrzymasz używającej tej komendy w wiadomościach prywatnych.'
            else:
                names = [somsiad.get_guild(server.id).name for server in self.birthday_public_servers]
                servers_number_form = word_number_form(
                    number_of_other_servers, 'serwerze', 'serwerach', include_number=False
                )
                names_before_and = ', '.join(names[:-1])
                name_after_and = names[-1]
                names_presentation = ' oraz '.join(filter(None, (names_before_and, name_after_and)))
                info = f'na {servers_number_form} {names_presentation}'
        return f'Twoja data urodzin jest teraz publiczna {info}{"." if period else ""}', extra


class BirthdayNotifier(data.Base, ServerSpecific, ChannelRelated):
    BirthdayToday = namedtuple('BirthdayToday', ('discord_user', 'age'))
    WISHES = ['Sto lat', 'Wszystkiego najlepszego', 'Spełnienia marzeń', 'Szczęścia, zdrowia, pomyślności']

    async def notify(self):
        if self.channel_id is not None:
            wishes = self.WISHES.copy()
            random.shuffle(wishes)
            for birthday_today, wish in zip(self.birthdays_today(), itertools.cycle(wishes)):
                if birthday_today.age:
                    notice = f'{wish} z okazji {birthday_today.age}. urodzin!'
                else:
                    notice = f'{wish} z okazji urodzin!'
                embed = somsiad.generate_embed('🎂', notice)
                await self.discord_channel.send(birthday_today.discord_user.mention, embed=embed)

    def birthdays_today(self) -> List[BirthdayToday]:
        today = dt.date.today()
        today_tuple = (today.day, today.month)
        birthdays_today = []
        for born_person in self.server.birthday_public_born_persons:
            if (
                    born_person.birthday is not None and
                    (born_person.birthday.day, born_person.birthday.month) == today_tuple
            ):
                birthdays_today.append(self.BirthdayToday(born_person.discord_user, born_person.age()))
        birthdays_today.sort(key=lambda birthday_today: birthday_today.age or 0)
        return birthdays_today


class Birthday(commands.Cog):
    DATE_WITH_YEAR_FORMATS = ('%d %m %Y', '%Y %m %d', '%d %B %Y', '%d %b %Y')
    DATE_WITHOUT_YEAR_FORMATS = ('%d %m', '%d %B', '%d %b')
    MONTH_FORMATS = ('%m', '%B', '%b')
    NOTIFICATIONS_HOUR = 8

    GROUP = Help.Command('urodziny', (), 'Grupa komend związanych z urodzinami.')
    COMMANDS = (
        Help.Command(('zapamiętaj', 'zapamietaj', 'ustaw'), 'data', 'Zapamiętuje twoją datę urodzin.'),
        Help.Command('zapomnij', (), 'Zapomina twoją datę urodzin.'),
        Help.Command('upublicznij', (), 'Upublicznia twoją datę urodzin na serwerze.'),
        Help.Command('utajnij', (), 'Utajnia twoją datę urodzin na serwerze.'),
        Help.Command('gdzie', (), 'Informuje na jakich serwerach twoja data urodzin jest teraz publiczna.'),
        Help.Command(
            'kiedy', '?użytkownik',
            'Zwraca datę urodzin <?użytkownika>. Jeśli nie podano <?użytkownika>, przyjmuje ciebie.'
        ),
        Help.Command(
            'wiek', '?użytkownik', 'Zwraca wiek <?użytkownika>. Jeśli nie podano <?użytkownika>, przyjmuje ciebie.'
        ),
        Help.Command(
            'powiadomienia', '?podkomenda',
            'Grupa komend związanych z powiadamianiem na serwerze o dzisiejszych urodzinach członków. '
            'Użyj bez <?podkomendy>, by poznać opcje. Wymaga uprawnień administratora.'
        )
    )
    HELP = Help(COMMANDS, group=GROUP)

    NOTIFICATIONS_GROUP = Help.Command(
        'urodziny powiadomienia', (),
        'Grupa komend związanych z powiadamianiem na serwerze o dzisiejszych urodzinach członków. '
        'Wymaga uprawnień administratora.'
    )
    NOTIFICATIONS_COMMANDS = (
        Help.Command(
            'status', (), 'Informuje czy powiadomienia o urodzinach są włączone i na jaki kanał są wysyłane.'
        ),
        Help.Command(
            ('włącz', 'wlacz'), '?kanał',
            'Ustawia <?kanał> jako kanał powiadomień o dzisiejszych urodzinach. '
            'Jeśli nie podano <?kanału>, przyjmuje te na którym użyto komendy.'
        ),
        Help.Command(
            ('wyłącz', 'wylacz'), (), 'Wyłącza powiadomienia o dzisiejszych urodzinach.'
        )
    )
    NOTIFICATIONS_HELP = Help(NOTIFICATIONS_COMMANDS, group=NOTIFICATIONS_GROUP)
    NOTIFICATIONS_EXPLANATION = (
        'Wiadomości z życzeniami wysyłane są o 8 rano dla członków serwera, którzy obchodzą tego dnia urodziny '
        'i upublicznili tu ich datę.'
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _comprehend_date(date_string: str, formats: Sequence[str]) -> dt.date:
        date_string = date_string.replace('-', ' ').replace('.', ' ').replace('/', ' ').strip()
        for i in itertools.count():
            try:
                date = dt.datetime.strptime(date_string, formats[i]).date()
            except ValueError:
                continue
            except IndexError:
                raise ValueError
            else:
                return date

    def comprehend_date_with_year(self, date_string: str) -> dt.date:
        return self._comprehend_date(date_string, self.DATE_WITH_YEAR_FORMATS)

    def comprehend_date_without_year(self, date_string: str) -> dt.date:
        return self._comprehend_date(date_string, self.DATE_WITHOUT_YEAR_FORMATS)

    def comprehend_month(self, date_string: str) -> int:
        return self._comprehend_date(date_string, self.MONTH_FORMATS).month

    async def send_all_birthday_today_notifications(self):
        with data.session(commit=True) as session:
            birthday_notifiers = session.query(BirthdayNotifier).all()
            for birthday_notifier in birthday_notifiers:
                await birthday_notifier.notify()

    async def initiate_notification_cycle(self):
        first_time = True
        while True:
            now = dt.datetime.now()
            next_day = now.hour >= self.NOTIFICATIONS_HOUR if first_time else True
            cycle_initiation = dt.datetime(
                now.year, now.month, now.day + 1 if next_day else now.day, self.NOTIFICATIONS_HOUR
            )
            timedelta = cycle_initiation - now
            await asyncio.sleep(timedelta.total_seconds())
            await self.send_all_birthday_today_notifications()
            first_time = False

    @commands.Cog.listener()
    async def on_ready(self):
        await self.initiate_notification_cycle()

    @commands.group(aliases=['urodziny'], invoke_without_command=True, case_insensitive=True)
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def birthday(self, ctx, *, member: discord.Member = None):
        if member is None:
            await somsiad.send(ctx, embeds=self.HELP.embeds)
        else:
            await ctx.invoke(self.birthday_when, member=member)

    @birthday.error
    async def birthday_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = somsiad.generate_embed('⚠️', 'Nie znaleziono na serwerze pasującego użytkownika')
            await somsiad.send(ctx, embed=embed)

    @birthday.command(aliases=['zapamiętaj', 'zapamietaj', 'ustaw'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def birthday_remember(self, ctx, *, raw_date_string):
        try:
            date = self.comprehend_date_without_year(raw_date_string)
        except ValueError:
            try:
                date = self.comprehend_date_with_year(raw_date_string)
            except ValueError:
                raise commands.BadArgument('could not comprehend date')
            else:
                if date.year <= BornPerson.EDGE_YEAR:
                    raise commands.BadArgument('date is in too distant past')
                elif date > dt.date.today():
                    raise commands.BadArgument('date is in the future')
        with data.session(commit=True) as session:
            born_person = session.query(BornPerson).get(ctx.author.id)
            if born_person is not None:
                born_person.birthday = date
            else:
                born_person = BornPerson(user_id=ctx.author.id, birthday=date)
                session.add(born_person)
            if ctx.guild is not None:
                this_server = session.query(data.Server).get(ctx.guild.id)
                born_person.birthday_public_servers.append(this_server)
            date_presentation = date.strftime('%-d %B' if date.year == BornPerson.EDGE_YEAR else '%-d %B %Y')
            birthday_public_servers_presentation, _ = born_person.birthday_public_servers_presentation(
                on_server_id=ctx.guild.id if ctx.guild else None
            )
            embed = somsiad.generate_embed(
                '✅', f'Ustawiono twoją datę urodzin na {date_presentation}', birthday_public_servers_presentation
            )
        await somsiad.send(ctx, embed=embed)

    @birthday_remember.error
    async def birthday_remember_error(self, ctx, error):
        notice = None
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title=':warning: Nie podano daty!',
                color=somsiad.COLOR
            )
        elif isinstance(error, commands.BadArgument):
            if str(error) == 'could not comprehend date':
                notice = 'Nie rozpoznano formatu daty'
            elif str(error) == 'date is in too distant past':
                notice = 'Podaj współczesną datę urodzin'
            elif str(error) == 'date is in the future':
                notice = 'Podaj przeszłą datę urodzin'
        if notice is not None:
            embed = somsiad.generate_embed('⚠️', notice)
            await somsiad.send(ctx, embed=embed)

    @birthday.command(aliases=['zapomnij'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def birthday_forget(self, ctx):
        forgotten = False
        with data.session(commit=True) as session:
            born_person = session.query(BornPerson).get(ctx.author.id)
            if born_person is not None:
                if born_person.birthday is not None:
                    forgotten = True
                born_person.birthday = None
            else:
                born_person = BornPerson(user_id=ctx.author.id)
                session.add(born_person)
        if forgotten:
            embed = somsiad.generate_embed('✅', 'Zapomniano twoją datę urodzin')
        else:
            embed = somsiad.generate_embed('ℹ️', 'Brak daty urodzin do zapomnienia')
        await somsiad.send(ctx, embed=embed)

    @birthday.command(aliases=['upublicznij'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    @commands.guild_only()
    async def birthday_make_public(self, ctx):
        with data.session(commit=True) as session:
            born_person = session.query(BornPerson).get(ctx.author.id)
            this_server = session.query(data.Server).get(ctx.guild.id)
            if born_person is None or born_person.birthday is None:
                embed = somsiad.generate_embed(
                    'ℹ️', 'Nie ustawiłeś swojej daty urodzin, więc nie ma czego upubliczniać'
                )
            elif this_server in born_person.birthday_public_servers:
                birthday_public_servers_presentation, _ = born_person.birthday_public_servers_presentation(
                    on_server_id=ctx.guild.id
                )
                embed = somsiad.generate_embed(
                    'ℹ️', 'Twoja data urodzin już była publiczna na tym serwerze', birthday_public_servers_presentation
                )
            else:
                born_person.birthday_public_servers.append(this_server)
                birthday_public_servers_presentation, _ = born_person.birthday_public_servers_presentation(
                    on_server_id=ctx.guild.id
                )
                embed = somsiad.generate_embed(
                    '✅', 'Upubliczniono twoją datę urodzin na tym serwerze', birthday_public_servers_presentation
                )
        await somsiad.send(ctx, embed=embed)

    @birthday.command(aliases=['utajnij'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    @commands.guild_only()
    async def birthday_make_secret(self, ctx):
        with data.session(commit=True) as session:
            born_person = session.query(BornPerson).get(ctx.author.id)
            this_server = session.query(data.Server).get(ctx.guild.id)
            if born_person is None or born_person.birthday is None:
                embed = somsiad.generate_embed(
                    'ℹ️', 'Nie ustawiłeś swojej daty urodzin, więc nie ma czego utajniać'
                )
            elif this_server not in born_person.birthday_public_servers:
                birthday_public_servers_presentation, _ = born_person.birthday_public_servers_presentation(
                    on_server_id=ctx.guild.id
                )
                embed = somsiad.generate_embed(
                    'ℹ️', 'Twoja data urodzin już była tajna na tym serwerze', birthday_public_servers_presentation
                )
            else:
                born_person.birthday_public_servers.remove(this_server)
                birthday_public_servers_presentation, _ = born_person.birthday_public_servers_presentation(
                    on_server_id=ctx.guild.id
                )
                embed = somsiad.generate_embed(
                    '✅', 'Utajniono twoją datę urodzin na tym serwerze', birthday_public_servers_presentation
                )
        await somsiad.send(ctx, embed=embed)

    @birthday.command(aliases=['gdzie'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def birthday_where(self, ctx):
        with data.session() as session:
            born_person = session.query(BornPerson).get(ctx.author.id)
            birthday_public_servers_presentation, extra = born_person.birthday_public_servers_presentation(
                on_server_id=ctx.guild.id if ctx.guild else None, period=False
            )
        embed = discord.Embed(
            title=f':information_source: {birthday_public_servers_presentation}',
            description=extra,
            color=somsiad.COLOR
        )
        await somsiad.send(ctx, embed=embed)

    @birthday.command(aliases=['kiedy'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def birthday_when(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        with data.session() as session:
            born_person = session.query(BornPerson).get(member.id)
            is_birthday_unset = born_person is None or born_person.birthday is None
            is_birthday_public = born_person.is_birthday_public(session, ctx.guild)
            if is_birthday_unset:
                if member == ctx.author:
                    address = 'Nie ustawiłeś'
                else:
                    address = f'{member} nie ustawił'
                embed = discord.Embed(
                    title=f':question: {address} swojej daty urodzin',
                    color=somsiad.COLOR
                )
            elif not is_birthday_public:
                if member == ctx.author:
                    address = 'Nie upubliczniłeś'
                else:
                    address = f'{member} nie upublicznił'
                embed = discord.Embed(
                    title=f':question: {address} na tym serwerze swojej daty urodzin',
                    color=somsiad.COLOR
                )
            else:
                emoji = 'birthday' if born_person.is_birthday_today() else 'calendar_spiral'
                address = 'Urodziłeś' if member == ctx.author else f'{member} urodził'
                date_presentation = born_person.birthday.strftime(
                    '%-d %B' if born_person.birthday.year == BornPerson.EDGE_YEAR else '%-d %B %Y'
                )
                embed = discord.Embed(
                    title=f':{emoji}: {address} się {date_presentation}',
                    color=somsiad.COLOR
                )
        return await somsiad.send(ctx, embed=embed)

    @birthday_when.error
    async def birthday_when_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title=':warning: Nie znaleziono na serwerze pasującego użytkownika!',
                color=somsiad.COLOR
            )
            await somsiad.send(ctx, embed=embed)

    @birthday.command(aliases=['wiek'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def birthday_age(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        with data.session() as session:
            born_person = session.query(BornPerson).get(member.id)
            is_birthday_public = born_person.is_birthday_public(session, ctx.guild)
            if born_person is None or born_person.birthday is None:
                age = None
                is_birthday_unset = True
            else:
                age = born_person.age() if born_person is not None else None
                is_birthday_unset = False
            if is_birthday_unset:
                if member == ctx.author:
                    address = 'Nie ustawiłeś'
                else:
                    address = f'{member} nie ustawił'
                embed = discord.Embed(
                    title=f':question: {address} swojej daty urodzin',
                    color=somsiad.COLOR
                )
            elif not is_birthday_public:
                if member == ctx.author:
                    address = 'Nie upubliczniłeś'
                else:
                    address = f'{member} nie upublicznił'
                embed = discord.Embed(
                    title=f':question: {address} na tym serwerze swojej daty urodzin',
                    color=somsiad.COLOR
                )
            elif age is None:
                address = 'Nie ustawiłeś' if member == ctx.author else f'{member} nie ustawił'
                embed = discord.Embed(
                    title=f':question: {address} swojego roku urodzin',
                    color=somsiad.COLOR
                )
            else:
                emoji = 'birthday' if born_person.is_birthday_today() else 'calendar_spiral'
                address = 'Masz' if member == ctx.author else f'{member} ma'
                embed = discord.Embed(
                    title=f':{emoji}: {address} {word_number_form(age, "rok", "lata", "lat")}',
                    color=somsiad.COLOR
                )
        return await somsiad.send(ctx, embed=embed)

    @birthday_age.error
    async def birthday_age_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title=':warning: Nie znaleziono na serwerze pasującego użytkownika!',
                color=somsiad.COLOR
            )
            await somsiad.send(ctx, embed=embed)

    @birthday.group(aliases=['powiadomienia'], invoke_without_command=True, case_insensitive=True)
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def birthday_notifications(self, ctx):
        await somsiad.send(ctx, embeds=self.NOTIFICATIONS_HELP.embeds)

    @birthday_notifications.command(aliases=['status'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def birthday_notifications_status(self, ctx, *, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        with data.session() as session:
            birthday_notifier = session.query(BirthdayNotifier).get(ctx.guild.id)
            if birthday_notifier is not None and birthday_notifier.channel_id is not None:
                title = f'✅ Powiadomienia o urodzinach są włączone na #{birthday_notifier.discord_channel}'
                description = self.NOTIFICATIONS_EXPLANATION
            else:
                title = f'🔴 Powiadomienia o urodzinach są wyłączone'
                description = None
        embed = discord.Embed(title=title, description=description, color=somsiad.COLOR)
        await somsiad.send(ctx, embed=embed)

    @birthday_notifications.command(aliases=['włącz', 'wlacz'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def birthday_notifications_enable(self, ctx, *, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        with data.session(commit=True) as session:
            birthday_notifier = session.query(BirthdayNotifier).get(ctx.guild.id)
            title = f'✅ Włączono powiadomienia o urodzinach na #{channel}'
            if birthday_notifier is not None:
                if birthday_notifier.channel_id != channel.id:
                    birthday_notifier.channel_id = channel.id
                else:
                    title = f'ℹ️ Powiadomienia o urodzinach już były włączone na #{channel}'
            else:
                birthday_notifier = BirthdayNotifier(server_id=ctx.guild.id, channel_id=channel.id)
                session.add(birthday_notifier)
        embed = discord.Embed(title=title, description=self.NOTIFICATIONS_EXPLANATION, color=somsiad.COLOR)
        await somsiad.send(ctx, embed=embed)

    @birthday_notifications.command(aliases=['wyłącz', 'wylacz'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def birthday_notifications_disable(self, ctx):
        with data.session(commit=True) as session:
            birthday_notifier = session.query(BirthdayNotifier).get(ctx.guild.id)
            title = 'ℹ️ Powiadomienia o urodzinach już były wyłączone'
            if birthday_notifier is not None:
                if birthday_notifier.channel_id is not None:
                    birthday_notifier.channel_id = None
                    title = '🔴 Wyłączono powiadomienia o urodzinach'
            else:
                birthday_notifier = BirthdayNotifier(server_id=ctx.guild.id)
                session.add(birthday_notifier)
        embed = discord.Embed(
            title=title,
            color=somsiad.COLOR
        )
        await somsiad.send(ctx, embed=embed)


somsiad.add_cog(Birthday(somsiad))
