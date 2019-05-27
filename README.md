# Somsiad – po polsku  

Polski bot discordowy. Napisany w Pythonie.  

## Funkcje  

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
* wyszukiwanie gifów na [Giphy](https://giphy.com/)  
* wyszukiwanie artykułów w [Wikipedii](https://www.wikipedia.org) w dowolnym języku  
* wyszukiwanie filmów i seriali w [OMDb](https://www.omdbapi.com/)  
* wyszukiwanie książek w [goodreads](https://www.goodreads.com)  
* tłumaczenie tekstu z [Yandex](https://translate.yandex.com/)  
* udostępnianie obecnie słuchanego na Spotify utworu  
* udostępnianie obecnie lub ostatnio słuchanego przez Last.fm utworu  
* wyszukiwanie definicji w [Urban Dictionary](https://www.urbandictionary.com)  
* wymiana walut za pomocą [CryptoCompare.com](https://www.cryptocompare.com/)  
* sprawdzanie statusu stron za pomocą [isitup.org](https://isitup.org)  
* weryfikacja konta na [Reddicie](https://www.reddit.com/)  
* rozpoczynanie głosowań z opcją opublikowania wyników po określonym czasie
* obliczanie wartości wyrażeń matematycznych  
* zapamiętywanie urodzin użytkowników serwera  
* statystyki serwera/kanału/użytkownika (wraz z generowaniem wykresu aktywności)  
* funkcje moderacyjne: ostrzeganie, wyrzucanie, banowanie  
* rejestrowanie zdarzeń związanych z członkami serwera (ostrzeżenia, wyrzucenia, bany, dołączenia, opuszczenia)  
* archiwizacja przypiętych wiadomości do wyznaczego kanału  

## Wymagania  

* Python 3.6 lub późniejszy.  

* Discordowy token bota. By go uzyskać utwórz aplikację w Portalu Deweloperskim Discorda i dodaj do niej bota:  
https://discordapp.com/developers/applications/me  

* Klucz API Google z obsługą API YouTube Data i Google Custom Search Engine, a także identyfikator wyszukiwarki Google 
Custom Search Engine:  
https://console.developers.google.com/apis/dashboard  
https://cse.google.com/cse/all  
By twoja wyszukiwarka Google Custom Search Engine działała prawidłowo, musisz podczas jej tworzenia przypisać do niej 
dowolną stronę (może być to https://example.com). Następnie musisz udać się do zakładki Konfiguracja / Podstawy 
wyszukiwarki, usunąć dodaną stronę i zaznaczyć pola: "Wyszukiwarka grafiki" oraz "Wyszukiwanie w całej sieci".  

* Klucz API Giphy:  
https://developers.giphy.com/  

* Klucz API goodreads:  
https://www.goodreads.com/api  

* Klucz API OMDb:  
https://www.omdbapi.com/apikey.aspx  

* Klucz API Yandex Translate:  
https://translate.yandex.com/developers/keys  

* Klucz API Last.fm:  
https://www.last.fm/api/account/create  

* Nazwa użytkownika i hasło konta na Reddicie, a także ID i szyfr aplikacji redditowej typu skrypt:  
https://www.reddit.com/prefs/apps  

* Następujące paczki:  

  * python3-dev  
  * python3-pip  
  * python3-wheel  
  * python3-venv  
  * libffi  
  * libnacl  
  * libopus  
  * ffmpeg  
  * libjpeg

  A także paczkę wsparcia języka polskiego dla twojego systemu.  
Na systemach opartych na Debianie możesz spełnić te zależności za pomocą `apt`:  
`$ sudo apt install language-pack-pl-base python3-dev python3-pip python3-wheel python3-venv libffi-dev libnacl-dev libopus-dev ffmpeg libjpeg-dev`  

## Instalacja  

1. Pobierz kopię najnowszego wydania:  
https://github.com/Twixes/Somsiad/releases/latest  

2. Rozpakuj pobrane archiwum i wejdź do nowo utworzonego katalogu:  
`$ tar -xvf Somsiad-<wersja>.tar.gz`  
`$ cd Somsiad-<wersja>`  

3. Uruchom bota (przy pierwszym uruchomieniu zostaniesz przeprowadzony przez krótki proces konfiguracji):  
`$ ./run.sh`  
lub jeśli masz `screen`:  
`$ screen -S Somsiad ./run.sh`  

4. Zaproś Somsiada na swój serwer za pomocą linku podanego w konsoli po uruchomieniu.  

## Licencja  

Kod tego projektu udostępniony jest na licencji GPLv3.  

---

# Somsiad – in English  

The Polish Discord bot. Written in Python.  

## Features  

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
* [Giphy](https://giphy.com/) gif search  
* [Wikipedia](https://www.wikipedia.org) article search, in Polish and English  
* [OMDb](https://www.omdbapi.com/) movie and TV show search  
* [goodreads](https://www.goodreads.com) book search  
* text translation powered by [Yandex](https://translate.yandex.com/)  
* sharing the song currently played on Spotify  
* sharing the song currently or previously played with Last.fm  
* [Urban Dictionary](https://www.urbandictionary.com) definition search  
* currency exchange powered by [CryptoCompare.com](https://www.cryptocompare.com/)  
* website status check powered by [isitup.org](https://isitup.org)  
* [Reddit](https://www.reddit.com/) account verification  
* vote commencement with optional publication of results after a specified amount of time
* calculation of mathematical expressions  
* remembering birthdays of server members  
* server/channel/user statistics (with activity chart generation)  
* moderation commands: warn, kick, ban  
* recording of server member events (warnings, kicks, bans, joinings, leavings)  
* archivization of pinned messages to a specified channel  

## Prerequisites  

* Python 3.6 or later.  

* A Discord bot token. In order to obtain it create an app in the Discord Developer Portal and add a bot to it:  
https://discordapp.com/developers/applications/me  

* A Google API key with YouTube Data and Google Custom Search Engine APIs support, and also a Google Custom Search 
Engine's identifier:  
https://console.developers.google.com/apis/dashboard  
https://cse.google.com/cse/all  
In order to make your Google Custom Search Engine work correctly, you must assign any website to it during creation 
(it might as well be https://example.com). Then you must go into the CSE's Setup / Basics, remove the website and 
check boxes: "Image search" and "Search the entire web".  

* A Giphy API key:  
https://developers.giphy.com/  

* A goodreads API key:  
https://www.goodreads.com/api  

* An OMDb API key:  
https://www.omdbapi.com/apikey.aspx  

* A Yandex Translate API key:  
https://translate.yandex.com/developers/keys  

* A Last.fm API key:  
https://www.last.fm/api/account/create  

* Reddit username and password, and also Reddit script application ID and secret:  
https://www.reddit.com/prefs/apps  

* The following packages:  

  * python3-dev  
  * python3-pip  
  * python3-wheel  
  * python3-venv  
  * libffi  
  * libnacl  
  * libopus  
  * ffmpeg
  * libjpeg

  And also whatever the Polish language support package is for your system.  
On Debian-based systems you can satisfy those dependencies with `apt`:  
`$ sudo apt install language-pack-pl-base python3-dev python3-pip python3-wheel python3-venv libffi-dev libnacl-dev libopus-dev ffmpeg libjpeg-dev`  

## Installation  

1. Grab a copy of the latest release:  
https://github.com/Twixes/Somsiad/releases/latest  

2. Unpack the downloaded archive and enter the newly created directory:  
`$ tar -xvf Somsiad-<version>.tar.gz`  
`$ cd Somsiad-<version>`  

3. Run the bot (you will be guided through configuration on the first run):  
`$ ./run.sh`  
or if you have `screen` installed:  
`$ screen -S Somsiad ./run.sh`  

4. Invite Somsiad to your server with the link provided in the console upon launch.  

## License  

The code of this project is licensed under GPLv3.  
