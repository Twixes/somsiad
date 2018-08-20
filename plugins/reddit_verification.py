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
from discord.ext import commands
import praw
from version import __version__
from somsiad_helper import *

class RedditVerificator:
    reddit = None
    users_db = None
    user_db_cursor = None
    parts = None

    def __init__(self, reddit, users_db_path, parts=None):
        """Connects to the database. Creates it if it doesn't yet. Sets up parts."""
        self.reddit = reddit
        self.users_db = sqlite3.connect(users_db_path)
        self.users_db_cursor = self.users_db.cursor()
        self.users_db_cursor.execute("""CREATE TABLE IF NOT EXISTS reddit_verification_users(
            discord_username TEXT PRIMARY KEY, phrase TEXT UNIQUE, phrase_gen_date DATE DEFAULT (date('now',
            'localtime')), reddit_username TEXT UNIQUE)""")
        self.users_db.commit()
        self.parts = parts

    @staticmethod
    def is_reddit_user_trustworthy(reddit_user):
        """Checks if given Reddit user seems trustworthy."""
        account_karma = reddit_user.link_karma + reddit_user.comment_karma
        account_age_days = (time.time() - reddit_user.created_utc) / 86400
        if (account_age_days >= float(conf['reddit_account_min_age_days']) and
            account_karma >= int(conf['reddit_account_min_karma'])):
            return True
        else:
            return False

    def phrase_gen(self):
        """Assembles a unique random phrase from given parts."""
        is_phrase_unique = False
        while not is_phrase_unique:
            phrase = ''
            for _, category_entry in self.parts.items():
                phrase += secrets.choice(category_entry).capitalize()
            if self.phrase_status(phrase)['discord_username'] is None:
                is_phrase_unique = True
        return phrase

    def phrase_status(self, phrase):
        """Returns given phrase's status."""
        self.users_db_cursor.execute('''SELECT discord_username FROM reddit_verification_users
            WHERE phrase = ?''', (phrase,))
        discord_username = self.users_db_cursor.fetchone()
        if discord_username is None:
            return {'discord_username': None, 'phrase_gen_date': None}
        else:
            discord_username = discord_username[0]
            self.users_db_cursor.execute('''SELECT phrase_gen_date FROM reddit_verification_users
                WHERE phrase = ?''', (phrase,))
            phrase_gen_date = self.users_db_cursor.fetchone()[0]
            return {'discord_username': discord_username, 'phrase_gen_date': phrase_gen_date}

    def discord_user_status(self, discord_user):
        """Returns given Discord user's status."""
        if discord_user is None:
            return {'phrase_gen_date': None, 'reddit_username': None}

        else:
            discord_username = str(discord_user)
            # Check if (and when) user has already been verified
            self.users_db_cursor.execute('''SELECT phrase_gen_date FROM reddit_verification_users
                WHERE discord_username = ?''', (discord_username,))
            phrase_gen_date = self.users_db_cursor.fetchone()

            if phrase_gen_date is None:
                return {'phrase_gen_date': None, 'reddit_username': None}

            else:
                self.users_db_cursor.execute('''SELECT reddit_username FROM reddit_verification_users
                    WHERE discord_username = ?''', (discord_username,))
                reddit_username = self.users_db_cursor.fetchone()
                return {'phrase_gen_date': phrase_gen_date[0],
                    'reddit_username': reddit_username[0]}

    def reddit_user_status(self, reddit_username):
        """Returns given Reddit user's status."""
        self.users_db_cursor.execute('''SELECT discord_username FROM reddit_verification_users
            WHERE reddit_username = ?''', (reddit_username,))
        discord_username = self.users_db_cursor.fetchone()
        self.users_db_cursor.execute('''SELECT phrase_gen_date FROM reddit_verification_users
            WHERE reddit_username = ?''', (reddit_username,))
        phrase_gen_date = self.users_db_cursor.fetchone()

        return {'discord_username': discord_username, 'phrase_gen_date': phrase_gen_date}

    def assign_phrase(self, discord_username):
        """Assigns a phrase to a Discord user."""
        phrase = self.phrase_gen()

        if self.discord_user_status(discord_username)['phrase_gen_date'] is None:
            self.users_db_cursor.execute('INSERT INTO reddit_verification_users(discord_username, phrase) VALUES(?, ?)',
                (discord_username, phrase,))
        else:
            today_date = str(datetime.date.today())
            self.users_db_cursor.execute('''UPDATE reddit_verification_users SET phrase = ?, phrase_gen_date = ?
                WHERE discord_username = ?''', (phrase, today_date, discord_username,))
        self.users_db.commit()
        return phrase

    def assign_reddit_username_by_phrase(self, phrase, reddit_username):
        """Assigns a Reddit username to a Discord user. Also unassigns the phrase."""
        user_status = self.reddit_user_status(reddit_username)

        if self.phrase_status(phrase)['discord_username'] is not None:
            if user_status['discord_username'] is None:
                self.users_db_cursor.execute('''UPDATE reddit_verification_users SET reddit_username = ?,
                    phrase = NULL WHERE phrase = ?''', (reddit_username, phrase,))
                self.users_db.commit()
            return self.reddit_user_status(reddit_username)
        else:
            return None

