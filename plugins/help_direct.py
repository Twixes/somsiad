# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from discord.ext import commands
from somsiad_helper import *

@client.command(aliases=['help', 'pomocy'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
async def help_direct(ctx):
    em = discord.Embed(title='Lecem na ratunek!' , color=brand_color)
    em.add_field(name='Dobry!', value='Somsiad jestem. Pomagam w różnych kwestiach, wystarczy mnie zawołać. '
        'Odpowiadam na wszystkie zawołania z poniższej listy. Pamiętaj tylko zawsze, by zacząć od "'
        f'{conf["command_prefix"]}".\nW nawiasach podane są alternatywne nazwy zawołań - tak dla różnorodności.')
    em.add_field(name=f'{conf["command_prefix"]}pomocy (help)', value='Wysyła użytkownikowi tę wiadomość.',
        inline=False)
    em.add_field(name=f'{conf["command_prefix"]}8-ball (8ball, eightball, 8) <pytanie>',
        value='Zadaje <pytanie> magicznej kuli.', inline=False)
    em.add_field(name=f'{conf["command_prefix"]}gugiel (g) <zapytanie>',
        value='Wysyła <zapytanie> do wyszukiwarki Google i zwraca najlepiej pasujący wynik.', inline=False)
    em.add_field(name=f'{conf["command_prefix"]}img (i) <zapytanie>',
        value='Wysyła <zapytanie> do wyszukiwarki Qwant i zwraca najlepiej pasujący do niego obrazek.', inline=False)
    em.add_field(name=f'{conf["command_prefix"]}youtube (yt, tuba) <zapytanie>',
        value='Wysyła <zapytanie> do YouTube i zwraca najlepiej pasujący wynik.', inline=False)
    em.add_field(name=f'{conf["command_prefix"]}wikipediapl (wikipl, wpl) <temat>',
        value='Sprawdza znaczenie <terminu> w polskiej wersji Wikipedii.', inline=False)
    em.add_field(name=f'{conf["command_prefix"]}wikipediaen (wikien, wen) <temat>',
        value='Sprawdza znaczenie <terminu> w anglojęzycznej wersji Wikipedii.', inline=False)
    em.add_field(name=f'{conf["command_prefix"]}urbandictionary (urban) <słowo>',
        value='Sprawdza znaczenie <słowa> w Urban Dictionary.', inline=False)
    em.add_field(name=f'{conf["command_prefix"]}isitup (isup, up) <url>',
        value='Za pomocą serwisu isitup.org wykrywa status danej strony.', inline=False)
    em.add_field(name=f'{conf["command_prefix"]}kantor (kurs) <liczba> <trzyliterowy kod waluty początkowej> '
        '<trzyliterowy kod waluty docelowej>', value='Konwertuje waluty.',
        inline=False)
    em.add_field(name=f'{conf["command_prefix"]}subreddit (sub, r) <subreddit>',
        value='Zwraca URL subreddita <subreddit>.', inline=False)
    em.add_field(name=f'{conf["command_prefix"]}user (u) <użytkownik Reddita>',
        value='Zwraca URL profilu użytkownika Reddita <użytkownik Reddita>.', inline=False)
    em.add_field(name=f'{conf["command_prefix"]}zweryfikuj',
        value='Rozpoczyna proces weryfikacji konta na Reddicie dla ciebie.', inline=False)
    em.add_field(name=f'{conf["command_prefix"]}prześwietl <użytkownik Discorda>',
        value='Sprawdza status weryfikacji konta na Reddicie dla <użytkownika Discorda> należącego do tego samego '
            'serwera.', inline=False)
    em.add_field(name=f'{conf["command_prefix"]}flip', value='Wywraca stół.', inline=False)
    em.add_field(name=f'{conf["command_prefix"]}fix (unflip)', value='Odstawia wywrócony stół na miejsce.',
        inline=False)
    em.add_field(name=f'{conf["command_prefix"]}lenny (lennyface)', value='( ͡° ͜ʖ ͡°)', inline=False)
    em.add_field(name=f'{conf["command_prefix"]}shrug', value='¯\_(ツ)_/¯', inline=False)
    em.add_field(name=f'{conf["command_prefix"]}ping', value=':ping_pong: Pong!', inline=False)
    em.add_field(name=f'{conf["command_prefix"]}wersja', value='Zwraca wersję bota z którą masz do czynienia.',
        inline=False)
    await ctx.author.send(embed=em)
