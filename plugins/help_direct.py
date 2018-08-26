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
from version import __version__


@somsiad.client.command(aliases=['help', 'pomocy'])
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
async def help_direct(ctx):
    embed = discord.Embed(title='Lecem na ratunek!' , color=somsiad.color)
    embed.add_field(
        name='Dobry!',
        value='Somsiad jestem. Na co dzień pomagam ludziom w różnych kwestiach. '
        'By skorzystać z mojej pomocy wystarczy wysłać komendę w miejscu, w którym będę mógł ją zobaczyć. '
        'Lista komend wraz z ich opisami znajduje się poniżej.\n'
        'W nawiasach okrągłych podane są alternatywne nazwy komend - tak dla różnorodności.\n'
        'W nawiasach ostrokątnych podane są argumenty komend. Jeśli na początku nazwy argumentu jest pytajnik, '
        'oznacza to, że jest to argument opcjonalny.\n',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}pomocy (help)',
        value='Wysyła ci tę wiadomość.',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}8-ball (8ball, eightball, 8, czy) <pytanie>',
        value='Zadaje <pytanie> magicznej kuli.',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}google (gugiel, g) <zapytanie>',
        value='Wysyła <zapytanie> do [Google](https://www.google.com) i zwraca najlepiej pasującą stronę.',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}googleimage (gi, i) <zapytanie>',
        value='Wysyła <zapytanie> do [Google](https://www.google.com) i zwraca najlepiej pasujący obrazek.',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}youtube (yt, tuba) <zapytanie>',
        value='Zwraca z [YouTube](https://www.youtube.com) najlepiej pasujące do <zapytania> wideo.',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}giphy (gif) <zapytanie>',
        value='Zwraca z [Giphy](https://giphy.com) najlepiej pasującego do <zapytania> gifa.',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}wikipediapl (wikipl, wpl) <hasło>',
        value='Sprawdza znaczenie <hasła> w [polskiej wersji Wikipedii]'
        '(https://pl.wikipedia.org/wiki/Wikipedia:Strona_główna).',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}wikipediaen (wikien, wen) <hasło>',
        value='Sprawdza znaczenie <hasła> w [anglojęzycznej wersji Wikipedii]'
        '(https://en.wikipedia.org/wiki/Main_Page).',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}goodreads (gr) <tytuł/autor>',
        value='Zwraca z [goodreads](https://www.goodreads.com) książkę najlepiej pasującą do <tytułu/autora>.',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}urbandictionary (urban) <wyrażenie>',
        value='Sprawdza znaczenie <wyrażenia> w [Urban Dictionary](https://www.urbandictionary.com).',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}isitup (isup) <url>',
        value='Za pomocą serwisu [isitup.org](https://isitup.org) sprawdza status danej strony.',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}kantor (kurs) <?liczba> '
        '<trzyliterowy kod waluty początkowej> <?trzyliterowy kod waluty docelowej>',
        value='Konwertuje waluty za pomocą serwisu [CryptoCompare](https://www.cryptocompare.com).',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}subreddit (sub, r) <subreddit>',
        value='Zwraca URL subreddita <subreddit>.',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}user (u) <użytkownik Reddita>',
        value='Zwraca URL profilu użytkownika Reddita <użytkownik Reddita>.',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}zweryfikuj',
        value=f'Rozpoczyna proces weryfikacji konta na Reddicie dla ciebie.',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}prześwietl (przeswietl) <?użytkownik Discorda>',
        value='Sprawdza status weryfikacji konta na Reddicie dla <?użytkownika Discorda> '
        '(jeśli należy on do serwera na którym użyto komendy) lub, jeśli nie podano argumentu, dla ciebie.',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}wyczyść (wyczysc) <?liczba>',
        value='Usuwa <?liczbę> ostatnich wiadomości lub, jeśli nie podano liczby, jedną ostatnią wiadomość z kanału '
        'na którym użyto komendy. Działa tylko dla członków serwera o podwyższonych uprawnieniach.',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}pomógł (pomogl) <?użytkownik Discorda>',
        value='Oznacza pomocną wiadomość za pomocą reakcji.',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}niepomógł (niepomogl) <?użytkownik Discorda>',
        value='Oznacza niepomocną wiadomość za pomocą reakcji.',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}rzuć (rzuc) <?liczba kości> <?liczba ścianek kości>',
        value='Rzuca kością. ',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}tableflip',
        value='(╯°□°）╯︵ ┻━┻',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}unflip',
        value='┬─┬ ノ( ゜-゜ノ)',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}shrug',
        value=r'¯\_(ツ)_/¯',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}lenny (lennyface)',
        value='( ͡° ͜ʖ ͡°)',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}dej (gib) <?rzecz>',
        value='༼ つ ◕_◕ ༽つ <?rzecz>',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}ping',
        value=':ping_pong: Pong!',
        inline=False
    )
    embed.add_field(
        name=f'{somsiad.conf["command_prefix"]}wersja',
        value=__version__,
        inline=False
    )
    await ctx.author.send(embed=embed)
