# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from somsiad import somsiad


@somsiad.client.command()
@discord.ext.commands.cooldown(
    1, int(somsiad.conf['command_cooldown_per_user_in_seconds']) * 10, discord.ext.commands.BucketType.guild
)
@discord.ext.commands.guild_only()
@discord.ext.commands.is_nsfw()
async def owo(ctx, *args):
    """OwO. This copypasta is dangerously long!"""
    await ctx.send(
        f'Rawr x3 nuzzles how are you pounces on you {" ".join(args) if args else ""}you\'re so warm o3o notices you'
        'have a bulge o: someone\'s happy ;) nuzzles your necky wecky~ murr~ hehehe rubbies your bulgy wolgy you\'re '
        'so big :oooo rubbies more on your bulgy wolgy it doesn\'t stop growing ·///· kisses you and lickies your '
        'necky daddy likies (; nuzzles wuzzles I hope daddy really likes $: wiggles butt and squirms I want to see '
        'your big daddy meat~ wiggles butt I have a little itch o3o wags tail can you please get my itch~ puts paws on '
        'your chest nyea~ its a seven inch itch rubs your chest can you help me pwease squirms pwetty pwease sad face '
        'I need to be punished runs paws down your chest and bites lip like I need to be punished really good~ paws on '
        'your bulge as I lick my lips I\'m getting thirsty. I can go for some milk unbuttons your pants as my eyes '
        'glow you smell so musky :v licks shaft mmmm~ so musky drools all over your cock your daddy meat I like '
        'fondles Mr. Fuzzy Balls hehe puts snout on balls and inhales deeply oh god im so hard~ licks balls punish me '
        'daddy~ nyea~ squirms more and wiggles butt I love your musky goodness bites lip please punish me licks lips '
        'nyea~ suckles on your tip so good licks pre of your cock salty goodness~ eyes role back and goes balls deep '
        'mmmm~ moans and suckles'
    )


@somsiad.client.command(aliases=['masztyrozumigodność', 'masztyrozumigodnośćczłowieka'])
@discord.ext.commands.cooldown(
    1, int(somsiad.conf['command_cooldown_per_user_in_seconds']) * 10, discord.ext.commands.BucketType.guild
)
@discord.ext.commands.guild_only()
@discord.ext.commands.is_nsfw()
async def rigcz(ctx, *args):
    """No comment. This copypasta is dangerously long!"""
    await ctx.send(
        f'no i ja się pytam człowieku {" ".join(args) if args else ""}dumny ty jesteś z siebie zdajesz sobie sprawę z '
        'tego co robisz?masz ty wogóle rozum i godnośc człowieka?ja nie wiem ale żałosny typek z ciebie ,chyba nie '
        'pomyślałes nawet co robisz i kogo obrażasz ,możesz sobie obrażac tych co na to zasłużyli sobie ale nie '
        'naszego papieża polaka naszego rodaka wielką osobę ,i tak wyjątkowa i ważną bo to nie jest ktoś tam taki '
        'sobie że możesz go sobie wyśmiać bo tak ci się podoba nie wiem w jakiej ty się wychowałes rodzinie ale chyba '
        'ty nie wiem nie rozumiesz co to jest wiara .jeśli myslisz że jestes wspaniały to jestes zwykłym czubkiem '
        'którego ktoś nie odizolował jeszcze od społeczeństwa ,nie wiem co w tym jest takie śmieszne ale czepcie się '
        'stalina albo hitlera albo innych zwyrodnialców a nie czepiacie się takiej świętej osoby jak papież jan paweł '
        '2 .jak można wogóle publicznie zamieszczac takie zdięcia na forach internetowych?ja się pytam kto powinien za '
        'to odpowiedziec bo chyba widac że do koscioła nie chodzi jak jestes nie wiem ateistą albo wierzysz w jakies '
        'sekty czy wogóle jestes może ty sługą szatana a nie będziesz z papieża robił takiego ,to ty chyba jestes '
        'jakis nie wiem co sie jarasz pomiotami szatana .'
    )
    await ctx.send(
        'wez pomyśl sobie ile papież zrobił ,on był kimś a ty kim jestes żeby z niego sobie robić kpiny co? kto dał ci '
        'prawo obrażac wogóle papieża naszego ?pomyślałes wogóle nad tym że to nie jest osoba taka sobie że ją '
        'wyśmieje i mnie będa wszyscy chwalic? wez dziecko naprawdę jestes jakis psycholek bo w przeciwieństwie do '
        'ciebie to papież jest autorytetem dla mnie a ty to nie wiem czyim możesz być autorytetem chyba takich samych '
        'jakiś głupków jak ty którzy nie wiedza co to kosciół i religia ,widac że się nie modlisz i nie chodzisz na '
        'religie do szkoły ,widac nie szanujesz religii to nie wiem jak chcesz to sobie wez swoje zdięcie wstaw '
        'ciekawe czy byś sie odważył .naprawdę wezta się dzieci zastanówcie co wy roicie bo nie macie widac pojęcia o '
        'tym kim był papież jan paweł2 jak nie jestescie w pełni rozwinięte umysłowo to się nie zabierajcie za taką '
        'osobę jak ojciec swięty bo to świadczy o tym że nie macie chyba w domu krzyża ani jednego obraza świętego '
        'nie chodzi tutaj o kosciół mnie ale wogóle ogólnie o zasady wiary żeby mieć jakąs godnosc bo papież nikogo '
        'nie obrażał a ty za co go obrażasz co? no powiedz za co obrażasz taką osobę jak ojciec święty ?brak mnie słów '
        'ale jakbyś miał pojęcie chociaz i sięgnął po pismo święte i poczytał sobie to może byś się odmienił .nie wiem '
        'idz do kościoła bo widac już dawno szatan jest w tobie człowieku ,nie lubisz kościoła to chociaż siedz cicho '
        'i nie obrażaj innych ludzi .'
    )


@somsiad.client.command(aliases=['oopsie'])
@discord.ext.commands.cooldown(
    1, int(somsiad.conf['command_cooldown_per_user_in_seconds']) * 10, discord.ext.commands.BucketType.guild
)
@discord.ext.commands.guild_only()
@discord.ext.commands.is_nsfw()
async def oopsiewoopsie(ctx):
    """OOPSIE WOOPSIE!!"""
    await ctx.send(
        'OOPSIE WOOPSIE!! Uwu We made a fucky wucky!! A wittle fucko boingo! The code monkeys at our headquarters are '
        'working VEWY HAWD to fix this!'
    )
