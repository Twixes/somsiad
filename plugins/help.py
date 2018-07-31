import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
from somsiad_helper import *


@client.command(aliases=['pomoc'])
@commands.cooldown(1, 1, commands.BucketType.user)
async def help(ctx):
    em = discord.Embed(title='POMOC' , colour=0x269d9c)
    em.add_field(name='Cześć!', value="Witaj na stronie pomocy Somdiada - dyskordowego bota. " +
        "By wysłać polecenie Somsiadowi, umieść kropkę `.` na początku polecenia. " +
        "Lista dostępnych poleceń znajduje się poniżej. " +
        "W nawiasie podano alternatywne nazwy poleceń. **Przykład:** `.w słowo`")
    em.add_field(name='8ball (eightball, 8) <pytanie>',
        value='Zadaje <pytanie> elektronicznej, magicznej kuli.', inline=False)
    em.add_field(name='fix (unflip)', value='Odwraca wywrócony stół.', inline=False)
    em.add_field(name='flip', value='Wywraca stół.', inline=False)
    em.add_field(name='g <zapytanie>',
        value='Wysyła <zapytanie> do wyszukiwarki Google i zwraca najlepiej pasujący wynik.', 
        inline=False)
    em.add_field(name='i <zapytanie>',
        value='Wysyła <zapytanie> do wyszukiwarki Qwant i zwraca najlepiej pasujący do niego ' +
        'obrazek.', inline=False)
    em.add_field(name='isup (isitup) <url>', 
        value='Z pomocą serwisu isitup.org wykrywa czy strona jest online bądź offline.', 
        inline=False)
    em.add_field(name='pomoc (help)', value='Zwraca tę wiadomość w prywatnej wiadomości.',
        inline=False)
    em.add_field(name='lenny (lennyface)', value='Wstawia lennyface ( ͡° ͜ʖ ͡°)', inline=False)
    em.add_field(name='ping', value='pong ;-)', inline=False)
    em.add_field(name='r <nazwa>', value='Zwraca pełny URL subreddita <nazwa>.', inline=False)
    em.add_field(name='shrug', value='¯\_(ツ)_/¯', inline=False)
    em.add_field(name='w (wiki, wikipedia) <termin>',
        value='Sprawdza znaczenie <terminu> w polskiej wersji Wikipedii.', inline=False)
    em.add_field(name='wen (wikien, wikipediaen) <termin>',
        value='Sprawdza znaczenie <terminu> w angielskiej wersji Wikipedii.', inline=False)
    em.add_field(name='u (urban) <słowo>',
        value='Sprawdza znaczenie <słowa> w słowniku Urban Dictionary.', inline=False)
    em.add_field(name='yt (youtube) <zapytanie>',
        value='Wysyła <zapytanie> do YouTube i zwraca najlepiej pasujący wynik.', inline=False)
    await ctx.author.send(embed=em)
