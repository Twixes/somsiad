# Copyright 2018-2019 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from collections import namedtuple
from typing import Union, Sequence, List, Tuple
import discord
from somsiad import somsiad
from version import __version__


class Helper:
    """Handles generation of the help message."""
    Command = namedtuple('Command', ('aliases', 'arguments', 'description'))

    @staticmethod
    def _add_command_field_to_embed(embed: discord.Embed, command: Command, is_subcommand: bool = False):
        if isinstance(command.aliases, (tuple, list)):
            name_string = command.aliases[0]
        else:
            name_string = command.aliases

        if isinstance(command.aliases, (tuple, list)) and len(command.aliases) > 1:
            aliases_string = f' ({", ".join(command.aliases[1:])})'
        else:
            aliases_string = ''

        if isinstance(command.arguments, (tuple, list)) and command.arguments:
            arguments_string = (
                f' {" ".join(f"<{argument}>" for argument in command.arguments)}' if command.arguments else ''
            )
        elif command.arguments is not None:
            arguments_string = f' <{command.arguments}>'
        else:
            arguments_string = ''

        prefix = '' if is_subcommand else somsiad.conf["command_prefix"]

        embed.add_field(
            name=f'{prefix}{name_string}{aliases_string}{arguments_string}',
            value=command.description,
            inline=False
        )

    @classmethod
    def generate_general_embed(
            cls, commands: Sequence[Command], embeds: Sequence[discord.Embed] = None
    ) -> discord.Embed:
        if embeds is None:
            embeds = []
            embeds.append(discord.Embed(color=somsiad.color))
            embeds[0].add_field(
                name='Dobry!',
                value='Somsiad jestem. Pomagam ludziom w różnych kwestiach. '
                'By skorzystać z mojej pomocy wystarczy wysłać komendę w miejscu, w którym będę mógł ją zobaczyć. '
                'Lista komend wraz z ich opisami znajduje się poniżej.\n'
                'W nawiasach okrągłych podane są alternatywne nazwy komend.\n'
                'W nawiasach ostrokątnych podane są argumenty komend. Jeśli przed nazwą argumentu jest pytajnik, '
                'oznacza to, że jest to argument opcjonalny.\n'
                'Gdybyś chciał dowiedzieć się o mnie więcej, wejdź na https://somsiad.twixes.com/.',
                inline=False
            )
        else:
            embeds.append(discord.Embed(color=somsiad.color))

        for command in commands[:25 * len(embeds)]:
            cls._add_command_field_to_embed(embeds[-1], command)

        if commands[25 * len(embeds):]:
            return cls.generate_general_embed(commands[25 * len(embeds) - 1:], embeds)
        else:
            return embeds

    @classmethod
    def generate_subcommands_embed(
            cls, command_aliases: Union[str, Union[List[str], Tuple[str]]], subcommands: Sequence[Command]
    ) -> discord.Embed:
        if isinstance(command_aliases, (tuple, list)):
            name_string = command_aliases[0]
        else:
            name_string = command_aliases

        if isinstance(command_aliases, (tuple, list)) and len(command_aliases) > 1:
            aliases_string = f' ({", ".join(command_aliases[1:])})'
        else:
            aliases_string = ''

        embed = discord.Embed(
            title=f'Dostępne podkomendy {somsiad.conf["command_prefix"]}{name_string}{aliases_string}',
            description=f'Użycie: {somsiad.conf["command_prefix"]}{name_string} <podkomenda>',
            color=somsiad.color
        )

        for subcommand in subcommands:
            cls._add_command_field_to_embed(embed, subcommand, is_subcommand=True)

        return embed


