import logging
import os.path
import time
import datetime
import secrets
import threading
import json
import sqlite3
from string import whitespace
import discord
from discord.ext import commands
import praw
from somsiad_helper import *
from version import __version__

reddit = praw.Reddit(client_id=conf['reddit_id'], client_secret=conf['reddit_secret'],
    username=conf['reddit_username'], password=conf['reddit_password'], user_agent=f'SomsiadBot/{__version__}')

parts_file_path = os.path.join(bot_dir, 'data', 'reddit_verification_parts.json')

# Load phrase parts
with open(parts_file_path, 'r') as parts_file:
    parts = json.load(parts_file)

# Connect to the database, create a table if it doesn't exist yet
users_db = sqlite3.connect('data/reddit_verification_users.db')
users_cursor = users_db.cursor()
users_cursor.execute('''CREATE TABLE IF NOT EXISTS reddit_verification_users(discord_username TEXT PRIMARY KEY,
    phrase TEXT UNIQUE, phrase_gen_date DATE DEFAULT (date('now', 'localtime')),
    reddit_username TEXT UNIQUE)''')
users_db.commit()

def phrase_gen():
    '''Assembles a random phrase from given parts'''
    phrase = ''
    for _, category in parts.items():
        phrase += secrets.choice(category).capitalize()
    return phrase

@client.command(aliases=['zweryfikuj'])
@commands.cooldown(1, conf['user_command_cooldown'], commands.BucketType.user)
async def reddit_verification(ctx, *args):
    '''Verifies user's Reddit account'''
    discord_username = str(ctx.author)
    # Check if (and when) user has already been verified
    users_cursor.execute('SELECT reddit_username FROM reddit_verification_users WHERE discord_username = ?',
        (discord_username,))
    reddit_username = users_cursor.fetchone()

    users_cursor.execute('SELECT phrase_gen_date FROM reddit_verification_users WHERE discord_username = ?',
        (discord_username,))
    phrase_gen_date = users_cursor.fetchone()

    if reddit_username is None:
        # If user is not verified, check if he has ever requested verification
        today_date = str(datetime.date.today())

        if phrase_gen_date is None:
            # If user has never requested verification, add him to the database and assign a phrase to him
            phrase = phrase_gen()

            users_cursor.execute('INSERT INTO reddit_verification_users(discord_username, phrase) VALUES(?, ?)',
                (discord_username, phrase,))
            users_db.commit()

            message_url = f'https://www.reddit.com/message/compose/?to=SomsiadBot&subject=Weryfikacja&message={phrase}'

            em = discord.Embed(title='Dokończ weryfikację na Reddicie.', color=brand_color)
            em.add_field(name=f'Wygenerowano tajną frazę', value=f'By zweryfikować się'
                ' wyślij /u/{conf["reddit_username"]} wiadomość o temacie "Weryfikacja" i treści "{phrase}".'
                ' Fraza jest ważna do końca dnia.')
            em.add_field(name='Najlepiej skorzystaj z linku:', value=message_url)

            await ctx.author.send(embed=em)

        elif phrase_gen_date[0] == today_date:
            # If user already has requested verification today, fend him off
            em = discord.Embed(title='Już rozpocząłeś proces weryfikacji.', color=brand_color)
            em.add_field(name='Sprawdź historię wiadomości', value='Wygenerowana fraza ważna jest do końca dnia.')
            await ctx.author.send(embed=em)

        else:
            # If user has requested verification but not today, assign him a new phrase
            phrase = phrase_gen()

            users_cursor.execute('''UPDATE reddit_verification_users SET phrase = ?, phrase_gen_date = ?
                WHERE discord_username = ?''', (phrase, today_date, discord_username,))
            users_db.commit()

            message_url = f'https://www.reddit.com/message/compose/?to=SomsiadBot&subject=Weryfikacja&message={phrase}'

            em = discord.Embed(title='Dokończ weryfikację na Reddicie.', color=brand_color)
            em.add_field(name=f'Wygenerowano tajną frazę', value=f'By zweryfikować się'
                ' wyślij /u/{conf["reddit_username"]} wiadomość o temacie "Weryfikacja" i treści "{phrase}".'
                ' Fraza jest ważna do końca dnia.')
            em.add_field(name='Najlepiej skorzystaj z linku:', value=message_url)

            await ctx.author.send(embed=em)
    else:
        em = discord.Embed(title='Już jesteś zweryfikowany', color=brand_color)
        em.add_field(name=f'Twoje konto na Reddicie to /u/{reddit_username[0]}.',
            value=f'Zweryfikowano {phrase_gen_date[0]}.')

        await ctx.author.send(embed=em)

