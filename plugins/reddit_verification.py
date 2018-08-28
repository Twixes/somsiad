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
import datetime
import secrets
import threading
import json
import sqlite3
import discord
import praw
from somsiad import TextFormatter, somsiad


class RedditVerifier:
    _users_db = None
    _users_db_cursor = None
    _phrase_parts = None

    def __init__(self, users_db_path: str, phrase_parts=None):
        """Connects to the database. Creates it if it doesn't yet. Sets up phrase parts."""
        self._users_db = sqlite3.connect(users_db_path)
        self._users_db_cursor = self._users_db.cursor()
        self._users_db_cursor.execute(
            'PRAGMA foreign_keys = ON'
        )
        self._users_db_cursor.execute(
            '''CREATE TABLE IF NOT EXISTS discord_users(
                discord_user_id INTEGER NOT NULL PRIMARY KEY,
                reddit_username TEXT UNIQUE,
                verification_status TEXT NOT NULL,
                first_contact_date TEXT NOT NULL DEFAULT (date('now', 'localtime')),
                phrase_gen_date TEXT NOT NULL DEFAULT (date('now', 'localtime')),
                verification_rejection_date TEXT,
                phrase TEXT,
                FOREIGN KEY(reddit_username) REFERENCES reddit_users(reddit_username)
            )'''
        )
        self._users_db_cursor.execute(
            '''CREATE TABLE IF NOT EXISTS reddit_users(
                reddit_username TEXT NOT NULL PRIMARY KEY,
                first_contact_date TEXT NOT NULL DEFAULT (date('now', 'localtime'))
            )'''
        )
        self._users_db.commit()
        self._phrase_parts = phrase_parts

    @staticmethod
    def today_date():
        return str(datetime.date.today())

    @staticmethod
    def is_reddit_user_trustworthy(reddit_user: str):
        """Checks if given Reddit user seems trustworthy."""
        account_karma = reddit_user.link_karma + reddit_user.comment_karma
        account_age_days = (time.time() - reddit_user.created_utc) / 86400
        if (account_age_days >= float(somsiad.conf['reddit_account_min_age_days']) and
                account_karma >= int(somsiad.conf['reddit_account_min_karma'])):
            return True
        else:
            return False

    def phrase_gen(self):
        """Assembles a unique random phrase from given phrase parts."""
        is_phrase_unique = False
        while not is_phrase_unique:
            phrase = ''
            for _, category_entry in self._phrase_parts.items():
                phrase += secrets.choice(category_entry).capitalize()
            if self.phrase_info(phrase)['discord_user_id'] is None:
                is_phrase_unique = True
        return phrase

    def phrase_info(self, phrase: str):
        """Returns information related to the given phrase."""
        self._users_db_cursor.execute(
            '''SELECT discord_user_id, verification_status, first_contact_date, phrase_gen_date,
            verification_rejection_date FROM discord_users WHERE phrase = ?''',
            (phrase,)
        )
        phrase_info = self._users_db_cursor.fetchone()
        if phrase_info is not None:
            discord_user_id = int(phrase_info[0]) if phrase_info[0] is not None else None
            verification_status = phrase_info[1]
            discord_first_contact_date = phrase_info[2]
            phrase_gen_date = phrase_info[3]
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
        """Returns information related to the given Discord user."""
        self._users_db_cursor.execute(
            '''SELECT reddit_username, verification_status, first_contact_date, phrase_gen_date,
            verification_rejection_date FROM discord_users WHERE discord_user_id = ?''',
            (discord_user_id,)
        )
        discord_user_info = self._users_db_cursor.fetchone()
        if discord_user_info is not None:
            reddit_username = discord_user_info[0]
            verification_status = discord_user_info[1]
            discord_first_contact_date = discord_user_info[2]
            reddit_first_contact_date = None
            phrase_gen_date = discord_user_info[3]
            verification_rejection_date = discord_user_info[4]
            if reddit_username is not None:
                self._users_db_cursor.execute(
                    'SELECT first_contact_date FROM reddit_users WHERE reddit_username = ?',
                    (reddit_username,)
                )
                reddit_first_contact_date = self._users_db_cursor.fetchone()
                reddit_first_contact_date = (reddit_first_contact_date[0] if reddit_first_contact_date is not None
                    else None)
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
        """Returns information related to the given Reddit user."""
        self._users_db_cursor.execute(
            'SELECT first_contact_date FROM reddit_users WHERE reddit_username = ?',
            (reddit_username,)
        )
        reddit_first_contact_date = self._users_db_cursor.fetchone()
        reddit_first_contact_date = reddit_first_contact_date[0] if reddit_first_contact_date is not None else None
        self._users_db_cursor.execute(
            '''SELECT discord_user_id, verification_status, first_contact_date, verification_rejection_date
            FROM discord_users WHERE reddit_username = ?''',
            (reddit_username,)
        )
        reddit_user_info = self._users_db_cursor.fetchone()
        if reddit_user_info is not None:
            discord_user_id = int(reddit_user_info[0]) if reddit_user_info[0] is not None else None
            verification_status = reddit_user_info[1]
            discord_first_contact_date = reddit_user_info[2]
            verification_rejection_date = reddit_user_info[3]
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

    def assign_phrase(self, discord_user_id: int):
        """Assigns a phrase to a Discord user."""
        phrase = self.phrase_gen()

        if self.discord_user_info(discord_user_id)['verification_status'] is None:
            self._users_db_cursor.execute(
                '''INSERT INTO discord_users(discord_user_id, verification_status, phrase)
                VALUES(?, 'AWAITING_MESSAGE', ?)''',
                (discord_user_id, phrase)
            )
        else:
            self._users_db_cursor.execute(
                '''UPDATE discord_users SET phrase = ?, verification_status = 'AWAITING_MESSAGE', phrase_gen_date = ?
                WHERE discord_user_id = ?''',
                (phrase, self.today_date(), discord_user_id)
            )
        self._users_db.commit()
        return phrase

    def add_reddit_user(self, reddit_username: str):
        """Adds the given Reddit user to the database."""
        if self.reddit_user_info(reddit_username)['reddit_first_contact_date'] is None:
            self._users_db_cursor.execute(
                'INSERT INTO reddit_users(reddit_username) VALUES(?)', (reddit_username,)
            )
            self._users_db.commit()
            return self.reddit_user_info(reddit_username)
        else:
            return None

    def verify_user(self, reddit_username: str, phrase: str):
        """Assigns a Reddit username to a Discord user. Also unassigns the phrase."""
        if self.phrase_info(phrase)['discord_user_id'] is not None:
            if self.reddit_user_info(reddit_username)['discord_user_id'] is None:
                self._users_db_cursor.execute(
                    '''UPDATE discord_users SET reddit_username = ?, verification_status = 'VERIFIED_NOT_NOTIFIED',
                    verification_rejection_date = ?, phrase = NULL WHERE phrase = ?''',
                    (reddit_username, self.today_date(), phrase)
                )
                self._users_db.commit()
            return self.reddit_user_info(reddit_username)
        else:
            return None

    def reject_user(self, reddit_username: str, phrase: str, reason: str):
        """Assigns a Reddit username to a Discord user. Also unassigns the phrase."""
        if self.phrase_info(phrase)['discord_user_id'] is not None:
            if self.reddit_user_info(reddit_username)['discord_user_id'] is None:
                new_verification_status = f'REJECTED_{reason}'
                self._users_db_cursor.execute(
                    f'''UPDATE discord_users SET verification_status = ?,
                    verification_rejection_date = ?, phrase = NULL WHERE phrase = ?''',
                    (new_verification_status, self.today_date(), phrase)
                )
                self._users_db.commit()
            return self.reddit_user_info(reddit_username)
        else:
            return None

    def update_discord_user_verification_status(self, discord_user_id: int, new_verification_status: str):
        if self.discord_user_info(discord_user_id)['verification_status'] is not None:
            self._users_db_cursor.execute(
                '''UPDATE discord_users SET verification_status = ? WHERE discord_user_id = ?''',
                (new_verification_status, discord_user_id)
            )
            self._users_db.commit()
        return self.discord_user_info(discord_user_id)