commands = (
    Helper.Command(('pomocy', 'help'), None, 'Wysyła ci tę wiadomość.'),
    Helper.Command(('8-ball', '8ball', 'eightball', '8', 'czy'), 'pytanie', 'Zadaje <pytanie> magicznej kuli.'),
    Helper.Command(
        ('wybierz',), ('opcje',),
        'Wybiera opcję z oddzielonych przecinkami, średnikami, "lub", "albo" lub "czy" <opcji>.'
    ),
    Helper.Command(('rzuć', 'rzuc'), ('?liczba kości', '?liczba ścianek kości'), 'Rzuca kością/koścmi.'),
    Helper.Command(
        ('oblicz', 'policz'), ('wyrażenie', '?zmienne'),
        'Oblicza wartość podanego wyrażenia. '
        'Przyjmuje również oddzielone średnikami zmienne, np. "x ^ 2 + y + 4; x = 3; y = 5". '
        'Jeśli podane dane nie są wystarczające do obliczenia wartości równania, próbuje je uprościć.'
    ),
    Helper.Command(
        ('google', 'gugiel', 'g'), 'zapytanie',
        'Wysyła <zapytanie> do [Google](https://www.google.com) i zwraca najlepiej pasującą stronę.'
    ),
    Helper.Command(
        ('googleimage', 'gi', 'i'), 'zapytanie',
        'Wysyła <zapytanie> do [Google](https://www.google.pl/imghp) i zwraca najlepiej pasujący obrazek.'
    ),
    Helper.Command(
        ('youtube', 'yt', 'tuba'), 'zapytanie',
        'Zwraca z [YouTube](https://www.youtube.com) najlepiej pasujące do <zapytania> wideo.'
    ),
    Helper.Command(
        ('giphy', 'gif'), 'zapytanie',
        'Zwraca z [Giphy](https://giphy.com) najlepiej pasującego do <zapytania> gifa.'
    ),
    Helper.Command(
        ('wikipedia', 'wiki', 'w'), ('dwuliterowy kod języka', 'hasło'),
        'Sprawdza znaczenie <hasła> w danej wersji językowej [Wikipedii](https://www.wikipedia.org/).'
    ),
    Helper.Command(
        ('omdb', 'film'), ('?sezon i odcinek', 'tytuł'),
        'Zwraca z [OMDb](https://www.omdbapi.com/) informacje na temat filmu lub serialu najlepiej pasującego '
        'do <tytułu>. Jeśli chcesz znaleźć informacje na temat konkretnego odcinka serialu, podaj przed tytułem '
        '<?sezon i odcinek> w formacie s<sezon>e<odcinek>, np. "s05e14 breaking bad".'
    ),
    Helper.Command(
        ('tłumacz', 'tlumacz', 'translator'), ('kod języka źródłowego', 'kod języka docelowego', 'tekst'),
        'Tłumaczy tekst z [Yandex](https://translate.yandex.com/). '
        'Wpisanie znaku zapytania w miejscu kodu języka źródłowego spowoduje wykrycie języka źródłowego.'
    ),
    Helper.Command(
        'spotify', '?użytkownik Discorda',
        'Zwraca informacje na temat utworu obecnie słuchanego przez <?użytkownika Discorda> na Spotify. '
        'Jeśli nie podano <?użytkownika Discorda>, przyjmuje ciebie.'
    ),
    Helper.Command(
        ('lastfm', 'last', 'fm', 'lfm'), 'użytkownik Last.fm',
        'Zwraca z Last.fm informacje na temat utworu obecnie słuchanego przez <użytkownika Last.fm>.'
    ),
    Helper.Command(
        ('goodreads', 'gr', 'książka', 'ksiazka'), 'tytuł/autor',
        'Zwraca z [goodreads](https://www.goodreads.com) informacje na temat książki najlepiej pasującej do '
        '<tytułu/autora>.'
    ),
    Helper.Command(
        ('urbandictionary', 'urban'), 'wyrażenie',
        'Sprawdza znaczenie <wyrażenia> w [Urban Dictionary](https://www.urbandictionary.com).'
    ),
    Helper.Command(
        ('kantor', 'kurs'), ('?liczba', 'trzyliterowy kod waluty początkowej', 'trzyliterowy kod waluty docelowej'),
        'Konwertuje waluty za pomocą serwisu [CryptoCompare](https://www.cryptocompare.com).'
    ),
    Helper.Command(
        'isitup', 'url', 'Za pomocą serwisu [isitup.org](https://isitup.org) sprawdza status danej strony.'
    ),
    Helper.Command(('rokszkolny', 'ilejeszcze'), None, 'Zwraca ile jeszcze zostało do końca roku szkolnego.'),
    Helper.Command(('subreddit', 'sub', 'r'), 'subreddit', 'Zwraca URL <subreddita>.'),
    Helper.Command(
        ('user', 'u'), 'użytkownik Reddita', 'Zwraca URL profilu <użytkownika Reddita>.'
    ),
    Helper.Command(
        ('disco', 'd'), 'podkomenda',
        'Grupa komend związanych z odtwarzaniem muzyki na kanale głosowym. '
        f'Użyj {somsiad.conf["command_prefix"]}disco (d) bez podkomendy by dowiedzieć się więcej.',
    ),
    Helper.Command(
        'stat', 'podkomenda',
        'Grupa komend związanych ze statystykami na serwerze. '
        f'Użyj {somsiad.conf["command_prefix"]}stat bez podkomendy by dowiedzieć się więcej.',
    ),
    Helper.Command(
        'urodziny', 'podkomenda',
        'Grupa komend związanych z datami urodzin. '
        f'Użyj {somsiad.conf["command_prefix"]}urodziny bez podkomendy by dowiedzieć się więcej.',
    ),
    Helper.Command(
        ('spal', 'burn'),
        ('?liczba sekund do/godzina usunięcia wiadomości', 'treść (może być załącznik)'),
        'Usuwa wiadomość po podanej liczbie sekund lub o podanym czasie.'
    ),
    Helper.Command(
        'weryfikacja', 'podkomenda',
        'Grupa komend związanych z weryfikacją użytkownika Discorda na Reddicie. '
        f'Użyj {somsiad.conf["command_prefix"]}weryfikacja bez podkomendy by dowiedzieć się więcej.',
    ),
    Helper.Command(
        'przypinki', 'podkomenda',
        'Grupa komend związanych z archiwizacją przypiętych widadomości. '
        f'Użyj {somsiad.conf["command_prefix"]}przypinki bez podkomendy by dowiedzieć się więcej.',
    ),
    Helper.Command(
        ('głosowanie', 'glosowanie'), ('?liczba minut do ogłoszenia wyniku/godzina', 'sprawa'),
        'Przeprowadza głosowanie za/przeciw dotyczące <sprawy>. '
        'Ogłasza wynik po upłynięciu <?liczby minut do ogłoszenia wyniku> lub o <?godzinie>, '
        'jeśli podano którąś z nich i jeśli oznacza to zakończenie głosowania w przyszłości odległej maksymalnie '
        'o tydzień.'
    ),
    Helper.Command(('pomógł', 'pomogl'), '?użytkownik Discorda', 'Oznacza pomocną wiadomość za pomocą reakcji.'),
    Helper.Command(
        ('niepomógł', 'niepomogl'), '?użytkownik Discorda', 'Oznacza niepomocną wiadomość za pomocą reakcji.'
    ),
    Helper.Command(
        ('hm', 'hmm', 'hmmm', 'hmmmm', 'hmmmmm', 'myśl', 'mysl', 'think', 'thinking', '🤔'),
        '?użytkownik Discorda', '🤔'
    ),
    Helper.Command(('^', 'to', 'this', 'up', 'upvote'), '?użytkownik Discorda', '⬆'),
    Helper.Command('f', '?użytkownik Discorda', 'F'),
    Helper.Command(
        ('zareaguj', 'x'), ('?użytkownik Discorda', 'reakcje'),
        'Dodaje <reakcje> do ostatniej wiadomości wysłanej na kanale '
        '(jeśli podano <?użytkownika Discorda>, to ostatnią jego autorstwa na kanale).'
    ),
    Helper.Command('oof', None, 'Oof!'),
    Helper.Command(
        'oof ile', '?użytkownik Discorda',
        'Zlicza oofnięcia dla <?użytkownika Discorda> lub, jeśli nie podano <?użytkownika Discorda>, dla ciebie. '
    ),
    Helper.Command(
        'oof serwer', '?użytkownik Discorda',
        'Zlicza oofnięcia na serwerze i generuje ranking ooferów.'
    ),
    Helper.Command(
        ('deepfry', 'usmaż', 'głębokosmaż', 'usmaz', 'glebokosmaz'),
        '?poziom usmażenia', 'Smaży ostatni załączony na kanale obrazek <?poziom usmażenia> razy (domyślnie 2). '
    ),
    Helper.Command('tableflip', None, '(╯°□°）╯︵ ┻━┻'),
    Helper.Command('unflip', None, '┬─┬ ノ( ゜-゜ノ)'),
    Helper.Command('shrug', None, r'¯\_(ツ)_/¯'),
    Helper.Command(('lenny', 'lennyface'), None, '( ͡° ͜ʖ ͡°)'),
    Helper.Command(('lenno', 'lennoface'), None, '( ͡ʘ ͜ʖ ͡ʘ)'),
    Helper.Command(('dej', 'gib'), '?rzecz', '༼ つ ◕_◕ ༽つ <?rzecz>'),
    Helper.Command(
        ('nie', 'nope', 'no'), None,
        'Usuwa ostatnią wiadomość wysłaną przez bota na kanale jako rezultat użytej przez ciebie komendy.'
    ),
    Helper.Command(
        ('warn', 'ostrzeż', 'ostrzez'), ('użytkownik Discorda', 'powód'),
        'Ostrzega <użytkownika Discorda>. Działa tylko dla członków serwera mających uprawnienia do wyrzucania innych.'
    ),
    Helper.Command(
        ('kick', 'wyrzuć', 'wyrzuc'), ('użytkownik Discorda', 'powód'),
        'Wyrzuca <użytkownika Discorda>. Działa tylko dla członków serwera mających uprawnienia do wyrzucania innych.'
    ),
    Helper.Command(
        ('ban', 'zbanuj'), ('użytkownik Discorda', 'powód'),
        'Banuje <użytkownika Discorda>. Działa tylko dla członków serwera mających uprawnienia do banowania innych.'
    ),
    Helper.Command(
        'kartoteka', ('?użytkownik Discorda', '?typy zdarzeń'),
        'Sprawdza kartotekę <?użytkownika Discorda> pod kątem <?typów zdarzeń>. '
        'Jeśli nie podano <?użytkownika Discorda>, przyjmuje ciebie. '
        'Jeśli nie podano typu <?typów zdarzeń>, zwraca wszystkie zdarzenia.'
    ),
    Helper.Command(
        ('wyczyść', 'wyczysc'), '?liczba',
        'Usuwa <?liczbę> ostatnich wiadomości z kanału lub, jeśli nie podano <?liczby>, jedną ostatnią wiadomość '
        'z kanału na którym użyto komendy. Działa tylko dla członków serwera mających uprawnienia '
        'do zarządzania wiadomościami na kanale.'
    ),
    Helper.Command('loguj', '?kanał',
        'Ustawia <?kanał> jako kanał logów serwera. Jeśli nie podano <?kanału> przyjmuje kanał na którym użyto '
        'komendy. Działa tylko dla administratorów serwera.'
    ),
    Helper.Command('nieloguj', None, 'Wyłącza kanał logów serwera. Działa tylko dla administratorów serwera.'),
    Helper.Command('ping', None, ':ping_pong: Pong!'),
    Helper.Command('wersja', None, __version__)
)


@somsiad.bot.command(aliases=['help', 'pomocy'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def help_message(ctx):
    embeds = Helper.generate_general_embed(commands)
    for embed in embeds:
        await ctx.author.send(embed=embed)