@client.command(aliases=['zweryfikowany'])
@commands.cooldown(1, conf['user_command_cooldown'], commands.BucketType.user)
@commands.guild_only()
async def reddit_status(ctx, *args):
    '''Checks given user's verification status'''
    # If no user was given assume message author
    if len(args) == 0:
        discord_username = str(ctx.author)

    else:
        if args[0].startswith('<@') and args[0].endswith('>'):
            # If user was mentioned convert his ID to username and then check if he is a member of the server
            discord_username = ctx.message.guild.get_member_named(str(await client.get_user_info(
                args[0].strip('<@!>'))))
        else:
            # Otherwise autofill user's tag (number) and check if he is a member of the server
            discord_username = ctx.message.guild.get_member_named(args[0])

    if discord_username is not None:
        discord_username = str(discord_username)
        # Check if (and when) user has already been verified
        users_cursor.execute('SELECT reddit_username FROM reddit_verification_users WHERE discord_username = ?',
            (discord_username,))
        reddit_username = users_cursor.fetchone()

        users_cursor.execute('SELECT phrase_gen_date FROM reddit_verification_users WHERE discord_username = ?',
            (discord_username,))
        phrase_gen_date = users_cursor.fetchone()

        if phrase_gen_date is None:
            await ctx.send(f'{ctx.author.mention}\n:red_circle: Użytkownik {discord_username} nigdy nie rozpoczął'
                ' procesu weryfikacji.')

        else:
            if reddit_username is None:
                await ctx.send(f'{ctx.author.mention}\n:red_circle: Użytkownik {discord_username} rozpoczął'
                    f' proces weryfikacji {phrase_gen_date[0]}, ale nigdy go nie dokończył.')

            else:
                await ctx.send(f'{ctx.author.mention}\n:white_check_mark: Użytkownik {discord_username}'
                    f' został zweryfikowany {phrase_gen_date[0]} jako /u/{reddit_username[0]}.')
    else:
        await ctx.send(f'{ctx.author.mention}\n:warning: Użytkownik {args[0]} nie znajduje się na tym serwerze.')



class reddit_message_watch(object):

    def __init__(self):
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        '''Checks new messages from inbox stream in the background (in the background is what the new thread is for)'''

        # Connect to the database (this must be done a second time because this is a new thread)
        users_db_watch = sqlite3.connect('data/reddit_verification_users.db')
        users_cursor_watch = users_db_watch.cursor()

        # Handle new message
        for message in praw.models.util.stream_generator(reddit.inbox.unread):

            if message.subject == 'Weryfikacja':

                # Check if (and when) Reddit account was verified
                phrase = message.body.strip(whitespace + '"\'')
                users_cursor_watch.execute('''SELECT phrase_gen_date FROM reddit_verification_users
                    WHERE reddit_username = ?''', (str(message.author),))
                phrase_gen_date = users_cursor_watch.fetchone()

                if phrase_gen_date is None:

                    # Check if phrase is in the database
                    users_cursor_watch.execute('''SELECT phrase_gen_date FROM reddit_verification_users
                        WHERE phrase = ?''', (phrase,))
                    phrase_gen_date = users_cursor_watch.fetchone()

                    if phrase_gen_date is None:
                        message.reply('Weryfikacja nie powiodła się. Wysłana fraza nie odpowiada żadnemu'
                            ' użytkownikowi.')

                    else:
                        # Check if phrase was sent the same day it was generated
                        message_sent_day = time.strftime('%Y-%m-%d', time.localtime(message.created_utc))

                        if message_sent_day == phrase_gen_date[0]:
                            # If phrase was indeed sent the same day it was generated,
                            # assign Reddit username to the Discord user whose secret phrase this was
                            users_cursor_watch.execute('''SELECT discord_username FROM reddit_verification_users
                                WHERE phrase = ?''', (phrase,))
                            discord_username = users_cursor_watch.fetchone()[0]

                            users_cursor_watch.execute('''UPDATE reddit_verification_users SET reddit_username = ?,
                                phrase = NULL WHERE phrase = ?''', (str(message.author), phrase,))
                            users_db_watch.commit()

                            message.reply(f'Pomyślnie zweryfikowano! Przypisano to konto do użytkownika Discorda'
                                f' {discord_username}.')

                        else:
                            message.reply('Weryfikacja nie powiodła się. Wysłana fraza wygasła. Wygeneruj nową frazę na'
                            ' Discordzie.')

                else:
                    message.reply(f'To konto zostało zweryfikowane {phrase_gen_date[0]}.')

            message.mark_read()

reddit_message_watch_thread = reddit_message_watch()