class RedditVerificatorMessageWatch:
    reddit = None
    watch_verificator = None

    def __init__(self, reddit):
        self.reddit = reddit
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        """Processes new messages from the inbox stream and uses them for verification."""
        # Handle each new message
        self.watch_verificator = RedditVerificator(self.reddit, users_db_path)
        for message in praw.models.util.stream_generator(self.reddit.inbox.unread):
            if message.subject == 'Weryfikacja':
                # Check if (and when) Reddit account was verified
                phrase = message.body.strip().strip('"\'')
                reddit_username = str(message.author)
                user_status = self.watch_verificator.reddit_user_status(str(message.author))

                if user_status['discord_username'] is None:
                    # Check if the phrase is in the database

                    if self.watch_verificator.phrase_status(phrase)['discord_username'] is None:
                        message.reply('Weryfikacja nie powiodła się. Wysłana fraza nie odpowiada żadnemu '
                            'użytkownikowi.')

                    else:
                        # Check if the phrase was sent the same day it was generated
                        message_sent_day = time.strftime('%Y-%m-%d', time.localtime(message.created_utc))

                        if message_sent_day == self.watch_verificator.phrase_status(phrase)['phrase_gen_date']:
                            if self.watch_verificator.is_reddit_user_trustworthy(message.author):
                                # If the phrase was indeed sent the same day it was generated
                                # and the user seems to be trustworthy,
                                # assign the Reddit username to the Discord user whose secret phrase this was
                                discord_username = (self.watch_verificator.assign_reddit_username_by_phrase(phrase,
                                    reddit_username)['discord_username'][0])
                                message.reply(f'Pomyślnie zweryfikowano! Przypisano to konto do użytkownika Discorda '
                                    f'{discord_username}.')

                            else:
                                day_noun_variant = 'dzień' if int(conf['reddit_account_min_age_days']) == 1 else 'dni'
                                message.reply('Weryfikacja nie powiodła się. Twoje konto na Reddicie nie spełnia '
                                    'wymagań. Do weryfikacji potrzebne jest konto założone co najmniej '
                                    f'{conf["reddit_account_min_age_days"]} {day_noun_variant} temu i o karmie '
                                    f'nie niższej niż {conf["reddit_account_min_karma"]}.')

                        else:
                            message.reply('Weryfikacja nie powiodła się. Wysłana fraza wygasła. Wygeneruj nową frazę '
                                'na Discordzie.')

                else:
                    message.reply('To konto zostało przypisane do użytkownika Discorda '
                        f'{user_status["discord_username"][0]} '
                        f'{user_status["phrase_gen_date"][0]}.')

            message.mark_read()

reddit = praw.Reddit(client_id=conf['reddit_id'], client_secret=conf['reddit_secret'],
    username=conf['reddit_username'], password=conf['reddit_password'], user_agent=user_agent)

parts_file_path = os.path.join(bot_dir_path, 'data', 'reddit_verification_parts.json')
users_db_path = os.path.join(conf_dir_path, 'reddit_verification.db')

# Load phrase parts
with open(parts_file_path, 'r') as parts_file:
    parts = json.load(parts_file)

verificator = RedditVerificator(reddit, users_db_path, parts)

