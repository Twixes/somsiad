# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import os.path
import time
import datetime as dt
import secrets
import asyncio
import threading
import json
import sqlite3
import discord
import praw
from somsiad import somsiad
from utilities import TextFormatter
from server_settings import ServerSettingsManager, server_settings_manager


class RedditVerifier:
    FOOTER_TEXT = 'Weryfikacja konta na Reddicie'

    _db = None
    _db_cursor = None
    _phrase_parts = None

    def __init__(self, db_path: str, phrase_parts=None):
        """Connects to the database. Creates it if it doesn't exist yet. Sets up tables. Sets up phrase parts."""
        self._db = sqlite3.connect(db_path)
        self._db_cursor = self._db.cursor()
        self._db_cursor.execute(
            'PRAGMA foreign_keys = ON'
        )
        self._db_cursor.execute(
            '''CREATE TABLE IF NOT EXISTS discord_servers(
                server_id INTEGER NOT NULL PRIMARY KEY,
                verified_role_id INTEGER,
                verification_messages_channel_id INTEGER
            )'''
        )
        self._db_cursor.execute(
            '''CREATE TABLE IF NOT EXISTS discord_users(
                discord_user_id INTEGER NOT NULL PRIMARY KEY,
                reddit_username TEXT UNIQUE,
                verification_status TEXT NOT NULL,
                discord_first_contact_date NUMERIC NOT NULL DEFAULT (date('now', 'localtime')),
                phrase_gen_date NUMERIC NOT NULL DEFAULT (date('now', 'localtime')),
                verification_rejection_date NUMERIC,
                phrase TEXT,
                FOREIGN KEY(reddit_username) REFERENCES reddit_users(reddit_username)
            )'''
        )
        self._db_cursor.execute(
            '''CREATE TABLE IF NOT EXISTS reddit_users(
                reddit_username TEXT NOT NULL PRIMARY KEY,
                reddit_first_contact_date NUMERIC NOT NULL DEFAULT (date('now', 'localtime'))
            )'''
        )
        self._db.commit()
        self._phrase_parts = phrase_parts

    @staticmethod
    def is_reddit_user_trustworthy(reddit_user: str):
        """Checks if given Reddit user seems trustworthy."""
        account_karma = reddit_user.link_karma + reddit_user.comment_karma
        account_age_in_days = (time.time() - reddit_user.created_utc) / 86400
        return bool(
            account_age_in_days >= float(somsiad.conf['reddit_account_min_age_in_days']) and
            account_karma >= int(somsiad.conf['reddit_account_min_karma'])
        )

    def phrase_gen(self):
        """Assembles a unique random phrase from given phrase parts."""
        is_phrase_unique = False
        while not is_phrase_unique:
            chosen_parts = []
            for _, category_entry in self._phrase_parts.items():
                chosen_parts.append(secrets.choice(category_entry).capitalize())
            phrase = ''.join(chosen_parts)
            if self.phrase_info(phrase)['discord_user_id'] is None:
                is_phrase_unique = True
        return phrase

    def discord_server_info(self, server_id: int):
        """Returns information from the database about the given Discord server."""
        self._db_cursor.execute(
            'SELECT verified_role_id, verification_messages_channel_id FROM discord_servers WHERE server_id = ?',
            (server_id,)
        )
        discord_server_info = self._db_cursor.fetchone()
        if discord_server_info is not None:
            was_found = True
            verified_role_id = discord_server_info[0]
            verification_messages_channel_id = discord_server_info[1]
        else:
            was_found = False
            verified_role_id = None
            verification_messages_channel_id = None

        return {
            'was_found': was_found,
            'verified_role_id': verified_role_id,
            'verification_messages_channel_id': verification_messages_channel_id
        }

    def phrase_info(self, phrase: str):
        """Returns information from the database about the given phrase."""
        self._db_cursor.execute(
            '''SELECT discord_user_id, verification_status, discord_first_contact_date, phrase_gen_date,
            verification_rejection_date FROM discord_users WHERE phrase = ?''',
            (phrase,)
        )
        phrase_info = self._db_cursor.fetchone()
        if phrase_info is not None:
            discord_user_id = int(phrase_info[0]) if phrase_info[0] is not None else None
            verification_status = phrase_info[1]
            discord_first_contact_date = dt.datetime.strptime(phrase_info[2], '%Y-%m-%d').date()
            phrase_gen_date = dt.datetime.strptime(phrase_info[3], '%Y-%m-%d').date()
        else:
            discord_user_id = None
            verification_status = None
            discord_first_contact_date = None
            phrase_gen_date = None

        return {
            'discord_user_id': discord_user_id,
            'verification_status': verification_status,
            'discord_first_contact_date': discord_first_contact_date,
            'phrase_gen_date': phrase_gen_date
        }

    def discord_user_info(self, discord_user_id: int):
        """Returns information from the database about the given Discord user."""
        self._db_cursor.execute(
            '''SELECT reddit_username, verification_status, discord_first_contact_date, phrase_gen_date,
            verification_rejection_date FROM discord_users WHERE discord_user_id = ?''',
            (discord_user_id,)
        )
        discord_user_info = self._db_cursor.fetchone()
        if discord_user_info is not None:
            reddit_username = discord_user_info[0]
            verification_status = discord_user_info[1]
            discord_first_contact_date = dt.datetime.strptime(discord_user_info[2], '%Y-%m-%d').date()
            reddit_first_contact_date = None
            phrase_gen_date = dt.datetime.strptime(discord_user_info[3], '%Y-%m-%d').date()
            verification_rejection_date = dt.datetime.strptime(discord_user_info[4], '%Y-%m-%d').date()
            if reddit_username is not None:
                self._db_cursor.execute(
                    'SELECT reddit_first_contact_date FROM reddit_users WHERE reddit_username = ?',
                    (reddit_username,)
                )
                reddit_first_contact_date = self._db_cursor.fetchone()
                reddit_first_contact_date = (
                    dt.datetime.strptime(reddit_first_contact_date[0], '%Y-%m-%d').date()
                    if reddit_first_contact_date is not None else None
                )
        else:
            reddit_username = None
            verification_status = None
            discord_first_contact_date = None
            reddit_first_contact_date = None
            phrase_gen_date = None
            verification_rejection_date = None

        return {
            'reddit_username': reddit_username,
            'verification_status': verification_status,
            'discord_first_contact_date': discord_first_contact_date,
            'reddit_first_contact_date': reddit_first_contact_date,
            'phrase_gen_date': phrase_gen_date,
            'verification_rejection_date': verification_rejection_date
        }

    def reddit_user_info(self, reddit_username: str):
        """Returns information from the database about the given Reddit user."""
        self._db_cursor.execute(
            'SELECT reddit_first_contact_date FROM reddit_users WHERE reddit_username = ?',
            (reddit_username,)
        )
        reddit_first_contact_date = self._db_cursor.fetchone()
        reddit_first_contact_date = (
            dt.datetime.strptime(reddit_first_contact_date[0], '%Y-%m-%d').date()
            if reddit_first_contact_date is not None else None
        )
        self._db_cursor.execute(
            '''SELECT discord_user_id, verification_status, discord_first_contact_date, verification_rejection_date
            FROM discord_users WHERE reddit_username = ?''',
            (reddit_username,)
        )
        reddit_user_info = self._db_cursor.fetchone()
        if reddit_user_info is not None:
            discord_user_id = int(reddit_user_info[0]) if reddit_user_info[0] is not None else None
            verification_status = reddit_user_info[1]
            discord_first_contact_date = dt.datetime.strptime(reddit_user_info[2], '%Y-%m-%d').date()
            verification_rejection_date = dt.datetime.strptime(reddit_user_info[3], '%Y-%m-%d').date()
        else:
            discord_user_id = None
            verification_status = None
            discord_first_contact_date = None
            verification_rejection_date = None

        return {
            'discord_user_id': discord_user_id,
            'verification_status': verification_status,
            'discord_first_contact_date': discord_first_contact_date,
            'reddit_first_contact_date': reddit_first_contact_date,
            'verification_rejection_date': verification_rejection_date
        }

    def ensure_discord_server_existence_in_db(self, server_id: int):
        if not self.discord_server_info(server_id)['was_found']:
            self._db_cursor.execute(
                'INSERT INTO discord_servers(server_id) VALUES(?)',
                (server_id,)
            )
            self._db.commit()

    def set_discord_server_setting(self, server_id: int, column: str, value):
        self.ensure_discord_server_existence_in_db(server_id)
        self._db_cursor.execute(
            f'UPDATE discord_servers SET {column} = ? WHERE server_id = ?',
            (value, server_id)
        )
        self._db.commit()

    def get_known_servers_ids(self):
        self._db_cursor.execute(
            'SELECT server_id FROM discord_servers'
        )
        return self._db_cursor.fetchall()

    def get_verified_roles(self):
        self._db_cursor.execute(
            'SELECT server_id, verified_role_id FROM discord_servers WHERE verified_role_id IS NOT NULL'
        )
        servers = self._db_cursor.fetchall()
        results = []
        for server in servers:
            results.append({'server_id': server[0], 'verified_role_id': server[1]})
        return results

    def get_verified_role_id_of_server(self, server_id: int) -> int:
        self._db_cursor.execute(
            'SELECT verified_role_id FROM discord_servers WHERE server_id = ?',
            (server_id,)
        )
        verified_role_id = self._db_cursor.fetchone()
        if verified_role_id is not None:
            return verified_role_id[0]
        else:
            return None

    def assign_phrase(self, discord_user_id: int):
        """Assigns a phrase to a Discord user."""
        phrase = self.phrase_gen()

        if self.discord_user_info(discord_user_id)['verification_status'] is None:
            self._db_cursor.execute(
                '''INSERT INTO discord_users(discord_user_id, verification_status, phrase)
                VALUES(?, 'AWAITING_MESSAGE', ?)''',
                (discord_user_id, phrase)
            )
        else:
            self._db_cursor.execute(
                '''UPDATE discord_users SET phrase = ?, verification_status = 'AWAITING_MESSAGE', phrase_gen_date = ?
                WHERE discord_user_id = ?''',
                (phrase, dt.date.today().isoformat(), discord_user_id)
            )
        self._db.commit()
        return phrase

    def add_reddit_user(self, reddit_username: str):
        """Adds the given Reddit user to the database."""
        if self.reddit_user_info(reddit_username)['reddit_first_contact_date'] is None:
            self._db_cursor.execute(
                'INSERT INTO reddit_users(reddit_username) VALUES(?)',
                (reddit_username,)
            )
            self._db.commit()
            return self.reddit_user_info(reddit_username)
        else:
            return None

    def verify_user(self, reddit_username: str, phrase: str):
        """Assigns a Reddit username to a Discord user. Also unassigns the phrase."""
        if self.phrase_info(phrase)['discord_user_id'] is not None:
            if self.reddit_user_info(reddit_username)['discord_user_id'] is None:
                self._db_cursor.execute(
                    '''UPDATE discord_users SET reddit_username = ?, verification_status = 'VERIFIED',
                    verification_rejection_date = ?, phrase = NULL WHERE phrase = ?''',
                    (reddit_username, dt.date.today().isoformat(), phrase)
                )
                self._db.commit()
            return self.reddit_user_info(reddit_username)
        else:
            return None

    def reject_user(self, reddit_username: str, phrase: str, reason: str):
        """Assigns a Reddit username to a Discord user. Also unassigns the phrase."""
        if self.phrase_info(phrase)['discord_user_id'] is not None:
            if self.reddit_user_info(reddit_username)['discord_user_id'] is None:
                new_verification_status = f'REJECTED_{str(reason).upper()}'
                self._db_cursor.execute(
                    f'''UPDATE discord_users SET verification_status = ?,
                    verification_rejection_date = ?, phrase = NULL WHERE phrase = ?''',
                    (new_verification_status, dt.date.today().isoformat(), phrase)
                )
                self._db.commit()
            return self.reddit_user_info(reddit_username)
        else:
            return None

    def update_discord_user_verification_status(self, discord_user_id: int, new_verification_status: str):
        if self.discord_user_info(discord_user_id)['verification_status'] is not None:
            self._db_cursor.execute(
                'UPDATE discord_users SET verification_status = ? WHERE discord_user_id = ?',
                (new_verification_status, discord_user_id)
            )
            self._db.commit()
        return self.discord_user_info(discord_user_id)

    @staticmethod
    def log_verification_result(
        discord_user_id: int, reddit_username: str, *, success: bool, personal_reason: str = '',
        log_reason: str = '', server_settings_manager: ServerSettingsManager = server_settings_manager
    ):
        discord_user = somsiad.client.get_user(discord_user_id)

        if success:
            embed = discord.Embed(
                title=f':white_check_mark: Pomyślnie zweryfikowano',
                description=f'Przypisano twoje konto na Discordzie do konta /u/{reddit_username} na Reddicie.',
                color=somsiad.color
            )
        else:
            embed = discord.Embed(
                title=f':red_circle: Weryfikacja nie powiodła się',
                description=f'Próbowałeś zweryfikować się jako /u/{reddit_username}, ale {personal_reason}.',
                color=somsiad.color
            )

        embed.set_footer(text=verifier.FOOTER_TEXT)
        asyncio.ensure_future(discord_user.send(embed=embed))

        for row in server_settings_manager.get_log_channels():
            server = somsiad.client.get_guild(row['server_id'])
            if server.get_member(discord_user_id) is not None:
                channel = server.get_channel(row['log_channel_id'])
                if channel is not None:
                    if success:
                        embed = discord.Embed(
                            title=f':white_check_mark: Pomyślna weryfikacja użytkownika na Reddicie',
                            description=f'Użytkownik {discord_user.mention} został zweryfikowany jako '
                            f'/u/{reddit_username}.',
                            timestamp=dt.datetime.now(),
                            color=somsiad.color
                        )
                    else:
                        embed = discord.Embed(
                            title=f':red_circle: Nieudana próba weryfikacji użytkownika na Reddicie',
                            description=f'Użytkownik {discord_user.mention} próbował zweryfikować się jako '
                            f'/u/{reddit_username}, ale {log_reason}.',
                            timestamp=dt.datetime.now(),
                            color=somsiad.color
                        )

                    embed.set_footer(text=verifier.FOOTER_TEXT)
                    asyncio.ensure_future(channel.send(embed=embed))

    def add_verified_roles_to_discord_user(self, discord_user_id: int):
        for row in self.get_verified_roles():
            server = somsiad.client.get_guild(row['server_id'])
            member = server.get_member(discord_user_id)
            if member is not None:
                for role in server.roles:
                    if role.id == row['verified_role_id']:
                        asyncio.ensure_future(member.add_roles(role))
                        break

    async def add_verified_role_to_members_of_discord_server(self, server: discord.Guild):
        verified_role_id = self.get_verified_role_id_of_server(server.id)
        verified_role = None

        # get the verified role from server roles using the ID obtained
        for role in server.roles:
            if role.id == verified_role_id:
                verified_role = role
                break

        # add the verified role to every member that is verified
        if verified_role is not None:
            for member in server.members:
                if self.discord_user_info(member.id)['verification_status'] == 'VERIFIED':
                    await member.add_roles(verified_role)


