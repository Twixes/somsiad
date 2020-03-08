***[polski](#somsiad--po-polsku), [English](#somsiad--in-english)***

---

# Somsiad – po polsku  

Polski bot discordowy. Napisany w Pythonie.  

## Funkcje  

* własny serwerowowy prefiks komend  
* odtwarzanie muzyki na czacie głosowym  
* wysyłanie emotikon (tableflip, shrug, lenny face itp.)  
* Magic 8-Ball  
* wybieranie jednej z podanych opcji
* rzucanie kośćmi do gry  
* reagowanie na wiadomości podanymi znakami  
* liczenie oofnięć  
* odliczanie do końca roku szkolnego (w Polsce)  
* wyszukiwanie stron i obrazków za pomocą [Google](https://www.google.com)  
* wyszukiwanie wideo na [YouTube](https://www.youtube.com)  
* wyszukiwanie artykułów w [Wikipedii](https://www.wikipedia.org) w dowolnym języku  
* wyszukiwanie filmów i seriali w [TMDb](https://www.themoviedb.org/)  
* wyszukiwanie książek w [goodreads](https://www.goodreads.com)  
* tłumaczenie tekstu z [Yandex](https://translate.yandex.com/)  
* uzyskiwanie informacji i przeprowadzanie obliczeń z [Wolfram Alpha](https://www.wolframalpha.com/)  
* udostępnianie obecnie słuchanego na [Spotify](https://spotify.com) utworu  
* udostępnianie obecnie lub ostatnio słuchanego przez [Last.fm](https://last.fm) utworu  
* wyszukiwanie definicji w [Urban Dictionary](https://www.urbandictionary.com)  
* informacje o subredditach i użytkownikach [Reddita](https://reddit.com)  
* rozpoczynanie głosowań z opcją opublikowania wyników po określonym czasie  
* przypomienia  
* zapamiętywanie urodzin użytkowników serwera i automatyczne składanie życzeń  
* statystyki aktywności serwera/kanału/użytkownika wraz z wykresami  
* samodzielne wybieranie koloru nicku przez użytkowników  
* archiwizacja przypiętych wiadomości do wyznaczego kanału  
* funkcje moderacyjne: ostrzeganie, wyrzucanie, banowanie  
* rejestrowanie zdarzeń związanych z członkami serwera (ostrzeżenia, wyrzucenia, bany, dołączenia, opuszczenia)  

## Wymagania  

* Python 3.6+.  

* Discordowy token bota. By go uzyskać utwórz aplikację w Portalu Deweloperskim Discorda i dodaj do niej bota:  
https://discordapp.com/developers/applications/me  

* Klucz API Google z obsługą API YouTube Data i Google Custom Search Engine, a także identyfikator wyszukiwarki Google 
Custom Search Engine:  
https://console.developers.google.com/apis/dashboard  
https://cse.google.com/cse/all  
By twoja wyszukiwarka Google Custom Search Engine działała prawidłowo, musisz podczas jej tworzenia przypisać do niej 
dowolną stronę (może być to https://example.com). Następnie musisz udać się do zakładki Konfiguracja / Podstawy 
wyszukiwarki, usunąć dodaną stronę i zaznaczyć pola: "Wyszukiwarka grafiki" oraz "Wyszukiwanie w całej sieci".  

* Klucz API goodreads:  
https://www.goodreads.com/api  

* Klucz API TMDb:  
https://developers.themoviedb.org/3/getting-started/introduction  

* Klucz API Yandex Translate:  
https://translate.yandex.com/developers/keys  

* Klucz API Last.fm:  
https://www.last.fm/api/account/create  

* Następujące paczki:  

  * python3-dev  
  * python3-pip  
  * python3-wheel  
  * python3-venv  
  * libffi  
  * libnacl  
  * libopus  
  * libjpeg  
  * ffmpeg  

  A także paczkę wsparcia języka polskiego dla twojego systemu.  
Na systemach opartych na Debianie możesz spełnić te zależności za pomocą `apt`:  
`$ sudo apt install language-pack-pl-base python3-dev python3-pip python3-wheel python3-venv libffi-dev libnacl-dev libopus-dev libjpeg-dev ffmpeg`  

## Instalacja  

1. Pobierz kopię najnowszego wydania:  
https://github.com/Twixes/somsiad/releases/latest  

2. Rozpakuj pobrane archiwum i wejdź do nowo utworzonego katalogu:  
`$ tar -xvf somsiad-<wersja>.tar.gz`  
`$ cd somsiad-<wersja>`  

3. Uruchom bota:  
`$ ./run.sh`  
Lub jeśli masz `screen`:  
`$ screen -S somsiad ./run.sh`  

4. Zapraszaj Somsiada na serwery za pomocą linku podanego w konsoli po uruchomieniu.  

## Licencja  

Kod tego projektu udostępniony jest na licencji GPLv3.  

---

# Somsiad – in English  

The Polish Discord bot. Written in Python.  

## Features  

* custom server command prefix  
* music playback over voice chat  
* emoticon sending (tableflip, shrug, lenny face, etc.)  
* Magic 8-Ball  
* choosing one of provided options
* dice rolling  
* reacting to messages with given characters  
* oof counting  
* counting down to the end of the school year (in Poland)  
* website and image search powered by [Google](https://www.google.com)  
* [YouTube](https://www.youtube.com) video search  
* [Wikipedia](https://www.wikipedia.org) article search, in Polish and English  
* [TMDb](https://www.themoviedb.org/) movie and TV show search  
* [goodreads](https://www.goodreads.com) book search  
* [TMDb](https://www.themoviedb.org/) movie and TV show search  
* text translation powered by [Yandex](https://translate.yandex.com/)  
* obtaining information and making calculations with [Wolfram Alpha](https://www.wolframalpha.com/)  
* sharing the song currently played on [Spotify](https://spotify.com)  
* sharing the song currently or previously played with [Last.fm](https://last.fm)  
* [Urban Dictionary](https://www.urbandictionary.com) definition search  
* subreddit and [Reddit](https://reddit.com) user information  
* vote commencement with optional publication of results after a specified amount of time  
* reminders  
* calculation of mathematical expressions  
* remembering birthdays of server members and automatic wishes  
* server/channel/user activity statistics with charts  
* self-selection of nick color by users  
* moderation commands: warn, kick, ban  
* recording of server member events (warnings, kicks, bans, joinings, leavings)  
* archivization of pinned messages to a specified channel  

## Prerequisites  

* Python 3.6+.  

* A Discord bot token. In order to obtain it create an app in the Discord Developer Portal and add a bot to it:  
https://discordapp.com/developers/applications/me  

* A Google API key with YouTube Data and Google Custom Search Engine APIs support, and also a Google Custom Search 
Engine's identifier:  
https://console.developers.google.com/apis/dashboard  
https://cse.google.com/cse/all  
In order to make your Google Custom Search Engine work correctly, you must assign any website to it during creation 
(it might as well be https://example.com). Then you must go into the CSE's Setup / Basics, remove the website and 
check boxes: "Image search" and "Search the entire web".  

* A goodreads API key:  
https://www.goodreads.com/api  

* A TMDb API key:  
https://developers.themoviedb.org/3/getting-started/introduction  

* A Yandex Translate API key:  
https://translate.yandex.com/developers/keys  

* A Last.fm API key:  
https://www.last.fm/api/account/create  

* The following packages:  

  * python3-dev  
  * python3-pip  
  * python3-wheel  
  * python3-venv  
  * libffi  
  * libnacl  
  * libopus  
  * libjpeg  
  * ffmpeg  

  And also whatever the Polish language support package is for your system.  
On Debian-based systems you can satisfy those dependencies with `apt`:  
`$ sudo apt install language-pack-pl-base python3-dev python3-pip python3-wheel python3-venv libffi-dev libnacl-dev libopus-dev libjpeg-dev ffmpeg`  

## Installation  

1. Grab a copy of the latest release:  
https://github.com/Twixes/somsiad/releases/latest  

2. Unpack the downloaded archive and enter the newly created directory:  
`$ tar -xvf somsiad-<version>.tar.gz`  
`$ cd somsiad-<version>`  

3. Run the bot:  
`$ ./run.sh`  
Or if you have `screen` installed:  
`$ screen -S somsiad ./run.sh`  

4. Invite Somsiad to servers with the link provided in the console upon launch.  

## License  

The code of this project is licensed under GPLv3.  
