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
    if command -V pip3 &>/dev/null
    then
        if ! test -d somsiad_env
        then
            echo Tworzenie środowiska wirtualnego...
            python3 -m venv --system-site-packages somsiad_env
        fi
        source ./somsiad_env/bin/activate
        echo Spełnianie zależności...
        pip3 install -q -r requirements.txt
        echo Budzenie Somsiada...
        python3 somsiad.py
    else
        echo W systemie nie znaleziono menedżera paczek pip3! Somsiad nie może wstać.
    fi
else
    echo W systemie nie znaleziono Pythona 3! Somsiad nie może wstać.
fi
