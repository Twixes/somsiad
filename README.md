### Somsiad
somsiad.py - discord bot written specifically for r/polska discord server.

## Features
* 8ball
* Simple text responses
* Image search using Qwant
* Checking the current status of websites with isitup.org
* Wikipedia search in Polish and English
* Urban Dictionary definitions
* YouTube search

## Installing / Getting started

# Requirements
You'll need to create new app and get a bot token here: 
https://discordapp.com/developers/applications/me

If you want Youtube Search plugin to work then you'll need YouTube API token. Get it here: 
https://console.developers.google.com/apis/dashboard

Python 3.5.3 or higher is required.

On Linux environments, the following dependencies are required for discord.py:
* libffi
* libnacl
* python3-dev

On debian-based system, the following command will help get those dependencies:
`$ sudo apt install libffi-dev libnacl-dev python3-dev`

# Installation
In order not to pollute your system, install this in virtual environment.

1. Grab a copy of the latest release here:


2. Unpack the downloaded package and open working directory:
`tar -xzvf`
`cd somsiad_bot`

3. In your working directory, create virtual environment:
`python3 -m venv --system-site-packages somsiad_env`

3. Activate the virtual environment
`source ./somsiad_env/bin/activate`

4. Use pip to install required packages
`pip3 install wikipedia google-api-python-client git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py[voice]`

5. Run the bot and follow the instructions (the bot will ask you to provide your tokens on first run):
`python3 somsiad.py`

7. Invite your bot to your server with link printed to the console.

## Licensing
The code in this project is licensed under GPLv3 license.
