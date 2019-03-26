# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import datetime as dt
import discord
from typing import Union, Optional, Sequence, Tuple, Dict
from somsiad import somsiad
from server_data import server_data_manager
from utilities import TextFormatter
from plugins.help_message import Helper


class BirthdayCalendar:
    TABLE_NAME = 'birthday'
    TABLE_COLUMNS = (
        'user_id INTEGER NOT NULL PRIMARY KEY',
        'birthday_date DATE'
    )
    DATE_WITH_YEAR_FORMATS = ('%d %m %Y', '%Y %m %d', '%d %B %Y', '%d %b %Y')
    DATE_WITHOUT_YEAR_FORMATS = ('%d %m', '%d %B', '%d %b')
    MONTH_FORMATS = ('%m', '%B', '%b')
    MONTH_NAMES_1 = [
        'styczniu', 'lutym', 'marcu', 'kwietniu', 'maju', 'czerwcu', 'lipcu', 'sierpniu', 'wrześniu', 'październiku',
        'listopadzie', 'grudniu'
    ]

    @classmethod
    def _comprehend_date(cls, date_string: str, formats: Sequence[str], iteration: int = 0) -> dt.date:
        date_string_elements = date_string.replace('-', ' ').replace('.', ' ').replace('/', ' ').split()
        try:
            date = dt.datetime.strptime(" ".join(date_string_elements), formats[iteration]).date()
        except ValueError:
            return cls._comprehend_date(date_string, formats, iteration+1)
        except IndexError:
            raise ValueError
        else:
            return date

    @staticmethod
    def calculate_age(birthday_date: dt.date):
        today = dt.date.today()
        return today.year - birthday_date.year - ((today.month, today.day) < (birthday_date.month, birthday_date.day))

    @classmethod
    def comprehend_date_with_year(cls, date_string: str) -> dt.date:
        return cls._comprehend_date(date_string, cls.DATE_WITH_YEAR_FORMATS)

    @classmethod
    def comprehend_date_without_year(cls, date_string: str) -> dt.date:
        return cls._comprehend_date(date_string, cls.DATE_WITHOUT_YEAR_FORMATS)

    @classmethod
    def comprehend_month(cls, date_string: str) -> int:
        return cls._comprehend_date(date_string, cls.MONTH_FORMATS).month

    @classmethod
    def is_member_registered(cls, server: discord.Guild, member: discord.Member) -> bool:
        """Returns the provided member's birthday or None if the member hasn't set their birthday."""
        server_data_manager.ensure_table_existence_for_server(server.id, cls.TABLE_NAME, cls.TABLE_COLUMNS)

        server_data_manager.servers[server.id]['db_cursor'].execute(
            'SELECT birthday_date FROM birthday WHERE user_id = ?',
            (member.id,)
        )
        result = server_data_manager.servers[server.id]['db_cursor'].fetchone()
        is_member_registered = not result is None

        return is_member_registered

    @classmethod
    def get_birthday_date(cls, server: discord.Guild, member: discord.Member) -> Optional[dt.date]:
        """Returns the provided member's birthday or None if the member hasn't set their birthday."""
        server_data_manager.ensure_table_existence_for_server(server.id, cls.TABLE_NAME, cls.TABLE_COLUMNS)

        server_data_manager.servers[server.id]['db_cursor'].execute(
            'SELECT birthday_date FROM birthday WHERE user_id = ?',
            (member.id,)
        )
        result = server_data_manager.servers[server.id]['db_cursor'].fetchone()
        birthday_date = (
            None if result is None or result['birthday_date'] is None
            else dt.datetime.strptime(result['birthday_date'], '%Y-%m-%d').date()
        )

        return birthday_date

    @classmethod
    def get_members_with_birthday(
            cls, server: discord.Guild, *, year: int = None, month: int = None, day: int = None
    ) -> Tuple[Dict[str, Union[int, dt.date]]]:
        server_data_manager.ensure_table_existence_for_server(server.id, cls.TABLE_NAME, cls.TABLE_COLUMNS)

        condition_strings = []
        condition_variables = []
        if year is not None:
            condition_strings.append('''CAST(strftime('%Y', birthday_date) AS integer) = ?''')
            condition_variables.append(year)
        if month is not None:
            condition_strings.append('''CAST(strftime('%m', birthday_date) AS integer) = ?''')
            condition_variables.append(month)
        if day is not None:
            condition_strings.append('''CAST(strftime('%d', birthday_date) AS integer) = ?''')
            condition_variables.append(day)

        combined_condition_string = f'WHERE {" AND ".join(condition_strings)}'
        server_data_manager.servers[server.id]['db_cursor'].execute(
            f'SELECT user_id, birthday_date FROM birthday {combined_condition_string if condition_strings else ""}',
            condition_variables
        )

        rows = (
            {'user_id': row['user_id'], 'birthday_date': dt.datetime.strptime(row['birthday_date'], '%Y-%m-%d').date()}
            for row in server_data_manager.servers[server.id]['db_cursor'].fetchall()
        )
        sorted_rows = tuple(sorted(rows, key=lambda row: row['birthday_date']))

        return sorted_rows

    @classmethod
    def set_birthday(cls, server: discord.Guild, member: discord.Member, birthday_date: Optional[dt.date]):
        if cls.is_member_registered(server, member):
            server_data_manager.servers[server.id]['db_cursor'].execute(
                'UPDATE birthday SET birthday_date = ? WHERE user_id = ?',
                (None if birthday_date is None else birthday_date.isoformat(), member.id)
            )
        else:
            server_data_manager.servers[server.id]['db_cursor'].execute(
                'INSERT INTO birthday(user_id, birthday_date) VALUES (?, ?)',
                (member.id, None if birthday_date is None else birthday_date.isoformat())
            )
        server_data_manager.servers[server.id]['db'].commit()


