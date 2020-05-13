# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Optional, Sequence, List
from collections import namedtuple, defaultdict
import random
import itertools
import datetime as dt
import discord
from discord.ext import commands
from core import Help, cooldown
from utilities import word_number_form, calculate_age
import data


class BirthdayPublicnessLink(data.Base, data.ServerSpecific):
    born_person_user_id = data.Column(data.BigInteger, data.ForeignKey('born_persons.user_id'), primary_key=True)


class BornPerson(data.Base, data.UserSpecific):
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
        return server is None or session.query(data.Server).get(server.id) in self.birthday_public_servers


class BirthdayNotifier(data.Base, data.ServerSpecific, data.ChannelRelated):
    BirthdayToday = namedtuple('BirthdayToday', ('user_id', 'age'))
    WISHES = ['Sto lat', 'Wszystkiego najlepszego', 'Spełnienia marzeń', 'Szczęścia, zdrowia, pomyślności']

    def birthdays_today(self) -> List[BirthdayToday]:
        today = dt.date.today()
        today_tuple = (today.day, today.month)
        birthdays_today = []
        for born_person in self.server.birthday_public_born_persons:
            if (
                    born_person.birthday is not None and
                    (born_person.birthday.day, born_person.birthday.month) == today_tuple
            ):
                birthdays_today.append(self.BirthdayToday(born_person.user_id, born_person.age()))
        birthdays_today.sort(key=lambda birthday_today: birthday_today.age or 0)
        return birthdays_today


