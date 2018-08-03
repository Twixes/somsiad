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

@client.command(aliases=['pomocy', 'pomoc'])
@commands.cooldown(1, conf['user_command_cooldown'], commands.BucketType.user)
async def help_direct(ctx):
    em = discord.Embed(title='Lecem na ratunek!' , colour=0x269d9c)
    em.add_field(name='Dobry!', value='Somsiad jestem. Pomagam w różnych kwestiach, wystarczy mnie zawołać.'
        ' Odpowiadam na wszystkie zawołania z poniższej listy. Pamiętaj tylko zawsze, by zacząć od "' +
        conf['command_prefix'] + '".\nW nawiasach podane są alternatywne nazwy zawołań - tak dla różnorodności.')
    em.add_field(name=conf['command_prefix'] + '8-ball (8ball, eightball, 8) <pytanie>',
        value='Zadaje <pytanie> magicznej kuli.', inline=False)
    em.add_field(name=conf['command_prefix'] + 'flip', value='Wywraca stół.', inline=False)
    em.add_field(name=conf['command_prefix'] + 'fix (unflip)', value='Odwraca wywrócony stół.', inline=False)
    em.add_field(name=conf['command_prefix'] + 'gugiel (g) <zapytanie>',
        value='Wysyła <zapytanie> do wyszukiwarki Google i zwraca najlepiej pasujący wynik.', inline=False)
    em.add_field(name=conf['command_prefix'] + 'img (i) <zapytanie>',
        value='Wysyła <zapytanie> do wyszukiwarki Qwant i zwraca najlepiej pasujący do niego obrazek.', inline=False)
    em.add_field(name=conf['command_prefix'] + 'isitup (isup) <url>',
        value='Za pomocą serwisu isitup.org wykrywa status danej strony.', inline=False)
    em.add_field(name=conf['command_prefix'] + 'pomocy (pomoc, help)', value='Wysyła użytkownikowi tę wiadomość.',
        inline=False)
    em.add_field(name=conf['command_prefix'] + 'lenny (lennyface)', value=' ( ͡° ͜ʖ ͡°)', inline=False)
    em.add_field(name=conf['command_prefix'] + 'ping', value=':ping_pong: Pong!', inline=False)
    em.add_field(name=conf['command_prefix'] + 'subreddit (sub, r) <subreddit>', value='Zwraca URL subreddita <subreddit>.',
        inline=False)
    em.add_field(name=conf['command_prefix'] + 'shrug', value='¯\_(ツ)_/¯', inline=False)
    em.add_field(name=conf['command_prefix'] + 'wikipediapl (wikipl, wpl) <temat>',
        value='Sprawdza znaczenie <terminu> w polskiej wersji Wikipedii.', inline=False)
    em.add_field(name=conf['command_prefix'] + 'wikipediaen (wikien, wen) <temat>',
        value='Sprawdza znaczenie <terminu> w anglojęzycznej wersji Wikipedii.', inline=False)
    em.add_field(name=conf['command_prefix'] + 'urbandictionary (urban) <słowo>',
        value='Sprawdza znaczenie <słowa> w Urban Dictionary.', inline=False)
    em.add_field(name=conf['command_prefix'] + 'youtube (yt, tuba) <zapytanie>',
        value='Wysyła <zapytanie> do YouTube i zwraca najlepiej pasujący wynik.', inline=False)
    await ctx.author.send(embed=em)