@somsiad.bot.group(aliases=['urodziny'], invoke_without_command=True, case_insensitive=True)
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def birthday(ctx, *, member: discord.Member = None):
    if member is None:
        subcommands = (
            Helper.Command(('zapamiętaj', 'zapamietaj'), 'data', 'Zapamiętuje twoją datę urodzin na serwerze.'),
            Helper.Command('zapomnij', None, 'Zapomina twoją datę urodzin na serwerze.'),
            Helper.Command(
                'kiedy', '?użytkownik',
                'Zwraca datę urodzin <?użytkownika>. Jeśli nie podano <?użytkownika>, przyjmuje ciebie.'
            ),
            Helper.Command(
                'wiek', '?użytkownik', 'Zwraca wiek <?użytkownika>. Jeśli nie podano <?użytkownika>, przyjmuje ciebie.'
            ),
            Helper.Command(
                ('dzień', 'dzien'), '?data',
                'Zwraca listę użytkowników obchodzących urodziny danego dnia. '
                'Jeśli nie podano <?daty> przyjmuje dzisiaj.'
            ),
            Helper.Command(
                ('miesiąc', 'miesiac'), '?miesiąc',
                'Zwraca listę użytkowników obchodzących urodziny w danym miesiącu. '
                'Jeśli nie podano <?miesiąca> przyjmuje obecny miesiąc.'
            )
        )
        embed = Helper.generate_subcommands_embed('urodziny', subcommands)
        await ctx.send(ctx.author.mention, embed=embed)
    else:
        await ctx.invoke(birthday_when)


@birthday.error
async def birthday_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Nie znaleziono na serwerze pasującego użytkownika!',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)


