import logging
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

reddit = praw.Reddit(client_id=conf['reddit_id'], client_secret=conf['reddit_secret'],
    username=conf['reddit_username'], password=conf['reddit_password'], user_agent=f'SomsiadBot/{__version__}')

parts_file_path = os.path.join(bot_dir, 'data', 'reddit_verification_parts.json')
database_path = os.path.join(bot_dir, 'data', 'reddit_verification.db')

# Load phrase parts
with open(parts_file_path, 'r') as parts_file:
    parts = json.load(parts_file)

# Connect to the database, create a table if it doesn't exist yet
users_db = sqlite3.connect(database_path)
users_cursor = users_db.cursor()
users_cursor.execute("""CREATE TABLE IF NOT EXISTS reddit_verification_users(discord_username TEXT PRIMARY KEY,
    phrase TEXT UNIQUE, phrase_gen_date DATE DEFAULT (date('now', 'localtime')),
    reddit_username TEXT UNIQUE)""")
users_db.commit()

def phrase_gen():
    """Assembles a random phrase from given parts."""
    phrase = ''
    for _, category in parts.items():
        phrase += secrets.choice(category).capitalize()
    return phrase

def is_Reddit_user_trustworthy(reddit_user):
    """Checks if given Reddit user seems trustworthy."""
    account_karma = reddit_user.link_karma + reddit_user.comment_karma
    account_age_days = (time.time() - reddit_user.created_utc) / 86400
    if (account_age_days >= float(conf['reddit_account_min_age_days']) and
        account_karma >= int(conf['reddit_account_min_karma'])):
        return True
    else:
        return False

