# Copyright 2018-2020 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from discord.ext import commands
from core import Help as _Help, cooldown
from configuration import configuration


class Help(commands.Cog):
    COMMANDS = (
        _Help.Command(('pomocy', 'pomoc', 'help'), (), 'Wysyła ci tę wiadomość.'),
        _Help.Command(('8-ball', '8ball', 'eightball', '8', 'czy'), 'pytanie', 'Zadaje <pytanie> magicznej kuli.'),
        _Help.Command(
            ('wybierz',), ('opcje',),
            'Wybiera opcję z oddzielonych przecinkami, średnikami, "lub", "albo" lub "czy" <opcji>.'
        ),
        _Help.Command(('rzuć', 'rzuc'), ('?liczba kości', '?liczba ścianek kości'), 'Rzuca kością/koścmi.'),
        _Help.Command(
            ('google', 'gugiel', 'g'), 'zapytanie',
            'Wysyła <zapytanie> do [Google](https://www.google.com) i zwraca najlepiej pasującą stronę.'
        ),
        _Help.Command(
            ('googleimage', 'gi', 'i'), 'zapytanie',
            'Wysyła <zapytanie> do [Google](https://www.google.pl/imghp) i zwraca najlepiej pasujący obrazek.'
        ),
        _Help.Command(
            ('youtube', 'yt', 'tuba'), 'zapytanie',
            'Zwraca z [YouTube](https://www.youtube.com) najlepiej pasujące do <zapytania> wideo.'
        ),
        _Help.Command(
            ('wikipedia', 'wiki', 'w'), ('dwuliterowy kod języka', 'hasło'),
            'Sprawdza znaczenie <hasła> w danej wersji językowej [Wikipedii](https://www.wikipedia.org/).'
        ),
        _Help.Command(
            'tmdb', 'zapytanie/podkomenda',
            'Zwraca z [TMDb](https://www.themoviedb.org/) najlepiej pasujący do <?zapytania> film/serial/osobę. '
            'Użyj bez <?zapytania/podkomendy>, by dowiedzieć się więcej.'
        ),
        _Help.Command(
            ('tłumacz', 'tlumacz', 'translator'), ('kod języka źródłowego', 'kod języka docelowego', 'tekst'),
            'Tłumaczy tekst z [Yandex](https://translate.yandex.com/). '
            'Wpisanie znaku zapytania w miejscu kodu języka źródłowego spowoduje wykrycie języka źródłowego.'
        ),
        _Help.Command(
            'spotify', '?użytkownik Discorda',
            'Zwraca informacje na temat utworu obecnie słuchanego przez <?użytkownika Discorda> na Spotify. '
            'Jeśli nie podano <?użytkownika Discorda>, przyjmuje ciebie.'
        ),
        _Help.Command(
            ('lastfm', 'last', 'fm', 'lfm'), 'użytkownik Last.fm',
            'Zwraca z Last.fm informacje na temat utworu obecnie słuchanego przez <użytkownika Last.fm>.'
        ),
        _Help.Command(
            ('goodreads', 'gr', 'książka', 'ksiazka'), 'tytuł/autor',
            'Zwraca z [goodreads](https://www.goodreads.com) informacje na temat książki najlepiej pasującej do '
            '<tytułu/autora>.'
        ),
        _Help.Command(
            ('urbandictionary', 'urban'), 'wyrażenie',
            'Sprawdza znaczenie <wyrażenia> w [Urban Dictionary](https://www.urbandictionary.com).'
        ),
        _Help.Command(
            ('wolframalpha', 'wolfram', 'wa', 'kalkulator', 'oblicz', 'policz', 'przelicz', 'konwertuj'),
            ('zapytanie',),
            '[Wolfram Alpha](https://www.wolframalpha.com/) – oblicza, przelicza, podaje najróżniejsze informacje. '
            'Usługa po angielsku.'
        ),
        _Help.Command(
            ('isitup', 'isup', 'czydziała', 'czydziala'), 'link', 'Sprawdza status danej strony.'
        ),
        _Help.Command(
            ('rokszkolny', 'wakacje', 'ilejeszcze'), '?podkomenda',
            'Zwraca ile jeszcze zostało do końca roku szkolnego lub wakacji. '
            'Użyj z <podkomendą> "matura", by dowiedzieć się ile zostało do matury.'
        ),
        _Help.Command(('subreddit', 'sub', 'r'), 'subreddit', 'Zwraca informacje o <subreddicie>.'),
        _Help.Command(('user', 'u'), 'użytkownik Reddita', 'Zwraca informacje o <użytkowniku Reddita>.'),
        _Help.Command(
            ('disco', 'd'), '?podkomenda',
            'Komendy związane z odtwarzaniem muzyki. Użyj bez <?podkomendy>, by dowiedzieć się więcej.',
        ),
        _Help.Command(
            'stat', '?użytkownik/kanał/kategoria/podkomenda',
            'Komendy związane ze statystykami serwerowymi. '
            'Użyj bez <?użytkownika/kanału/kategorii/podkomendy>, by dowiedzieć się więcej.',
        ),
        _Help.Command(
            'urodziny', '?podkomenda/użytkownik',
            'Komendy związane z datami urodzin. Użyj bez <?podkomendy/użytkownika>, by dowiedzieć się więcej.',
        ),
        _Help.Command(
            ('handlowe', 'niedzielehandlowe'), '?podkomenda',
            'Komendy związane z niedzielami handlowymi. Użyj bez <?podkomendy>, by dowiedzieć się więcej.',
        ),
        _Help.Command(
            ('przypomnij', 'przypomnienie', 'pomidor'),
            ('liczba minut/data i godzina', 'treść'),
            'Przypomina o <treści> po upływie podanego czasu.'
        ),
        _Help.Command(
            ('spal', 'burn'),
            ('liczba minut/data i godzina', '?treść – może to też być załącznik'),
            'Usuwa wiadomość po upływie podanego czasu.'
        ),
        _Help.Command(
            ('kolory', 'kolor', 'kolorki', 'kolorek'), '?podkomenda',
            'Komendy związane z kolorami nicków samodzielnie wybieranymi przez użytkowników. '
            'Użyj bez <?podkomendy>, by dowiedzieć się więcej.',
        ),
        _Help.Command(
            'przypinki', '?podkomenda',
            'Komendy związane z archiwizacją przypiętych wiadomości. '
            'Użyj bez <?podkomendy>, by dowiedzieć się więcej.',
        ),
        _Help.Command(
            ('głosowanie', 'glosowanie'), ('?liczba minut/data i godzina', 'sprawa'),
            'Przeprowadza głosowanie za/przeciw dotyczące <sprawy>. '
            'Ogłasza wynik po upływie podanego czasu, jeśli go podano.'
        ),
        _Help.Command(('pomógł', 'pomogl'), '?użytkownik Discorda', 'Oznacza pomocną wiadomość za pomocą reakcji.'),
        _Help.Command(
            ('niepomógł', 'niepomogl'), '?użytkownik Discorda', 'Oznacza niepomocną wiadomość za pomocą reakcji.'
        ),
        _Help.Command(
            ('hm', 'hmm', 'hmmm', 'hmmmm', 'hmmmmm', 'myśl', 'mysl', 'think', 'thinking', '🤔'),
            '?użytkownik Discorda', '🤔'
        ),
        _Help.Command(('^', 'to', 'this', 'up', 'upvote'), '?użytkownik Discorda', '⬆'),
        _Help.Command('f', '?użytkownik Discorda', 'F'),
        _Help.Command(
            ('zareaguj', 'reaguj', 'x'), ('?użytkownik Discorda', 'reakcje'),
            'Dodaje <reakcje> do ostatniej wiadomości wysłanej na kanale '
            '(jeśli podano <?użytkownika Discorda>, to ostatnią jego autorstwa na kanale).'
        ),
        _Help.Command('oof', (), 'Oof!'),
        _Help.Command(
            'oof ile', '?użytkownik Discorda',
            'Zlicza oofnięcia dla <?użytkownika Discorda> lub, jeśli nie podano <?użytkownika Discorda>, dla ciebie. '
        ),
        _Help.Command('oof serwer', (), 'Zlicza oofnięcia na serwerze i generuje ranking ooferów.'),
        _Help.Command(
            ('obróć', 'obroc', 'niewytrzymie'), ('?użytkownik', '?stopni/razy'),
            'Obraca ostatni załączony na kanale lub, jeśli podano <?użytkownika>, na kanale przez <?użytkownika> obrazek <?stopni/razy> (domyślnie 90 stopni/1 raz) zgodnie z ruchem wskazówek zegara.'
        ),
        _Help.Command(
            ('deepfry', 'usmaż', 'głębokosmaż', 'usmaz', 'glebokosmaz'),
            ('?użytkownik', '?poziom usmażenia'), 'Smaży ostatni załączony na kanale lub, jeśli podano <?użytkownika>, na kanale przez <?użytkownika> obrazek <?poziom usmażenia> razy (domyślnie 2 razy). '
        ),
        _Help.Command(
            ('robot9000', 'r9k', 'było', 'bylo', 'byo'),
            '?użytkownik', 'Sprawdza czy ostatnio załączony na kanale lub, jeśli podano <?użytkownika>, na kanale przez <?użytkownika> obrazek pojawił się wcześniej na serwerze.'
        ),
        _Help.Command('tableflip', (), '(╯°□°）╯︵ ┻━┻'),
        _Help.Command('unflip', (), '┬─┬ ノ( ゜-゜ノ)'),
        _Help.Command('shrug', (), r'¯\_(ツ)_/¯'),
        _Help.Command(('lenny', 'lennyface'), (), '( ͡° ͜ʖ ͡°)'),
        _Help.Command(('lenno', 'lennoface'), (), '( ͡ʘ ͜ʖ ͡ʘ)'),
        _Help.Command(('dej', 'gib'), '?rzecz', '༼ つ ◕_◕ ༽つ <?rzecz>'),
        _Help.Command(
            ('nie', 'nope', 'no'), (),
            'Usuwa ostatnią wiadomość wysłaną przez bota na kanale jako rezultat użytej przez ciebie komendy.'
        ),
        _Help.Command(
            ('warn', 'ostrzeż', 'ostrzez'), ('użytkownik Discorda', 'powód'),
            'Ostrzega <użytkownika Discorda>. '
            'Działa tylko dla członków serwera mających uprawnienia do wyrzucania innych.'
        ),
        _Help.Command(
            ('kick', 'wyrzuć', 'wyrzuc'), ('użytkownik Discorda', 'powód'),
            'Wyrzuca <użytkownika Discorda>. '
            'Działa tylko dla członków serwera mających uprawnienia do wyrzucania innych.'
        ),
        _Help.Command(
            ('ban', 'zbanuj'), ('użytkownik Discorda', 'powód'),
            'Banuje <użytkownika Discorda>. Działa tylko dla członków serwera mających uprawnienia do banowania innych.'
        ),
        _Help.Command(
            ('przebacz', 'pardon'), ('użytkownik Discorda'),
            'Usuwa wszystkie ostrzeżenia <użytkownika Discorda> na serwerze. '
            'Działa tylko dla członków serwera mających uprawnienia administratora.'
        ),
        _Help.Command(
            'kartoteka', ('?użytkownik Discorda', '?typy zdarzeń'),
            'Sprawdza kartotekę <?użytkownika Discorda> pod kątem <?typów zdarzeń>. '
            'Jeśli nie podano <?użytkownika Discorda>, przyjmuje ciebie. '
            'Jeśli nie podano typu <?typów zdarzeń>, zwraca wszystkie zdarzenia.'
        ),
        _Help.Command(
            ('wyczyść', 'wyczysc'), '?liczba',
            'Usuwa <?liczbę> ostatnich wiadomości z kanału lub, jeśli nie podano <?liczby>, jedną ostatnią wiadomość '
            'z kanału na którym użyto komendy. Działa tylko dla członków serwera mających uprawnienia '
            'do zarządzania wiadomościami na kanale.'
        ),
        _Help.Command(
            ('prefiks', 'prefix'), '?podkomenda',
            'Komendy związane z własnymi serwerowymi prefiksami komend. '
            'Użyj bez <?podkomendy>, by dowiedzieć się więcej.'
        ),
        _Help.Command(('ping', 'pińg'), (), 'Pong!'),
        _Help.Command(('wersja', 'v'), (), 'Działająca wersja bota.'),
        _Help.Command(('informacje', 'info'), (), 'Działająca wersja bota plus dodatkowe informacje.'),
    )
    DESCRIPTION = (
        'Somsiad jestem. Pomagam ludziom w różnych kwestiach. '
        'By skorzystać z mojej pomocy wystarczy wysłać komendę w miejscu, w którym będę mógł ją zobaczyć. '
        'Lista komend wraz z ich opisami znajduje się poniżej. '
        'Używając ich na serwerach pamiętaj o prefiksie (możesz zawsze sprawdzić go za pomocą '
        f'`{configuration["command_prefix"]}prefiks sprawdź`).\n'
        'W (nawiasach okrągłych) podane są aliasy komend.\n'
        'W <nawiasach ostrokątnych> podane są argumenty komend. Jeśli przed nazwą argumentu jest ?pytajnik, '
        'oznacza to, że jest to argument opcjonalny.'
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        description = self.DESCRIPTION + f'\nBy dowiedzieć się o mnie więcej, wejdź na {self.bot.WEBSITE_URL}.'
        self.HELP = _Help(self.COMMANDS, '👋', 'Dobry!', description)

    @commands.command(aliases=['help', 'pomocy', 'pomoc'])
    @cooldown()
    async def help_message(self, ctx):
        await self.bot.send(ctx, direct=True, embeds=self.HELP.embeds)


def setup(bot: commands.Bot):
    bot.add_cog(Help(bot))