@birthday.command(aliases=['zapamiętaj', 'zapamietaj'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def birthday_remember(ctx, *, raw_date_string):
    try:
        date = BirthdayCalendar.comprehend_date_without_year(raw_date_string)
    except ValueError:
        try:
            date = BirthdayCalendar.comprehend_date_with_year(raw_date_string)
        except ValueError:
            raise discord.ext.commands.BadArgument
        else:
            if date.year <= 1900:
                embed = discord.Embed(
                    title=f':warning: Podaj współczesną datę urodzin!',
                    color=somsiad.color
                )
                return await ctx.send(ctx.author.mention, embed=embed)
            elif date > dt.date.today():
                embed = discord.Embed(
                    title=f':warning: Podaj przeszłą datę urodzin!',
                    color=somsiad.color
                )
                return await ctx.send(ctx.author.mention, embed=embed)

    BirthdayCalendar.set_birthday(ctx.guild, ctx.author, date)

    if date.year == 1900:
        date_string = date.strftime('%-d %B')
    else:
        date_string = date.strftime('%-d %B %Y')

    embed = discord.Embed(
        title=f':white_check_mark: Ustawiono twoją datę urodzin na {date_string}',
        color=somsiad.color
    )

    return await ctx.send(ctx.author.mention, embed=embed)


@birthday_remember.error
async def birthday_remember_error(ctx, error):
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        embed = discord.Embed(
            title=':warning: Nie podano daty!',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)
    elif isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=f':warning: Podano datę w nieznanym formacie!',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)


@birthday.command(aliases=['zapomnij'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def birthday_forget(ctx):
    BirthdayCalendar.set_birthday(ctx.guild, ctx.author, None)

    embed = discord.Embed(
        title=f':white_check_mark: Zapomniano twoją datę urodzin',
        color=somsiad.color
    )

    return await ctx.send(ctx.author.mention, embed=embed)


@birthday.command(aliases=['kiedy'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def birthday_when(ctx, *, member: discord.Member = None):
    member = member or ctx.author

    date = BirthdayCalendar.get_birthday_date(ctx.guild, member)

    if date is None:
        embed = discord.Embed(
            title=f':question: {"Nie ustawiłeś" if member == ctx.author else f"{member} nie ustawił"} '
            'swojej daty urodzin na serwerze',
            color=somsiad.color
        )
    else:
        if date.year == 1900:
            date_string = date.strftime('%-d %B')
        else:
            date_string = date.strftime('%-d %B %Y')

        embed = discord.Embed(
            title=f':calendar_spiral: {"Urodziłeś" if member == ctx.author else f"{member} urodził"} się {date_string}',
            color=somsiad.color
        )

    return await ctx.send(ctx.author.mention, embed=embed)


@birthday_when.error
async def birthday_when_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Nie znaleziono na serwerze pasującego użytkownika!',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)


@birthday.command(aliases=['wiek'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def birthday_age(ctx, *, member: discord.Member = None):
    member = member or ctx.author

    date = BirthdayCalendar.get_birthday_date(ctx.guild, member)

    if date is None or date.year <= 1900:
        embed = discord.Embed(
            title=f':question: {"Nie ustawiłeś" if member == ctx.author else f"{member} nie ustawił"} '
            'swojego roku urodzin na serwerze',
            color=somsiad.color
        )
    else:
        age = BirthdayCalendar.calculate_age(date)
        embed = discord.Embed(
            title=f':calendar_spiral: {"Masz" if member == ctx.author else f"{member} ma"} '
            f'{TextFormatter.word_number_variant(age, "rok", "lata", "lat")}',
            color=somsiad.color
        )

    return await ctx.send(ctx.author.mention, embed=embed)


@birthday_age.error
async def birthday_age_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Nie znaleziono na serwerze pasującego użytkownika!',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)


@birthday.command(aliases=['dzień', 'dzien'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def birthday_day(ctx, *, date_string = None):
    if date_string is None:
        date = dt.date.today()
    else:
        date = BirthdayCalendar.comprehend_date_without_year(date_string)

    members = BirthdayCalendar.get_members_with_birthday(ctx.guild, month=date.month, day=date.day)

    if members:
        embed = discord.Embed(
            title=f':calendar_spiral: {date.strftime("%-d %B")} urodziny ma '
            f'{TextFormatter.word_number_variant(len(members), "użytkownik", "użytkowników")}',
            description='\n'.join(
                (f'<@{member["user_id"]}>' for member in members if ctx.guild.get_member(member["user_id"]) is not None)
            ),
            color=somsiad.color
        )
    else:
        embed = discord.Embed(
            title=f':question: Nikt na serwerze nie ma ustawionych urodzin {date.strftime("%-d %B")}',
            color=somsiad.color
        )

    return await ctx.send(ctx.author.mention, embed=embed)


@birthday_day.error
async def birthday_day_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Podano dzień w nieznanym formacie!',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)


@birthday.command(aliases=['miesiąc', 'miesiac'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def birthday_month(ctx, *, month_string = None):
    if month_string is None:
        month = dt.date.today().month
    else:
        try:
            month = BirthdayCalendar.comprehend_month(month_string)
        except ValueError:
            raise discord.ext.commands.BadArgument

    members = BirthdayCalendar.get_members_with_birthday(ctx.guild, month=month)

    if members:
        embed = discord.Embed(
            title=f':calendar_spiral: W {BirthdayCalendar.MONTH_NAMES_1[month-1]} urodziny ma '
            f'{TextFormatter.word_number_variant(len(members), "użytkownik", "użytkowników")}',
            description='\n'.join((
                f'{member["birthday_date"].day} – <@{member["user_id"]}>'
                for member in members if ctx.guild.get_member(member["user_id"]) is not None
            )),
            color=somsiad.color
        )
    else:
        embed = discord.Embed(
            title=f':question: Nikt na serwerze nie ma ustawionych urodzin w {BirthdayCalendar.MONTH_NAMES_1[month-1]}',
            color=somsiad.color
        )

    return await ctx.send(ctx.author.mention, embed=embed)


@birthday_month.error
async def birthday_month_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=f':warning: Podano miesiąc w nieznanym formacie!',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)