class Birthday(commands.Cog):
    DATE_WITH_YEAR_FORMATS = (
        '%d %m %Y', '%Y %m %d', '%d %B %Y', '%d %b %Y', '%d %m %y', '%y %m %d', '%d %B %y', '%d %b %y'
    )
    DATE_WITHOUT_YEAR_FORMATS = ('%d %m', '%d %B', '%d %b')
    MONTH_FORMATS = ('%m', '%B', '%b')
    NOTIFICATIONS_TIME = (8, 0)

    GROUP = Help.Command(
        'urodziny', (), 'Komendy związane z datami urodzin. '
        'Użyj <?użytkownika> zamiast <?podkomendy>, by sprawdzić datę urodzin.'
    )
    COMMANDS = (
        Help.Command(('zapamiętaj', 'zapamietaj', 'ustaw'), 'data', 'Zapamiętuje twoją datę urodzin.'),
        Help.Command('zapomnij', (), 'Zapomina twoją datę urodzin.'),
        Help.Command(
            'upublicznij', (), 'Upublicznia twoją datę urodzin na serwerze. '
            'Dzięki temu mogą też działać serwerowe powiadomienia o urodzinach.'
        ),
        Help.Command('utajnij', (), 'Utajnia twoją datę urodzin na serwerze.'),
        Help.Command('gdzie', (), 'Informuje na jakich serwerach twoja data urodzin jest w tym momencie publiczna.'),
        Help.Command(
            'kiedy', '?użytkownik',
            'Zwraca datę urodzin <?użytkownika>. Jeśli nie podano <?użytkownika>, przyjmuje ciebie.'
        ),
        Help.Command(
            'wiek', '?użytkownik', 'Zwraca wiek <?użytkownika>. Jeśli nie podano <?użytkownika>, przyjmuje ciebie.'
        ),
        Help.Command(
            'powiadomienia', '?podkomenda',
            'Komendy związane z powiadamianiem na serwerze o dzisiejszych urodzinach członków. '
            'Użyj bez <?podkomendy>, by dowiedzieć się więcej. Wymaga uprawnień administratora.'
        )
    )
    HELP = Help(COMMANDS, '🎂', group=GROUP)

    NOTIFICATIONS_GROUP = Help.Command(
        'urodziny powiadomienia', (),
        'Komendy związane z powiadamianiem na serwerze o dzisiejszych urodzinach członków. '
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

    NOTIFICATIONS_HELP = Help(NOTIFICATIONS_COMMANDS, '🎂', group=NOTIFICATIONS_GROUP)
    NOTIFICATIONS_TIME_PRESENTATION = f'{NOTIFICATIONS_TIME[0]}:{str(NOTIFICATIONS_TIME[1]).zfill(2)}'
    NOTIFICATIONS_EXPLANATION = (
        f'Wiadomości z życzeniami wysyłane są o {NOTIFICATIONS_TIME_PRESENTATION} dla członków serwera, '
        'którzy obchodzą tego dnia urodziny i upublicznili tu ich datę.'
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.already_notified = defaultdict(set)

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

    async def send_server_birthday_notifications(self, birthday_notifier: BirthdayNotifier):
        wishes = birthday_notifier.WISHES.copy()
        random.shuffle(wishes)
        for birthday_today, wish in zip(birthday_notifier.birthdays_today(), itertools.cycle(wishes)):
            channel = birthday_notifier.discord_channel(self.bot)
            if channel is None:
                return
            key = f'{channel.guild.id}-{dt.date.today()}'
            if (
                    channel.guild.get_member(birthday_today.user_id) is None or
                    birthday_today.user_id in self.already_notified[key]
            ):
                continue
            self.already_notified[key].add(birthday_today.user_id)
            if birthday_today.age:
                notice = f'{wish} z okazji {birthday_today.age}. urodzin!'
            else:
                notice = f'{wish} z okazji urodzin!'
            embed = self.bot.generate_embed('🎂', notice)
            await channel.send(f'<@{birthday_today.user_id}>', embed=embed)

    async def send_all_birthday_today_notifications(self):
        with data.session(commit=True) as session:
            birthday_notifiers = session.query(BirthdayNotifier).all()
            for birthday_notifier in birthday_notifiers:
                if birthday_notifier.channel_id is not None:
                    await self.send_server_birthday_notifications(birthday_notifier)

    async def initiate_notification_cycle(self):
        initiated = False
        while True:
            now = dt.datetime.now()
            next_iteration = dt.datetime(
                now.year, now.month, now.day, *self.NOTIFICATIONS_TIME
            ).astimezone()
            if initiated or (now.hour, now.minute) >= self.NOTIFICATIONS_TIME:
                next_iteration += dt.timedelta(1)
            await discord.utils.sleep_until(next_iteration)
            await self.send_all_birthday_today_notifications()
            initiated = True

    def _get_birthday_public_servers_presentation(
        self, born_person: BornPerson, *, on_server_id: Optional[int] = None, period: bool = True
    ) -> str:
        if born_person.birthday is None:
            return f'Nie ustawiłeś swojej daty urodzin, więc nie ma czego upubliczniać{"." if period else ""}', None
        extra = None
        if not born_person.birthday_public_servers:
            info = 'nigdzie'
        else:
            number_of_other_servers = len(born_person.birthday_public_servers)
            if on_server_id:
                public_here = any((server.id == on_server_id for server in born_person.birthday_public_servers))
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
                names = [self.bot.get_guild(server.id).name for server in born_person.birthday_public_servers]
                servers_number_form = word_number_form(
                    number_of_other_servers, 'serwerze', 'serwerach', include_number=False
                )
                names_before_and = ', '.join(names[:-1])
                name_after_and = names[-1]
                names_presentation = ' oraz '.join(filter(None, (names_before_and, name_after_and)))
                info = f'na {servers_number_form} {names_presentation}'
        main = f'Twoja data urodzin jest w tym momencie publiczna {info}{"." if period else ""}'
        return main, extra

    @commands.Cog.listener()
    async def on_ready(self):
        await self.initiate_notification_cycle()

    @commands.group(aliases=['urodziny'], invoke_without_command=True, case_insensitive=True)
    @cooldown()
    async def birthday(self, ctx, *, member: discord.Member = None):
        if member is None:
            await self.bot.send(ctx, embeds=self.HELP.embeds)
        else:
            await ctx.invoke(self.birthday_when, member=member)

    @birthday.error
    async def birthday_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = self.bot.generate_embed('⚠️', 'Nie znaleziono na serwerze pasującego użytkownika')
            await self.bot.send(ctx, embed=embed)

    @birthday.command(aliases=['zapamiętaj', 'zapamietaj', 'ustaw'])
    @cooldown()
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
            birthday_public_servers_presentation = ' '.join(filter(None, self._get_birthday_public_servers_presentation(
                born_person, on_server_id=ctx.guild.id if ctx.guild else None
            )))
            embed = self.bot.generate_embed(
                '✅', f'Zapamiętano twoją datę urodzin jako {date_presentation}', birthday_public_servers_presentation
            )
        await self.bot.send(ctx, embed=embed)

    @birthday_remember.error
    async def birthday_remember_error(self, ctx, error):
        notice = None
        if isinstance(error, commands.MissingRequiredArgument):
            notice = 'Nie podano daty'
        elif isinstance(error, commands.BadArgument):
            if str(error) == 'could not comprehend date':
                notice = 'Nie rozpoznano formatu daty'
            elif str(error) == 'date is in too distant past':
                notice = 'Podaj współczesną datę urodzin'
            elif str(error) == 'date is in the future':
                notice = 'Podaj przeszłą datę urodzin'
        if notice is not None:
            embed = self.bot.generate_embed('⚠️', notice)
            await self.bot.send(ctx, embed=embed)

    @birthday.command(aliases=['zapomnij'])
    @cooldown()
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
            embed = self.bot.generate_embed('✅', 'Zapomniano twoją datę urodzin')
        else:
            embed = self.bot.generate_embed('ℹ️', 'Brak daty urodzin do zapomnienia')
        await self.bot.send(ctx, embed=embed)

    @birthday.command(aliases=['upublicznij'])
    @cooldown()
    @commands.guild_only()
    async def birthday_make_public(self, ctx):
        with data.session(commit=True) as session:
            born_person = session.query(BornPerson).get(ctx.author.id)
            this_server = session.query(data.Server).get(ctx.guild.id)
            if born_person is None or born_person.birthday is None:
                embed = self.bot.generate_embed(
                    'ℹ️', 'Nie ustawiłeś swojej daty urodzin, więc nie ma czego upubliczniać'
                )
            elif this_server in born_person.birthday_public_servers:
                birthday_public_servers_presentation = ' '.join(filter(
                    None, self._get_birthday_public_servers_presentation(born_person, on_server_id=ctx.guild.id)
                ))
                embed = self.bot.generate_embed(
                    'ℹ️', 'Twoja data urodzin już jest publiczna na tym serwerze', birthday_public_servers_presentation
                )
            else:
                born_person.birthday_public_servers.append(this_server)
                birthday_public_servers_presentation = ' '.join(filter(
                    None, self._get_birthday_public_servers_presentation(born_person, on_server_id=ctx.guild.id)
                ))
                embed = self.bot.generate_embed(
                    '📖', 'Upubliczniono twoją datę urodzin na tym serwerze', birthday_public_servers_presentation
                )
        await self.bot.send(ctx, embed=embed)

    @birthday.command(aliases=['utajnij'])
    @cooldown()
    @commands.guild_only()
    async def birthday_make_secret(self, ctx):
        with data.session(commit=True) as session:
            born_person = session.query(BornPerson).get(ctx.author.id)
            this_server = session.query(data.Server).get(ctx.guild.id)
            if born_person is None or born_person.birthday is None:
                embed = self.bot.generate_embed(
                    'ℹ️', 'Nie ustawiłeś swojej daty urodzin, więc nie ma czego utajniać'
                )
            elif this_server not in born_person.birthday_public_servers:
                birthday_public_servers_presentation = ' '.join(filter(
                    None, self._get_birthday_public_servers_presentation(born_person, on_server_id=ctx.guild.id)
                ))
                embed = self.bot.generate_embed(
                    'ℹ️', 'Twoja data urodzin już jest tajna na tym serwerze', birthday_public_servers_presentation
                )
            else:
                born_person.birthday_public_servers.remove(this_server)
                birthday_public_servers_presentation = ' '.join(filter(
                    None, self._get_birthday_public_servers_presentation(born_person, on_server_id=ctx.guild.id)
                ))
                embed = self.bot.generate_embed(
                    '🕵️‍♂️', 'Utajniono twoją datę urodzin na tym serwerze', birthday_public_servers_presentation
                )
        await self.bot.send(ctx, embed=embed)

    @birthday.command(aliases=['gdzie'])
    @cooldown()
    async def birthday_where(self, ctx):
        with data.session() as session:
            born_person = session.query(BornPerson).get(ctx.author.id)
            birthday_public_servers_presentation, extra = self._get_birthday_public_servers_presentation(
                born_person, on_server_id=ctx.guild.id if ctx.guild else None, period=False
            ) if born_person is not None else 'Nie ustawiłeś swojej daty urodzin, więc nie ma czego upubliczniać', None
        embed = discord.Embed(
            title=f':information_source: {birthday_public_servers_presentation}',
            description=extra,
            color=self.bot.COLOR
        )
        await self.bot.send(ctx, embed=embed)

    @birthday.command(aliases=['kiedy'])
    @cooldown()
    async def birthday_when(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        with data.session() as session:
            born_person = session.query(BornPerson).get(member.id)
            if born_person is None or born_person.birthday is None:
                if member == ctx.author:
                    address = 'Nie ustawiłeś'
                else:
                    address = f'{member} nie ustawił'
                embed = discord.Embed(
                    title=f':question: {address} swojej daty urodzin',
                    color=self.bot.COLOR
                )
            elif not born_person.is_birthday_public(session, ctx.guild):
                if member == ctx.author:
                    address = 'Nie upubliczniłeś'
                else:
                    address = f'{member} nie upublicznił'
                embed = discord.Embed(
                    title=f':question: {address} na tym serwerze swojej daty urodzin',
                    color=self.bot.COLOR
                )
            else:
                emoji = 'birthday' if born_person.is_birthday_today() else 'calendar_spiral'
                address = 'Urodziłeś' if member == ctx.author else f'{member} urodził'
                date_presentation = born_person.birthday.strftime(
                    '%-d %B' if born_person.birthday.year == BornPerson.EDGE_YEAR else '%-d %B %Y'
                )
                embed = discord.Embed(
                    title=f':{emoji}: {address} się {date_presentation}',
                    color=self.bot.COLOR
                )
        return await self.bot.send(ctx, embed=embed)

    @birthday_when.error
    async def birthday_when_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title=':warning: Nie znaleziono na serwerze pasującego użytkownika!',
                color=self.bot.COLOR
            )
            await self.bot.send(ctx, embed=embed)

    @birthday.command(aliases=['wiek'])
    @cooldown()
    async def birthday_age(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        with data.session() as session:
            born_person = session.query(BornPerson).get(member.id)
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
                    color=self.bot.COLOR
                )
            elif not born_person.is_birthday_public(session, ctx.guild):
                if member == ctx.author:
                    address = 'Nie upubliczniłeś'
                else:
                    address = f'{member} nie upublicznił'
                embed = discord.Embed(
                    title=f':question: {address} na tym serwerze swojej daty urodzin',
                    color=self.bot.COLOR
                )
            elif age is None:
                address = 'Nie ustawiłeś' if member == ctx.author else f'{member} nie ustawił'
                embed = discord.Embed(
                    title=f':question: {address} swojego roku urodzenia',
                    color=self.bot.COLOR
                )
            else:
                emoji = 'birthday' if born_person.is_birthday_today() else 'calendar_spiral'
                address = 'Masz' if member == ctx.author else f'{member} ma'
                embed = discord.Embed(
                    title=f':{emoji}: {address} {word_number_form(age, "rok", "lata", "lat")}',
                    color=self.bot.COLOR
                )
        return await self.bot.send(ctx, embed=embed)

    @birthday_age.error
    async def birthday_age_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title=':warning: Nie znaleziono na serwerze pasującego użytkownika!',
                color=self.bot.COLOR
            )
            await self.bot.send(ctx, embed=embed)

    @birthday.group(aliases=['powiadomienia'], invoke_without_command=True, case_insensitive=True)
    @cooldown()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def birthday_notifications(self, ctx):
        await self.bot.send(ctx, embeds=self.NOTIFICATIONS_HELP.embeds)

    @birthday_notifications.command(aliases=['status'])
    @cooldown()
    @commands.guild_only()
    async def birthday_notifications_status(self, ctx, *, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        with data.session() as session:
            birthday_notifier = session.query(BirthdayNotifier).get(ctx.guild.id)
            if birthday_notifier is not None and birthday_notifier.channel_id is not None:
                title = f'✅ Powiadomienia o urodzinach są włączone na #{birthday_notifier.discord_channel(self.bot)}'
                description = self.NOTIFICATIONS_EXPLANATION
            else:
                title = f'🔴 Powiadomienia o urodzinach są wyłączone'
                description = None
        embed = discord.Embed(title=title, description=description, color=self.bot.COLOR)
        await self.bot.send(ctx, embed=embed)

    @birthday_notifications.command(aliases=['włącz', 'wlacz'])
    @cooldown()
    @commands.guild_only()
    async def birthday_notifications_enable(self, ctx, *, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        with data.session(commit=True) as session:
            birthday_notifier = session.query(BirthdayNotifier).get(ctx.guild.id)
            title = f'✅ Włączono powiadomienia o urodzinach na #{channel}'
            if birthday_notifier is not None:
                if birthday_notifier.channel_id != channel.id:
                    birthday_notifier.channel_id = channel.id
                else:
                    title = f'ℹ️ Powiadomienia o urodzinach już są włączone na #{channel}'
            else:
                birthday_notifier = BirthdayNotifier(server_id=ctx.guild.id, channel_id=channel.id)
                session.add(birthday_notifier)
        embed = discord.Embed(title=title, description=self.NOTIFICATIONS_EXPLANATION, color=self.bot.COLOR)
        await self.bot.send(ctx, embed=embed)

    @birthday_notifications.command(aliases=['wyłącz', 'wylacz'])
    @cooldown()
    @commands.guild_only()
    async def birthday_notifications_disable(self, ctx):
        with data.session(commit=True) as session:
            birthday_notifier = session.query(BirthdayNotifier).get(ctx.guild.id)
            title = 'ℹ️ Powiadomienia o urodzinach już są wyłączone'
            if birthday_notifier is not None:
                if birthday_notifier.channel_id is not None:
                    birthday_notifier.channel_id = None
                    title = '🔴 Wyłączono powiadomienia o urodzinach'
            else:
                birthday_notifier = BirthdayNotifier(server_id=ctx.guild.id)
                session.add(birthday_notifier)
        embed = discord.Embed(
            title=title,
            color=self.bot.COLOR
        )
        await self.bot.send(ctx, embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Birthday(bot))