@client.command(aliases=['zweryfikuj'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
async def redditverify(ctx, *args):
    """Verifies Discord user via Reddit."""
    discord_username = str(ctx.author)

    user_status = verificator.discord_user_status(discord_username)

    if user_status['reddit_username'] is None:
        # If user is not verified, check if he has ever requested verification
        today_date = str(datetime.date.today())

        if user_status['phrase_gen_date'] is None:
            # If user has never requested verification, add him to the database and assign a phrase to him
            phrase = verificator.assign_phrase(discord_username)

            message_url = ('https://www.reddit.com/message/compose/'
                f'?to={conf["reddit_username"]}&subject=Weryfikacja&message={phrase}')

            embed = discord.Embed(title='Dokończ weryfikację na Reddicie', color=brand_color)
            embed.add_field(name='Wygenerowano tajną frazę', value='By zweryfikować się '
                f'wyślij /u/{conf["reddit_username"]} wiadomość o temacie "Weryfikacja" i treści "{phrase}". '
                'Fraza ważna jest do końca dnia.')
            embed.add_field(name='Najlepiej skorzystaj z linku:', value=message_url)

            await ctx.author.send(embed=embed)

        elif user_status['phrase_gen_date'] == today_date:
            # If user already has requested verification today, fend him off
            embed = discord.Embed(title='Już zażądałeś dziś weryfikacji', color=brand_color)
            embed.add_field(name='Sprawdź historię wiadomości', value='Wygenerowana fraza ważna jest do końca dnia.')
            await ctx.author.send(embed=embed)

        else:
            # If user has requested verification but not today, assign him a new phrase
            phrase = verificator.assign_phrase(discord_username)

            message_url = ('https://www.reddit.com/message/compose/'
                f'?to={conf["reddit_username"]}&subject=Weryfikacja&message={phrase}')

            embed = discord.Embed(title='Dokończ weryfikację na Reddicie', color=brand_color)
            embed.add_field(name='Wygenerowano tajną frazę', value='By zweryfikować się '
                f'wyślij /u/{conf["reddit_username"]} wiadomość o temacie "Weryfikacja" i treści "{phrase}". '
                'Fraza ważna jest do końca dnia.')
            embed.add_field(name='Najlepiej skorzystaj z linku:', value=message_url)

            await ctx.author.send(embed=embed)
    else:
        embed = discord.Embed(title='Już jesteś zweryfikowany', color=brand_color)
        embed.add_field(name=f'Twoje konto na Reddicie to /u/{user_status["reddit_username"]}',
            value=f'Zweryfikowano {user_status["phrase_gen_date"]}.')

        await ctx.author.send(embed=embed)

@client.command(aliases=['prześwietl', 'przeswietl'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def redditxray(ctx, *args):
    """Checks given user's verification status."""
    # If no user was given assume message author
    embed = discord.Embed(title='Wynik prześwietlenia', color=brand_color)

    if len(args) == 1 and args[0] == '@everyone' and does_member_have_elevated_permissions(ctx.author):
        for member in ctx.guild.members:
            user_status = verificator.discord_user_status(member)
            if user_status['reddit_username'] is not None:
                embed.add_field(name=str(member), value=f'/u/{user_status["reddit_username"]}',
                    inline=False)
        await ctx.send(embed=embed)

    elif len(args) == 1 and args[0] == '@here' and does_member_have_elevated_permissions(ctx.author):
        for member in ctx.channel.members:
            user_status = verificator.discord_user_status(member)
            if user_status['reddit_username'] is not None:
                embed.add_field(name=str(member), value=f'/u/{user_status["reddit_username"]}',
                    inline=False)
        await ctx.send(embed=embed)

    else:
        if len(args) == 0:
            discord_user = ctx.author
            discord_username = str(discord_user)

        else:
            if len(args) == 1 and args[0].startswith('<@') and args[0].endswith('>'):
                # If user was mentioned convert his ID to a username and then check if he is a member of the server
                discord_username = str(await client.get_user_info(int(args[0].strip('<@!>'))))
            else:
                # Otherwise autofill user's tag (number) and check if he is a member of the server
                discord_username = ''.join(args)

            discord_user = ctx.message.guild.get_member_named(discord_username)

        user_status = verificator.discord_user_status(discord_user)

        if discord_user is not None:
            discord_username = str(discord_user)
            # Check if (and when) user has already been verified
            if user_status['phrase_gen_date'] is None:
                embed.add_field(name=':red_circle: Niezweryfikowany',
                    value=f'Użytkownik {discord_username} nigdy nie zażądał weryfikacji.')
                await ctx.send(embed=embed)

            else:
                if user_status['reddit_username'] is None:
                    embed.add_field(name=':red_circle: Niezweryfikowany',
                        value=f'Użytkownik {discord_username} zażądał weryfikacji '
                        f'{user_status["phrase_gen_date"]}, '
                        'ale nie dokończył jej na Reddicie.')
                    await ctx.send(embed=embed)
                else:
                    reddit_username_info = ''
                    if does_member_have_elevated_permissions(ctx.author):
                        reddit_username_info = f' jako /u/{user_status["reddit_username"]}'
                    embed.add_field(name=':white_check_mark: Zweryfikowany',
                        value=f'Użytkownik {discord_username} został zweryfikowany '
                        f'{user_status["phrase_gen_date"]}{reddit_username_info}.')
                    await ctx.send(embed=embed)

        else:
            embed.add_field(name=':warning: Błąd', value=f'Użytkownik {discord_username} nie znajduje się na tym '
                'serwerze.')
            await ctx.send(embed=embed)

reddit_verificator_message_watch = RedditVerificatorMessageWatch(reddit)
