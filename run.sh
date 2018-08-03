#!/usr/bin/env bash

# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

if command -V python3 &>/dev/null
then
    if ! test -d somsiad_env
    then
        echo Tworzenie środowiska wirtualnego...
        python3 -m venv --system-site-packages somsiad_env
    fi
    source ./somsiad_env/bin/activate
    pip install --upgrade --quiet pip
    if ! command pip3 show discord.py &>/dev/null
    then
        pip3 install git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py[voice]
    fi
    if ! command pip3 show google-api-python-client &>/dev/null
    then
        pip3 install google-api-python-client
    fi
    if ! command pip3 show praw &>/dev/null
    then
        pip3 install praw
    fi
    if ! command pip3 show wikipedia &>/dev/null
    then
        pip3 install wikipedia
    fi
    echo Budzenie Somsiada...
    python3 somsiad.py
else
    echo W systemie nie znaleziono Pythona 3! Somsiad nie może wstać.
fi
