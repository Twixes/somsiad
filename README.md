# Somsiad

Somsiad.py - a Discord bot written for the /r/Polska server.

## Features

* 8-Ball
* simple text replies
* image search using Qwant
* checking the current status of websites with isitup.org
* Wikipedia search in Polish and English
* Urban Dictionary definitions
* YouTube search

## Requirements

* Python 3.5.3 or newer.

* A Discord bot token. In order to obtain it create an app in the Discord Developer Portal and add a bot to it:  
https://discordapp.com/developers/applications/me

* *optionally* A YouTube API token (if you want YouTube search):  
https://console.developers.google.com/apis/dashboard

* In Linux environments, the following dependencies of discord.py:  

  * libffi
  * libnacl
  * python3-dev
  * python3-pip
  * python3-wheel
  * python3-venv

  On Debian-based systems you can satisfy them with `apt`:  
`$ sudo apt install libffi-dev libnacl-dev python3-dev python3-pip python3-wheel python3-venv`

## Installation

In order not to pollute your system, install Somsiad in a virtual environment.

1. Grab a copy of the latest release:  
  https://github.com/ondondil/somsiad/releases

2. Unpack the downloaded package and enter the newly created directory:  
`$ tar -xvf somsiad.tar.gz`  
`$ cd somsiad`

3. Run the bot (you will be asked to provide tokens on the first run):  
`$ ./run.sh`

4. Invite Somsiad to your server with the link provided upon launch.

## License

The code in this project is licensed under GPLv3.