class RedditVerificationMessageScout:
    _reddit = None
    _verifier = None
    _users_db_path = None

    class MessageRetrievalFailure(praw.exceptions.APIException):
        """Raised when messages could not be retrieved from Reddit."""
        pass

    def __init__(self, users_db_path):
        self._users_db_path = users_db_path
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        self._reddit = praw.Reddit(
            client_id=somsiad.conf['reddit_id'],
            client_secret=somsiad.conf['reddit_secret'],
            username=somsiad.conf['reddit_username'],
            password=somsiad.conf['reddit_password'],
            user_agent=somsiad.user_agent
        )
        self._verifier = RedditVerifier(self._users_db_path)

        while True:
            try:
                self.process_messages()
            except self.MessageRetrievalFailure:
                somsiad.logger.warning(
                    'Something went wrong while trying to process Reddit verification messages! Trying again...'
                )

    def process_messages(self):
        """Processes new messages from the inbox stream and uses them for verification."""
        # Handle each new message
        for message in praw.models.util.stream_generator(self._reddit.inbox.unread):
            if message.subject == 'Weryfikacja':
                # Check if (and when) Reddit account was verified
                phrase = message.body.strip().strip('"\'')
                reddit_username = str(message.author)
                reddit_user_info = self._verifier.reddit_user_info(str(message.author))
                self._verifier.add_reddit_user(reddit_username)
                if reddit_user_info['discord_user_id'] is None:
                    # Check if the phrase is in the database

                    if self._verifier.phrase_info(phrase)['discord_user_id'] is None:
                        message.reply(
                            'Weryfikacja nie powiodła się. Wysłana fraza nie odpowiada żadnemu użytkownikowi.'
                        )

                    else:
                        # Check if the phrase was sent the same day it was generated
                        message_sent_day = time.strftime('%Y-%m-%d', time.localtime(message.created_utc))

                        if message_sent_day == self._verifier.phrase_info(phrase)['phrase_gen_date']:
                            if self._verifier.is_reddit_user_trustworthy(message.author):
                                # If the phrase was indeed sent the same day it was generated
                                # and the user seems to be trustworthy,
                                # assign the Reddit username to the Discord user whose secret phrase this was
                                verification = self._verifier.verify_user(reddit_username, phrase)
                                if verification is not None:
                                    discord_user_id = verification['discord_user_id']
                                    discord_user = somsiad.client.get_user(discord_user_id)
                                    message.reply(
                                        f'Pomyślnie zweryfikowano! Przypisano to konto do użytkownika Discorda '
                                        f'{discord_user}.'
                                    )
                                    self._verifier.update_discord_user_verification_status(
                                        discord_user_id, 'VERIFIED_NOTIFIED'
                                    )
                            else:
                                self._verifier.reject_user(reddit_username, phrase, 'NOT_TRUSTWORTHY')
                                account_min_age_days = int(somsiad.conf['reddit_account_min_age_days'])
                                message.reply(
                                    'Weryfikacja nie powiodła się. Twoje konto na Reddicie nie spełnia wymagań. '
                                    f'Do weryfikacji potrzebne jest konto założone co najmniej {account_min_age_days} '
                                    f'{TextFormatter.noun_variant(account_min_age_days, "dzień", "dni")} temu '
                                    f'i o karmie nie niższej niż {somsiad.conf["reddit_account_min_karma"]}.'
                                )

                        else:
                            self._verifier.reject_user(reddit_username, phrase, 'PHRASE_EXPIRED')
                            message.reply(
                                'Weryfikacja nie powiodła się. Wysłana fraza wygasła. Wygeneruj nową frazę '
                                'na Discordzie.'
                            )

                else:
                    discord_user_id = self._verifier.reddit_user_info(reddit_username)['discord_user_id']
                    discord_user = somsiad.client.get_user(discord_user_id)
                    message.reply(
                        f'To konto zostało przypisane do użytkownika Discorda {discord_user} '
                        f'{reddit_user_info["verification_rejection_date"]}.'
                    )

            message.mark_read()


