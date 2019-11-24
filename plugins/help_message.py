# Copyright 2018-2019 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from core import somsiad, Help
from configuration import configuration

COMMANDS = (
    Help.Command(('pomocy', 'pomoc', 'help'), (), 'Wysyła ci tę wiadomość.'),
    Help.Command(('8-ball', '8ball', 'eightball', '8', 'czy'), 'pytanie', 'Zadaje <pytanie> magicznej kuli.'),
    Help.Command(
        ('wybierz',), ('opcje',),
        'Wybiera opcję z oddzielonych przecinkami, średnikami, "lub", "albo" lub "czy" <opcji>.'
    ),
    Help.Command(('rzuć', 'rzuc'), ('?liczba kości', '?liczba ścianek kości'), 'Rzuca kością/koścmi.'),
    Help.Command(
        ('oblicz', 'policz'), ('wyrażenie', '?zmienne', '?poziom zaokrąglenia'),
        'Oblicza wartość podanego wyrażenia. '
        'Przyjmuje również oddzielone średnikami zmienne. Po średniku można też podać liczbę miejsc po przecinku do jakiej ma zostać zaokrąglony wynik. '
        f'Przykładowo `oblicz 71 / x; x = 58; 2` zwróci 71/100 '
        'zaokrąglone do 2 cyfr po przecinku. '
        'Jeśli podane dane nie są wystarczające do obliczenia wartości równania, próbuje je uprościć.'
    ),
    Help.Command(
        ('google', 'gugiel', 'g'), 'zapytanie',
        'Wysyła <zapytanie> do [Google](https://www.google.com) i zwraca najlepiej pasującą stronę.'
    ),
    Help.Command(
        ('googleimage', 'gi', 'i'), 'zapytanie',
        'Wysyła <zapytanie> do [Google](https://www.google.pl/imghp) i zwraca najlepiej pasujący obrazek.'
    ),
    Help.Command(
        ('youtube', 'yt', 'tuba'), 'zapytanie',
        'Zwraca z [YouTube](https://www.youtube.com) najlepiej pasujące do <zapytania> wideo.'
    ),
    Help.Command(
        ('wikipedia', 'wiki', 'w'), ('dwuliterowy kod języka', 'hasło'),
        'Sprawdza znaczenie <hasła> w danej wersji językowej [Wikipedii](https://www.wikipedia.org/).'
    ),
    Help.Command(
        ('omdb', 'film'), ('?sezon i odcinek', 'tytuł'),
        'Zwraca z [OMDb](https://www.omdbapi.com/) informacje na temat filmu lub serialu najlepiej pasującego '
        'do <tytułu>. Jeśli chcesz znaleźć informacje na temat konkretnego odcinka serialu, podaj przed tytułem '
        '<?sezon i odcinek> w formacie s<sezon>e<odcinek>, np. "s05e14 breaking bad".'
    ),
    Help.Command(
        ('tłumacz', 'tlumacz', 'translator'), ('kod języka źródłowego', 'kod języka docelowego', 'tekst'),
        'Tłumaczy tekst z [Yandex](https://translate.yandex.com/). '
        'Wpisanie znaku zapytania w miejscu kodu języka źródłowego spowoduje wykrycie języka źródłowego.'
    ),
    Help.Command(
        'spotify', '?użytkownik Discorda',
        'Zwraca informacje na temat utworu obecnie słuchanego przez <?użytkownika Discorda> na Spotify. '
        'Jeśli nie podano <?użytkownika Discorda>, przyjmuje ciebie.'
    ),
    Help.Command(
        ('lastfm', 'last', 'fm', 'lfm'), 'użytkownik Last.fm',
        'Zwraca z Last.fm informacje na temat utworu obecnie słuchanego przez <użytkownika Last.fm>.'
    ),
    Help.Command(
        ('goodreads', 'gr', 'książka', 'ksiazka'), 'tytuł/autor',
        'Zwraca z [goodreads](https://www.goodreads.com) informacje na temat książki najlepiej pasującej do '
        '<tytułu/autora>.'
    ),
    Help.Command(
        ('urbandictionary', 'urban'), 'wyrażenie',
        'Sprawdza znaczenie <wyrażenia> w [Urban Dictionary](https://www.urbandictionary.com).'
    ),
    Help.Command(
        ('kantor', 'kurs'), ('?liczba', 'trzyliterowy kod waluty początkowej', 'trzyliterowy kod waluty docelowej'),
        'Konwertuje waluty za pomocą serwisu [CryptoCompare](https://www.cryptocompare.com).'
    ),
    Help.Command(
        'isitup', 'url', 'Za pomocą serwisu [isitup.org](https://isitup.org) sprawdza status danej strony.'
    ),
    Help.Command(
        ('rokszkolny', 'wakacje', 'ilejeszcze'), (), 'Zwraca ile jeszcze zostało do końca roku szkolnego lub wakacji.'
    ),
    Help.Command(('subreddit', 'sub', 'r'), 'subreddit', 'Zwraca URL <subreddita>.'),
    Help.Command(
        ('user', 'u'), 'użytkownik Reddita', 'Zwraca URL profilu <użytkownika Reddita>.'
    ),
    Help.Command(
        ('disco', 'd'), 'podkomenda',
        'Grupa komend związanych z odtwarzaniem muzyki na kanale głosowym. '
        f'Użyj disco (d) bez podkomendy, by dowiedzieć się więcej.',
    ),
    Help.Command(
        'stat', 'podkomenda',
        'Grupa komend związanych ze statystykami na serwerze. '
        f'Użyj stat bez podkomendy, by dowiedzieć się więcej.',
    ),
    Help.Command(
        'urodziny', 'podkomenda',
        'Grupa komend związanych z datami urodzin. '
        f'Użyj urodziny bez podkomendy, by dowiedzieć się więcej.',
    ),
    Help.Command(
        ('handlowe', 'niedzielehandlowe'), 'podkomenda',
        'Grupa komend związanych z niedzielami handlowymi. '
        f'Użyj handlowe bez podkomendy, by dowiedzieć się więcej.',
    ),
    Help.Command(
        ('spal', 'burn'),
        ('?liczba sekund do/godzina usunięcia wiadomości', 'treść (może być załącznik)'),
        'Usuwa wiadomość po podanej liczbie sekund lub o podanym czasie.'
    ),
    Help.Command(
        'przypinki', 'podkomenda',
        'Grupa komend związanych z archiwizacją przypiętych widadomości. '
        f'Użyj przypinki bez podkomendy, by dowiedzieć się więcej.',
    ),
    Help.Command(
        ('głosowanie', 'glosowanie'), ('?liczba minut do ogłoszenia wyniku/godzina', 'sprawa'),
        'Przeprowadza głosowanie za/przeciw dotyczące <sprawy>. '
        'Ogłasza wynik po upłynięciu <?liczby minut do ogłoszenia wyniku> lub o <?godzinie>, '
        'jeśli podano którąś z nich i jeśli oznacza to zakończenie głosowania w przyszłości odległej maksymalnie '
        'o tydzień.'
    ),
    Help.Command(('pomógł', 'pomogl'), '?użytkownik Discorda', 'Oznacza pomocną wiadomość za pomocą reakcji.'),
    Help.Command(
        ('niepomógł', 'niepomogl'), '?użytkownik Discorda', 'Oznacza niepomocną wiadomość za pomocą reakcji.'
    ),
    Help.Command(
        ('hm', 'hmm', 'hmmm', 'hmmmm', 'hmmmmm', 'myśl', 'mysl', 'think', 'thinking', '🤔'),
        '?użytkownik Discorda', '🤔'
    ),
    Help.Command(('^', 'to', 'this', 'up', 'upvote'), '?użytkownik Discorda', '⬆'),
    Help.Command('f', '?użytkownik Discorda', 'F'),
    Help.Command(
        ('zareaguj', 'x'), ('?użytkownik Discorda', 'reakcje'),
        'Dodaje <reakcje> do ostatniej wiadomości wysłanej na kanale '
        '(jeśli podano <?użytkownika Discorda>, to ostatnią jego autorstwa na kanale).'
    ),
    Help.Command('oof', (), 'Oof!'),
    Help.Command(
        'oof ile', '?użytkownik Discorda',
        'Zlicza oofnięcia dla <?użytkownika Discorda> lub, jeśli nie podano <?użytkownika Discorda>, dla ciebie. '
    ),
    Help.Command(
        'oof serwer', '?użytkownik Discorda',
        'Zlicza oofnięcia na serwerze i generuje ranking ooferów.'
    ),
    Help.Command(
        ('deepfry', 'usmaż', 'głębokosmaż', 'usmaz', 'glebokosmaz'),
        '?poziom usmażenia', 'Smaży ostatni załączony na kanale obrazek <?poziom usmażenia> razy (domyślnie 2). '
    ),
    Help.Command('tableflip', (), '(╯°□°）╯︵ ┻━┻'),
    Help.Command('unflip', (), '┬─┬ ノ( ゜-゜ノ)'),
    Help.Command('shrug', (), r'¯\_(ツ)_/¯'),
    Help.Command(('lenny', 'lennyface'), (), '( ͡° ͜ʖ ͡°)'),
    Help.Command(('lenno', 'lennoface'), (), '( ͡ʘ ͜ʖ ͡ʘ)'),
    Help.Command(('dej', 'gib'), '?rzecz', '༼ つ ◕_◕ ༽つ <?rzecz>'),
    Help.Command(
        ('nie', 'nope', 'no'), (),
        'Usuwa ostatnią wiadomość wysłaną przez bota na kanale jako rezultat użytej przez ciebie komendy.'
    ),
    Help.Command(
        ('warn', 'ostrzeż', 'ostrzez'), ('użytkownik Discorda', 'powód'),
        'Ostrzega <użytkownika Discorda>. Działa tylko dla członków serwera mających uprawnienia do wyrzucania innych.'
    ),
    Help.Command(
        ('kick', 'wyrzuć', 'wyrzuc'), ('użytkownik Discorda', 'powód'),
        'Wyrzuca <użytkownika Discorda>. Działa tylko dla członków serwera mających uprawnienia do wyrzucania innych.'
    ),
    Help.Command(
        ('ban', 'zbanuj'), ('użytkownik Discorda', 'powód'),
        'Banuje <użytkownika Discorda>. Działa tylko dla członków serwera mających uprawnienia do banowania innych.'
    ),
    Help.Command(
        'kartoteka', ('?użytkownik Discorda', '?typy zdarzeń'),
        'Sprawdza kartotekę <?użytkownika Discorda> pod kątem <?typów zdarzeń>. '
        'Jeśli nie podano <?użytkownika Discorda>, przyjmuje ciebie. '
        'Jeśli nie podano typu <?typów zdarzeń>, zwraca wszystkie zdarzenia.'
    ),
    Help.Command(
        ('wyczyść', 'wyczysc'), '?liczba',
        'Usuwa <?liczbę> ostatnich wiadomości z kanału lub, jeśli nie podano <?liczby>, jedną ostatnią wiadomość '
        'z kanału na którym użyto komendy. Działa tylko dla członków serwera mających uprawnienia '
        'do zarządzania wiadomościami na kanale.'
    ),
    Help.Command('ping', (), 'Pong!'),
    Help.Command(('wersja', 'v'), (), 'Działająca wersja bota.'),
    Help.Command(('informacje', 'info'), (), 'Działająca wersja bota plus dodatkowe informacje.'),
)

DESCRIPTION = (
    'Somsiad jestem. Pomagam ludziom w różnych kwestiach. '
    'By skorzystać z mojej pomocy wystarczy wysłać komendę w miejscu, w którym będę mógł ją zobaczyć. '
    'Lista komend wraz z ich opisami znajduje się poniżej. '
    'Używając ich pamiętaj o prefiksie (możesz zawsze sprawdzić go za pomocą '
    f'`{configuration["command_prefix"]}prefiks sprawdź`).\n'
    'W (nawiasach okrągłych) podane są aliasy komend.\n'
    'W <nawiasach ostrokątnych> podane są argumenty komend. Jeśli przed nazwą argumentu jest ?pytajnik, '
    'oznacza to, że jest to argument opcjonalny.\n'
    f'By dowiedzieć się o mnie więcej, wejdź na {somsiad.WEBSITE_URL}.'
)


@somsiad.command(aliases=['help', 'pomocy', 'pomoc'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def help_message(ctx):
    await Help(COMMANDS, title='Dobry!', description=DESCRIPTION).send(ctx, privately=True)
