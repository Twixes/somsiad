# Somsiad - polski  

Polski bot discordowy. Napisany w Pythonie.  

## Funkcje  

* automatyczne odpowiedzi  
* Magic 8-Ball  
* wyszukiwanie obrazków za pomocą [Qwant](https://www.qwant.com)  
* wyszukiwanie wideo na [YouTube](https://www.youtube.com)  
* wyszukiwanie artykułów w [Wikipedii](https://www.wikipedia.org) po polsku i po angielsku  
* wyszukiwanie definicji w [Urban Dictionary](https://www.urbandictionary.com)  
* sprawdzanie statusu stron za pomocą [isitup.org](https://isitup.org)  

## Wymagania  

* Python 3.6 lub późniejszy.  

* Discordowy token bota. By go uzyskać utwórz aplikację w Portalu Deweloperskim Discorda i dodaj do niej bota:  
https://discordapp.com/developers/applications/me  

* *opcjonalnie* Klucz API Google z obsługą YouTube Data API (jeśli chcesz korzystać z wyszukiwarki wideo):  
https://console.developers.google.com/apis/dashboard  

* Następujące paczki:  

  * libffi  
  * libnacl  
  * python3-dev  
  * python3-pip  
  * python3-wheel  
  * python3-venv  

  Na systemach opartych o Debiana możesz spełnić te zależności za pomocą `apt`:  
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

# Somsiad - English  

The Polish Discord bot. Written in Python.  

## Features  

* automatic replies  
* Magic 8-Ball  
* image search powered by [Qwant](https://www.qwant.com)  
* [YouTube](https://www.youtube.com) video search  
* [Wikipedia](https://www.wikipedia.org) article search, in Polish and English  
* [Urban Dictionary](https://www.urbandictionary.com) definition search  
* website status check powered by [isitup.org](https://isitup.org)  

## Prerequisites  

* Python 3.6 or later.  

* A Discord bot token. In order to obtain it create an app in the Discord Developer Portal and add a bot to it:  
https://discordapp.com/developers/applications/me  

* *optionally* A Google API key with YouTube Data API support (if you want YouTube video search):  
https://console.developers.google.com/apis/dashboard  

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

3. Run the bot (on the first run you will be guided through a quick configuration process):  
`$ ./run.sh`  
or if you have `screen` installed:  
`$ screen -S Somsiad ./run.sh`  

4. Invite Somsiad to your server with the link provided in the console upon launch.  

## License  

The code of this project is licensed under GPLv3.  