@client.command(aliases=['zweryfikuj'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
async def redditverify(ctx, *args):
    """Verifies Discord user via Reddit."""
    discord_username = str(ctx.author)
    # Check if (and when) user has already been verified
    users_cursor.execute('SELECT reddit_username FROM reddit_verification_users WHERE discord_username = ?',
        (discord_username,))
    reddit_username = users_cursor.fetchone()

    users_cursor.execute('SELECT phrase_gen_date FROM reddit_verification_users WHERE discord_username = ?',
        (discord_username,))
    phrase_gen_date = users_cursor.fetchone()

    if reddit_username is None or reddit_username[0] is None:
        # If user is not verified, check if he has ever requested verification
        today_date = str(datetime.date.today())

        if phrase_gen_date is None:
            # If user has never requested verification, add him to the database and assign a phrase to him
            phrase = phrase_gen()

            users_cursor.execute('INSERT INTO reddit_verification_users(discord_username, phrase) VALUES(?, ?)',
                (discord_username, phrase,))
            users_db.commit()

            message_url = ('https://www.reddit.com/message/compose/'
                f'?to={conf["reddit_username"]}&subject=Weryfikacja&message={phrase}')

            embed = discord.Embed(title='Dokończ weryfikację na Reddicie', color=brand_color)
            embed.add_field(name='Wygenerowano tajną frazę', value='By zweryfikować się '
                f'wyślij /u/{conf["reddit_username"]} wiadomość o temacie "Weryfikacja" i treści "{phrase}". '
                'Fraza ważna jest do końca dnia.')
            embed.add_field(name='Najlepiej skorzystaj z linku:', value=message_url)

            await ctx.author.send(embed=embed)

        elif phrase_gen_date[0] == today_date:
            # If user already has requested verification today, fend him off
            embed = discord.Embed(title='Już zażądałeś dziś weryfikacji', color=brand_color)
            embed.add_field(name='Sprawdź historię wiadomości', value='Wygenerowana fraza ważna jest do końca dnia.')
            await ctx.author.send(embed=embed)

        else:
            # If user has requested verification but not today, assign him a new phrase
            phrase = phrase_gen()

            users_cursor.execute("""UPDATE reddit_verification_users SET phrase = ?, phrase_gen_date = ?
                WHERE discord_username = ?""", (phrase, today_date, discord_username,))
            users_db.commit()

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
        embed.add_field(name=f'Twoje konto na Reddicie to /u/{reddit_username[0]}',
            value=f'Zweryfikowano {phrase_gen_date[0]}.')

        await ctx.author.send(embed=embed)

@client.command(aliases=['prześwietl'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def redditcheck(ctx, *args):
    """Checks given user's verification status."""
    # If no user was given assume message author
    if len(args) == 0:
        discord_username = str(ctx.author)

    else:
        if len(args) == 1 and args[0].startswith('<@') and args[0].endswith('>'):
            # If user was mentioned convert his ID to a username and then check if he is a member of the server
            raw_discord_username = str(await client.get_user_info(int(args[0].strip('<@!>'))))
        else:
            # Otherwise autofill user's tag (number) and check if he is a member of the server
            raw_discord_username = ''
            for arg in args:
                raw_discord_username += arg + ' '
            raw_discord_username = raw_discord_username.strip()

        discord_username = ctx.message.guild.get_member_named(raw_discord_username)

    embed = discord.Embed(title='Wynik prześwietlenia', color=brand_color)

    if discord_username is None:
        embed.add_field(name=':warning: Błąd', value=f'Użytkownik {raw_discord_username} nie znajduje się na tym '
            'serwerze.')
        await ctx.send(embed=embed)

    else:
        discord_username = str(discord_username)
        # Check if (and when) user has already been verified
        users_cursor.execute('SELECT phrase_gen_date FROM reddit_verification_users WHERE discord_username = ?',
            (discord_username,))
        phrase_gen_date = users_cursor.fetchone()

        if phrase_gen_date is None:
            embed.add_field(name=':red_circle: Niezweryfikowany',
                value=f'Użytkownik {discord_username} nigdy nie zażądał weryfikacji.')
            await ctx.send(embed=embed)

        else:
            users_cursor.execute('SELECT reddit_username FROM reddit_verification_users WHERE discord_username = ?',
                (discord_username,))
            reddit_username = users_cursor.fetchone()
            if reddit_username[0] is None:
                embed.add_field(name=':red_circle: Niezweryfikowany',
                    value=f'Użytkownik {discord_username} zażądał weryfikacji {phrase_gen_date[0]}, '
                    'ale nie dokończył jej na Reddicie.')
                await ctx.send(embed=embed)
            else:
                embed.add_field(name=':white_check_mark: Zweryfikowany',
                    value=f'Użytkownik {discord_username} został zweryfikowany {phrase_gen_date[0]} jako '
                    f'/u/{reddit_username[0]}.')
                await ctx.send(embed=embed)

class RedditMessageWatch:

    def __init__(self):
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    @staticmethod
    def run():
        """Processes new messages from the inbox stream and uses them for verification."""

        # Connect to the database (this must be done a second time because this is a new thread)
        users_db_watch = sqlite3.connect(database_path)
        users_cursor_watch = users_db_watch.cursor()

        # Handle each new message
        for message in praw.models.util.stream_generator(reddit.inbox.unread):
            if message.subject == 'Weryfikacja':
                # Check if (and when) Reddit account was verified
                phrase = message.body.strip().strip('"\'')
                users_cursor_watch.execute("""SELECT phrase_gen_date FROM reddit_verification_users
                    WHERE reddit_username = ?""", (str(message.author),))
                phrase_gen_date = users_cursor_watch.fetchone()

                if phrase_gen_date is None:
                    # Check if the phrase is in the database
                    users_cursor_watch.execute("""SELECT phrase_gen_date FROM reddit_verification_users
                        WHERE phrase = ?""", (phrase,))
                    phrase_gen_date = users_cursor_watch.fetchone()

                    if phrase_gen_date is None:
                        message.reply('Weryfikacja nie powiodła się. Wysłana fraza nie odpowiada żadnemu '
                            'użytkownikowi.')

                    else:
                        # Check if the phrase was sent the same day it was generated
                        message_sent_day = time.strftime('%Y-%m-%d', time.localtime(message.created_utc))

                        if message_sent_day == phrase_gen_date[0]:
                            if is_Reddit_user_trustworthy(message.author):
                                # If the phrase was indeed sent the same day it was generated,
                                # assign the Reddit username to the Discord user whose secret phrase this was
                                users_cursor_watch.execute("""SELECT discord_username FROM reddit_verification_users
                                    WHERE phrase = ?""", (phrase,))
                                discord_username = users_cursor_watch.fetchone()[0]

                                users_cursor_watch.execute("""UPDATE reddit_verification_users SET reddit_username = ?,
                                    phrase = NULL WHERE phrase = ?""", (str(message.author), phrase,))
                                users_db_watch.commit()

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
                    message.reply(f'To konto zostało zweryfikowane {phrase_gen_date[0]}.')

            message.mark_read()

reddit_message_watch = RedditMessageWatch()