class RedditVerificationMessageScout:
    _db_path = None
    _reddit = None
    _verifier = None
    _server_settings_manager = None

    class MessageRetrievalFailure(praw.exceptions.APIException):
        """Raised when messages could not be retrieved from Reddit."""
        pass

    def __init__(self, db_path):
        """Runs message processing in a new thread."""
        self._db_path = db_path
        loop = asyncio.get_event_loop()
        thread = threading.Thread(target=self._run, args=(loop,))
        thread.daemon = True
        thread.start()

    def _run(self, loop):
        """Ensures that message processing is running."""
        asyncio.set_event_loop(loop)
        self._reddit = praw.Reddit(
            client_id=somsiad.conf['reddit_id'],
            client_secret=somsiad.conf['reddit_secret'],
            username=somsiad.conf['reddit_username'],
            password=somsiad.conf['reddit_password'],
            user_agent=somsiad.user_agent
        )
        self._verifier = RedditVerifier(self._db_path)
        self._server_settings_manager = ServerSettingsManager()

        while True:
            try:
                self._process_unread_messages()
            except self.MessageRetrievalFailure:
                somsiad.logger.warning(
                    'Something went wrong while trying to process Reddit verification messages! Trying again...'
                )

    def _process_unread_messages(self):
        """Processes new messages from the inbox stream and uses them for verification."""
        # Handle each new message
        for message in praw.models.util.stream_generator(self._reddit.inbox.unread):
            self.process_message(message)

    def process_message(self, message: praw.models.Message):
        reddit_username = str(message.author)
        self._verifier.add_reddit_user(reddit_username)
        if message.subject == 'Weryfikacja':
            # Check if (and when) Reddit account was verified
            phrase = message.body.strip().strip('"\'')
            reddit_user_info = self._verifier.reddit_user_info(str(message.author))
            if reddit_user_info['discord_user_id'] is None:
                # Check if the phrase is in the database

                if self._verifier.phrase_info(phrase)['discord_user_id'] is None:
                    message.reply(
                        'Weryfikacja nie powiodła się. Wysłana fraza nie odpowiada żadnemu użytkownikowi Discorda.'
                    )

                else:
                    # Check if the phrase was sent the same day it was generated
                    message_sent_date = dt.date.fromtimestamp(message.created_utc)
                    phrase_info = self._verifier.phrase_info(phrase)
                    if message_sent_date == phrase_info['phrase_gen_date']:
                        if self._verifier.is_reddit_user_trustworthy(message.author):
                            # If the phrase was indeed sent the same day it was generated
                            # and the user seems to be trustworthy,
                            # assign the Reddit username to the Discord user whose secret phrase this was
                            self._verifier.verify_user(reddit_username, phrase)
                            discord_user = somsiad.client.get_user(phrase_info['discord_user_id'])
                            self._verifier.add_verified_roles_to_discord_user(phrase_info['discord_user_id'])
                            self._verifier.log_verification_result(
                                phrase_info['discord_user_id'],
                                reddit_username,
                                success=True,
                                server_settings_manager=self._server_settings_manager
                            )
                            message.reply(
                                f'Pomyślnie zweryfikowano! Przypisano to konto do użytkownika Discorda '
                                f'{discord_user}.'
                            )
                        else:
                            self._verifier.reject_user(reddit_username, phrase, 'NOT_TRUSTWORTHY')
                            account_min_age_in_days = int(somsiad.conf['reddit_account_min_age_in_days'])
                            self._verifier.log_verification_result(
                                phrase_info['discord_user_id'],
                                reddit_username,
                                success=False,
                                personal_reason='twoje konto na Reddicie nie spełnia wymagań. '
                                f'Do weryfikacji potrzebne jest konto założone co najmniej '
                                f'{TextFormatter.noun_variant(account_min_age_in_days, "dzień", "dni")} temu '
                                f'i o karmie nie niższej niż {somsiad.conf["reddit_account_min_karma"]}',
                                log_reason='jego konto na Reddicie nie spełniło wymagań',
                                server_settings_manager=self._server_settings_manager
                            )
                            message.reply(
                                'Weryfikacja nie powiodła się. Twoje konto na Reddicie nie spełnia wymagań. '
                                f'Do weryfikacji potrzebne jest konto założone co najmniej '
                                f'{TextFormatter.noun_variant(account_min_age_in_days, "dzień", "dni")} temu '
                                f'i o karmie nie niższej niż {somsiad.conf["reddit_account_min_karma"]}.'
                            )

                    else:
                        self._verifier.reject_user(reddit_username, phrase, 'PHRASE_EXPIRED')
                        self._verifier.log_verification_result(
                            phrase_info['discord_user_id'],
                            reddit_username,
                            success=False,
                            personal_reason='twoja fraza wygasła. Wygeneruj nową frazę za pomocą komendy '
                            f'{somsiad.conf["command_prefix"]}weryfikacja zweryfikuj',
                            log_reason='jego fraza wygasła',
                            server_settings_manager=self._server_settings_manager
                        )
                        message.reply(
                            'Weryfikacja nie powiodła się. Wysłana fraza wygasła. Wygeneruj nową frazę '
                            'na Discordzie.'
                        )

            else:
                discord_user_id = self._verifier.reddit_user_info(reddit_username)['discord_user_id']
                discord_user = somsiad.client.get_user(discord_user_id)
                message.reply(
                    f'To konto zostało przypisane do użytkownika Discorda {discord_user} '
                    f'{reddit_user_info["verification_rejection_date"].strftime("%d %b %Y")}.'
                )

        message.mark_read()