phrase_parts_file_path = os.path.join(somsiad.bot_dir_path, 'data', 'reddit_verification_phrase_parts.json')
users_db_path = os.path.join(somsiad.storage_dir_path, 'reddit_verification.db')


# Load phrase parts
with open(phrase_parts_file_path, 'r') as f:
    phrase_parts = json.load(f)


verifier = RedditVerifier(users_db_path, phrase_parts)


@somsiad.client.command(aliases=['zweryfikuj'])
@discord.ext.commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], discord.ext.commands.BucketType.user)
async def reddit_verify(ctx, *args):
    """Verifies Discord user via Reddit."""
    FOOTER_TEXT = 'Reddit - weryfikacja'

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
        if discord_user_info['phrase_gen_date'] == verifier.today_date():
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
                    value='Do weryfikacji potrzebne jest konto założone co najmniej '
                        f'{somsiad.conf["reddit_account_min_age_days"]} '
                        f'{TextFormatter.noun_variant(somsiad.conf["reddit_account_min_age_days"], "dzień", "dni")} '
                        f'temu i o karmie nie niższej niż {somsiad.conf["reddit_account_min_karma"]}. '
                        'Spróbuj zweryfikować się, gdy już będziesz spełniał te warunki.'
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

    elif str(discord_user_info['verification_status']).startswith('VERIFIED'):
        embed = discord.Embed(title='Już jesteś zweryfikowany', color=somsiad.color)
        embed.add_field(
            name=f'Twoje konto na Reddicie to /u/{discord_user_info["reddit_username"]}.',
            value=f'Zweryfikowano {discord_user_info["verification_rejection_date"]}.'
        )
    else:
        embed = discord.Embed(
            title='Wystąpił błąd podczas sprawdzania twojego statusu weryfikacji', color=somsiad.color
        )

    embed.set_footer(text=FOOTER_TEXT)
    await ctx.author.send(embed=embed)


