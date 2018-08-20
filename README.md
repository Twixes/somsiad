# Somsiad - po polsku  

Polski bot discordowy. Napisany w Pythonie.  

## Funkcje  

* wysyłanie emotikon (tableflip, shrug, lenny face itp.)  
* oznaczanie na żądanie pomocnych wiadomości za pomocą reakcji  
* Magic 8-Ball  
* kantor  
* wyszukiwanie stron i obrazków za pomocą [Google](https://www.google.com)  
* wyszukiwanie wideo na [YouTube](https://www.youtube.com)  
* wyszukiwanie artykułów w [Wikipedii](https://www.wikipedia.org) po polsku i po angielsku  
* wyszukiwanie definicji w [Urban Dictionary](https://www.urbandictionary.com)  
* sprawdzanie statusu stron za pomocą [isitup.org](https://isitup.org)  
* weryfikacja konta redditowego  

## Wymagania  

* Python 3.6 lub późniejszy.  

* Discordowy token bota. By go uzyskać utwórz aplikację w Portalu Deweloperskim Discorda i dodaj do niej bota:  
https://discordapp.com/developers/applications/me  

* Klucz API Google z obsługą YouTube Data API:  
https://console.developers.google.com/apis/dashboard  

* Klucz API Google z obsługą API YouTube Data i Google Custom Search Engine, a także identyfikator wyszukiwarki Google 
Custom Search Engine:  
https://console.developers.google.com/apis/dashboard  
https://cse.google.com/cse/all  
By twoja wyszukiwarka Google Custom Search Engine działała prawidłowo, musisz podczas jej tworzenia przypisać do niej 
dowolną stronę (może być to https://example.com). Następnie musisz udać się do zakładki Konfiguracja / Podstawy 
wyszukiwarki, usunąć dodaną stronę i zaznaczyć pola: "Wyszukiwarka grafiki" oraz "Wyszukiwanie w całej sieci".

* Nazwa użytkownika i hasło konta na Reddicie, a także ID i szyfr aplikacji redditowej typu skrypt:  
https://www.reddit.com/prefs/apps  

* Następujące paczki:  

  * libffi  
  * libnacl  
  * python3-dev  
  * python3-pip  
  * python3-wheel  
  * python3-venv  

  Na systemach opartych na Debianie możesz spełnić te zależności za pomocą `apt`:  
`$ sudo apt install libffi-dev libnacl-dev python3-dev python3-pip python3-wheel python3-venv`  

## Instalacja  

By nie zanieczyszczać swojego systemu, zainstaluj Somsiada w środowisku wirtualnym.  

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

# Somsiad - in English  

The Polish Discord bot. Written in Python.  

## Features  

* emoticon sending (tableflip, shrug, lenny face, etc.)  
* reacting to helpful messages on demand  
* Magic 8-Ball  
* currency exchange  
* website and image search powered by [Google](https://www.google.com)  
* [YouTube](https://www.youtube.com) video search  
* [Wikipedia](https://www.wikipedia.org) article search, in Polish and English  
* [Urban Dictionary](https://www.urbandictionary.com) definition search  
* website status check powered by [isitup.org](https://isitup.org)  
* Reddit account verification

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

* Reddit username and password, and also Reddit script application ID and secret:  
https://www.reddit.com/prefs/apps  

* The following packages:  

  * libffi  
  * libnacl  
  * python3-dev  
  * python3-pip  
  * python3-wheel  
  * python3-venv  

  On Debian-based systems you can satisfy those dependencies with `apt`:  
`$ sudo apt install libffi-dev libnacl-dev python3-dev python3-pip python3-wheel python3-venv`  

## Installation  

In order not to pollute your system, install Somsiad in a virtual environment.  

1. Grab a copy of the latest release:  
https://github.com/Twixes/Somsiad/releases/latest  

2. Unpack the downloaded archive and enter the newly created directory:  
`$ tar -xvf Somsiad-<version>.tar.gz`  
`$ cd Somsiad-<version>`  

3. Run the bot (you will be guided through a quick configuration process on the first run):  
`$ ./run.sh`  
or if you have `screen` installed:  
`$ screen -S Somsiad ./run.sh`  

4. Invite Somsiad to your server with the link provided in the console upon launch.  

## License  

The code of this project is licensed under GPLv3.  