phrase_parts_file_path = os.path.join(somsiad.bot_dir_path, 'data', 'reddit_verification_phrase_parts.json')
db_path = os.path.join(somsiad.storage_dir_path, 'reddit_verification.db')

with open(phrase_parts_file_path, 'r') as f:
    phrase_parts = json.load(f)

verifier = RedditVerifier(db_path, phrase_parts)

@somsiad.client.group(aliases=['weryfikacja'], invoke_without_command=True)
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def verification(ctx):
    embed = discord.Embed(
        title=f'Dostępne podkomendy {somsiad.conf["command_prefix"]}{ctx.invoked_with}',
        description=f'Użycie: {somsiad.conf["command_prefix"]}{ctx.invoked_with} <podkomenda>',
        color=somsiad.color
    )
    embed.add_field(
        name=f'zweryfikuj',
        value='Rozpoczyna proces weryfikacji konta na Reddicie dla ciebie.',
        inline=False
    )
    embed.add_field(
        name=f'prześwietl (przeswietl) <?użytkownik Discorda>',
        value='Sprawdza status weryfikacji konta na Reddicie dla <?użytkownika Discorda> '
        '(jeśli należy on do serwera na którym użyto komendy) lub, jeśli nie podano argumentu, dla ciebie.',
        inline=False
    )
    embed.add_field(
        name=f'rola <?rola>',
        value='Ustawia <?rolę> jako rolę automatycznie nadawaną członkom serwera po pomyślnej weryfikacji konta na '
        'Reddicie. Dodatkowo nadaje tę rolę już zweryfikowanym członkom serwera. Jeśli nie podano roli, wyłącza tę '
        'funkcję dla serwera. Działa tylko dla członków mających uprawnienie do na zarządzania rolami.',
        inline=False
    )

    await ctx.send(ctx.author.mention, embed=embed)