@somsiad.client.command(aliases=['prześwietl', 'przeswietl'])
@discord.ext.commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], discord.ext.commands.BucketType.user)
@discord.ext.commands.guild_only()
async def reddit_xray(ctx, *args):
    """Checks given user's verification status.
    If no user was given, assumes message author.
    If @here or @everyone mentions were given, returns a list of verified members of, respectively,
    the channel or the server.
    """
    FOOTER_TEXT = 'Reddit - weryfikacja'

    if (len(args) == 1 and args[0].strip('\\') == '@everyone' and
            somsiad.does_member_have_elevated_permissions(ctx.author)):
        embed = discord.Embed(
            title='Zweryfikowani użytkownicy na tym serwerze',
            color=somsiad.color
        )
        for member in ctx.guild.members:
            discord_user_info = verifier.discord_user_info(member.id)
            if str(discord_user_info['verification_status']).startswith('VERIFIED'):
                embed.add_field(
                    name=str(member),
                    value=f'/u/{discord_user_info["reddit_username"]}',
                    inline=False
                )

    elif (len(args) == 1 and args[0].strip('\\') == '@here' and
            somsiad.does_member_have_elevated_permissions(ctx.author)):
        embed = discord.Embed(
            title='Zweryfikowani użytkownicy na tym kanale',
            color=somsiad.color
        )
        for member in ctx.channel.members:
            discord_user_info = verifier.discord_user_info(member.id)
            if str(discord_user_info['verification_status']).startswith('VERIFIED'):
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
            if str(discord_user_info['verification_status']).startswith('VERIFIED'):
                reddit_username_info = ''
                if somsiad.does_member_have_elevated_permissions(ctx.author):
                    reddit_username_info = (f' jako [/u/{discord_user_info["reddit_username"]}]'
                    f'(https://www.reddit.com/user/{discord_user_info["reddit_username"]})')
                embed = discord.Embed(
                    title=':white_check_mark: Zweryfikowany',
                    description=f'Użytkownik {discord_user} został zweryfikowany '
                    f'{discord_user_info["verification_rejection_date"]}'
                    f'{reddit_username_info}.',
                    color=somsiad.color
                )
            elif str(discord_user_info['verification_status']) == 'REJECTED_NOT_TRUSTWORTHY':
                embed = discord.Embed(
                    title=':red_circle: Niezweryfikowany',
                    description=f'Użytkownik {discord_user} zażądał ostatnio weryfikacji '
                    f'{discord_user_info["phrase_gen_date"]} i spróbował się zweryfikować '
                    f'{discord_user_info["verification_rejection_date"]}, lecz jego konto nie spełniało wymagań.',
                    color=somsiad.color
                )
            elif str(discord_user_info['verification_status']) == 'REJECTED_PHRASE_EXPIRED':
                embed = discord.Embed(
                    title=':red_circle: Niezweryfikowany',
                    description=f'Użytkownik {discord_user} zażądał ostatnio weryfikacji '
                    f'{discord_user_info["phrase_gen_date"]}, ale nie dokończył jej na Reddicie w wyznaczonym czasie '
                    f'- wysłał wiadomość {discord_user_info["verification_rejection_date"]}.',
                    color=somsiad.color
                )
            elif str(discord_user_info['verification_status']) == 'AWAITING_MESSAGE':
                embed = discord.Embed(
                    title=':red_circle: Niezweryfikowany',
                    description=f'Użytkownik {discord_user} zażądał ostatnio weryfikacji '
                    f'{discord_user_info["phrase_gen_date"]}, ale nie dokończył jej na Reddicie.',
                    color=somsiad.color
                )
            else:
                embed = discord.Embed(
                    title=':warning: Błąd',
                    color=somsiad.color
                )


    embed.set_footer(text=FOOTER_TEXT)
    await ctx.send(ctx.author.mention, embed=embed)


@reddit_xray.error
async def reddit_xray_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadArgument):
        FOOTER_TEXT = 'Reddit - weryfikacja'

        embed = discord.Embed(
            title=':warning: Błąd',
            description=f'Podany użytkownik nie znajduje się na tym serwerze.',
            color=somsiad.color
        )
        embed.set_footer(text=FOOTER_TEXT)

        await ctx.send(ctx.author.mention, embed=embed)


reddit_verification_message_scout = RedditVerificationMessageScout(users_db_path)