@verification.command(aliases=['zweryfikuj'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def verification_begin(ctx):
    """Starts the Reddit account verification process for the invoking Discord user."""
    discord_user_id = ctx.author.id
    discord_user_info = verifier.discord_user_info(discord_user_id)

    if (discord_user_info['verification_status'] is None
            or str(discord_user_info['verification_status']) == 'REJECTED_PHRASE_EXPIRED'):
        # If user has never requested verification or his phrase expired,
        # add him to the database and assign a phrase to him
        phrase = verifier.assign_phrase(discord_user_id)

        message_url = ('https://www.reddit.com/message/compose/'
            f'?to={somsiad.conf["reddit_username"]}&subject=Weryfikacja&message={phrase}')

        embed = discord.Embed(title='Dokończ weryfikację na Reddicie', color=somsiad.color)
        embed.add_field(
            name='Wygenerowano tajną frazę.',
            value=f'By zweryfikować się wyślij /u/{somsiad.conf["reddit_username"]} wiadomość o temacie '
            f'"Weryfikacja" i treści "{phrase}". Fraza ważna jest do końca dnia.'
        )
        embed.add_field(name='Najlepiej skorzystaj z linku:', value=message_url)

    elif (discord_user_info['verification_status'] == 'AWAITING_MESSAGE'
            or discord_user_info['verification_status'] == 'REJECTED_NOT_TRUSTWORTHY'):
        if discord_user_info['phrase_gen_date'] == dt.date.today():
            # If user already has requested verification today or has been rejected due to not meeting requirements,
            # fend him off
            if discord_user_info['verification_status'] == 'AWAITING_MESSAGE':
                embed = discord.Embed(title='Już zażądałeś dziś weryfikacji', color=somsiad.color)
                embed.add_field(
                    name='Sprawdź historię wiadomości.', value='Wygenerowana fraza ważna jest do końca dnia.'
                )
            elif discord_user_info['verification_status'] == 'REJECTED_NOT_TRUSTWORTHY':
                embed = discord.Embed(title='Już zażądałeś dziś weryfikacji', color=somsiad.color)
                embed.add_field(
                    name='Weryfikacja nie powiodła się dzisiaj, bo twoje konto na Reddicie nie spełnia wymagań.',
                    value=(
                        'Do weryfikacji potrzebne jest konto założone co najmniej '
                        f'{TextFormatter.noun_variant(somsiad.conf["reddit_account_min_age_in_days"], "dzień", "dni")} '
                        f'temu i o karmie nie niższej niż {somsiad.conf["reddit_account_min_karma"]}. '
                        'Spróbuj zweryfikować się innego dnia, gdy twoje konto będzie już spełniało te warunki.'
                    )
                )

        else:
            # If user has requested verification but not today, assign him a new phrase
            phrase = verifier.assign_phrase(discord_user_id)

            message_url = ('https://www.reddit.com/message/compose/'
                f'?to={somsiad.conf["reddit_username"]}&subject=Weryfikacja&message={phrase}')

            embed = discord.Embed(title='Dokończ weryfikację na Reddicie', color=somsiad.color)
            embed.add_field(
                name='Wygenerowano tajną frazę.',
                value=f'By zweryfikować się wyślij [/u/{somsiad.conf["reddit_username"]}]'
                f'(https://www.reddit.com/user/{somsiad.conf["reddit_username"]}) wiadomość o temacie '
                f'"Weryfikacja" i treści "{phrase}". Fraza ważna jest do końca dnia.'
            )
            embed.add_field(name='Najlepiej skorzystaj z linku:', value=message_url)

    elif discord_user_info['verification_status'] == 'VERIFIED':
        embed = discord.Embed(title='Już jesteś zweryfikowany', color=somsiad.color)
        embed.add_field(
            name=f'Twoje konto na Reddicie to /u/{discord_user_info["reddit_username"]}.',
            value=f'Zweryfikowano {discord_user_info["verification_rejection_date"].strftime("%d %b %Y")}.'
        )
    else:
        embed = discord.Embed(
            title='Wystąpił błąd podczas sprawdzania twojego statusu weryfikacji', color=somsiad.color
        )

    embed.set_footer(text=verifier.FOOTER_TEXT)
    await ctx.author.send(embed=embed)


@verification.command(aliases=['prześwietl', 'przeswietl'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def verification_xray(ctx, *args):
    """Checks given user's verification status.
    If no user was given, assumes message author.
    If the argument passed was "@here" or "here" or "@everyone" or "everyone",
    returns a list of verified members of, respectively, the channel or the server.
    """

    if (len(args) == 1 and args[0].strip('@\\') == 'everyone' and
            ctx.channel.permissions_for(ctx.author).manage_roles
    ):
        embed = discord.Embed(
            title='Zweryfikowani użytkownicy na tym serwerze',
            color=somsiad.color
        )
        for member in ctx.guild.members:
            discord_user_info = verifier.discord_user_info(member.id)
            if discord_user_info['verification_status'] == 'VERIFIED':
                embed.add_field(
                    name=str(member),
                    value=f'/u/{discord_user_info["reddit_username"]}',
                    inline=False
                )

    elif (len(args) == 1 and args[0].strip('@\\') == 'here' and
            ctx.channel.permissions_for(ctx.author).manage_roles
    ):
        embed = discord.Embed(
            title='Zweryfikowani użytkownicy na tym kanale',
            color=somsiad.color
        )
        for member in ctx.channel.members:
            discord_user_info = verifier.discord_user_info(member.id)
            if discord_user_info['verification_status'] == 'VERIFIED':
                embed.add_field(
                    name=str(member),
                    value=f'/u/{discord_user_info["reddit_username"]}',
                    inline=False
                )

    else:
        if not args:
            discord_user = ctx.author

        else:
            argument = ' '.join(args)
            discord_user = await somsiad.member_converter.convert(ctx, argument)

        discord_user_info = verifier.discord_user_info(discord_user.id)
        # Check if (and when) user has already been verified
        if discord_user_info['verification_status'] is None:
            embed = discord.Embed(
                title=':red_circle: Niezweryfikowany',
                description=f'Użytkownik {discord_user} nigdy nie zażądał weryfikacji.',
                color=somsiad.color
            )
        else:
            if discord_user_info['verification_status'] == 'VERIFIED':
                if ctx.channel.permissions_for(ctx.author).manage_roles:
                    more_info = (f' {discord_user_info["verification_rejection_date"].strftime("%d %b %Y")} jako [/u/{discord_user_info["reddit_username"]}]'
                    f'(https://www.reddit.com/user/{discord_user_info["reddit_username"]})')
                else:
                    more_info = ''
                embed = discord.Embed(
                    title=':white_check_mark: Zweryfikowany',
                    description=f'Użytkownik {discord_user} został zweryfikowany{more_info}.',
                    color=somsiad.color
                )
            elif str(discord_user_info['verification_status']) == 'REJECTED_NOT_TRUSTWORTHY':
                embed = discord.Embed(
                    title=':red_circle: Niezweryfikowany',
                    description=f'Użytkownik {discord_user} zażądał ostatnio weryfikacji '
                    f'{discord_user_info["phrase_gen_date"].strftime("%d %b %Y")} i spróbował się zweryfikować '
                    f'{discord_user_info["verification_rejection_date"].strftime("%d %b %Y")}, lecz jego konto nie spełniało wymagań.',
                    color=somsiad.color
                )
            elif str(discord_user_info['verification_status']) == 'REJECTED_PHRASE_EXPIRED':
                embed = discord.Embed(
                    title=':red_circle: Niezweryfikowany',
                    description=f'Użytkownik {discord_user} zażądał ostatnio weryfikacji '
                    f'{discord_user_info["phrase_gen_date"].strftime("%d %b %Y")}, ale nie dokończył jej na Reddicie w wyznaczonym czasie '
                    f'- wysłał wiadomość {discord_user_info["verification_rejection_date"].strftime("%d %b %Y")}.',
                    color=somsiad.color
                )
            elif str(discord_user_info['verification_status']) == 'AWAITING_MESSAGE':
                embed = discord.Embed(
                    title=':red_circle: Niezweryfikowany',
                    description=f'Użytkownik {discord_user} zażądał ostatnio weryfikacji '
                    f'{discord_user_info["phrase_gen_date"].strftime("%d %b %Y")}, ale nie dokończył jej na Reddicie.',
                    color=somsiad.color
                )
            else:
                embed = discord.Embed(
                    title=':warning: Błąd',
                    color=somsiad.color
                )

    embed.set_footer(text=verifier.FOOTER_TEXT)
    await ctx.send(ctx.author.mention, embed=embed)


@verification_xray.error
async def verification_xray_error(ctx, error):
    """Handles errors in the verification_xrays command."""
    if isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Błąd',
            description=f'Podany użytkownik nie znajduje się na tym serwerze.',
            color=somsiad.color
        )
        embed.set_footer(text=verifier.FOOTER_TEXT)

        await ctx.send(ctx.author.mention, embed=embed)


@verification.command(aliases=['rola'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
@discord.ext.commands.has_permissions(manage_roles=True)
async def verification_role(ctx, *args):
    """Sets the role to be given automatically to verified members."""
    provided_role_name = ' '.join(args)
    roles_found = []

    if ctx.message.role_mentions:
        roles_found.append(ctx.message.role_mentions[0])
    else:
        for role in ctx.guild.role_hierarchy:
            if role.name == provided_role_name:
                roles_found.append(role)

    if args:
        if len(roles_found) > 1:
            embed = discord.Embed(
                title=f':warning: Nie wiadomo którą rolę o nazwie "{provided_role_name}" masz na myśli',
                description=f'Upewnij się, że na serwerze jest tylko jedna rola o takiej nazwie. '
                'Możesz też po prostu użyć @wzmianki roli zamiast nazwy.',
                color=somsiad.color
            )
        elif len(roles_found) == 1:
            verifier.set_discord_server_setting(ctx.guild.id, 'verified_role_id', roles_found[0].id)
            await verifier.add_verified_role_to_members_of_discord_server(ctx.guild)
            embed = discord.Embed(
                title=f':white_check_mark: Ustawiono {roles_found[0]} jako rolę weryfikacji',
                description=f'Rola została właśnie przyznana już zweryfikowanym użytkownikom. Reszcie zostanie '
                'przyznana automatycznie, jeśli zweryfikują się.',
                color=somsiad.color
            )
        else:
            embed = discord.Embed(
                title=f':warning: Nie znaleziono na serwerze roli o nazwie "{provided_role_name}"',
                color=somsiad.color
            )
    else:
        verifier.set_discord_server_setting(ctx.guild.id, 'verified_role_id', 'NULL')
        embed = discord.Embed(
            title=f':white_check_mark: Wyłączono przyznawanie roli zweryfikowanym użytkownikom',
            color=somsiad.color
        )

    embed.set_footer(text=verifier.FOOTER_TEXT)
    await ctx.send(ctx.author.mention, embed=embed)


reddit_verification_message_scout = RedditVerificationMessageScout(db_path)
