#!/usr/bin/env bash

# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

echo "UWAGA: Ta metoda uruchamiania bota jest przestarzała!"
echo "UWAGA: Użyj Dockera!"

if [[ ${1::1} == "!" ]]
then
    OPTIONS="-m cProfile -s tottime -o somsiad.cprof"
    OPTIONS_PRESENTATION=" z profilowaniem"
    ARGUMENT=${1:1}
else
    ARGUMENT=$1
fi

if [ ! -z "$ARGUMENT" ]
then
    if command -V python$ARGUMENT &>/dev/null
    then
        PYTHON_VERSION_PRESENTATION="$(python$ARGUMENT -V)"
        if [[ $PYTHON_VERSION_PRESENTATION == "Python 3.7."* ]] || [[ $PYTHON_VERSION_PRESENTATION == "Python 3.8."* ]]
        then
            PYTHON_VERSION="$ARGUMENT"
        else
            echo "Podana komenda python$ARGUMENT to $PYTHON_VERSION_PRESENTATION, nie obsługiwany 3.7.* lub 3.8.*!"
        fi
    else
        echo "Podana komenda python$ARGUMENT nie działa!"
    fi
else
    if command -V python3 &>/dev/null
    then
        PYTHON_VERSION_PRESENTATION="$(python3 -V)"
        if [[ $PYTHON_VERSION_PRESENTATION == "Python 3.7."* ]] || [[ $PYTHON_VERSION_PRESENTATION == "Python 3.8."* ]]
        then
            PYTHON_VERSION="3"
        fi
    fi
    if [ -z "$PYTHON_VERSION" ]
    then
        if command -V python3.8 &>/dev/null
        then
            PYTHON_VERSION="3.8"
        elif command -V python3.7 &>/dev/null
        then
            PYTHON_VERSION="3.7"
        fi
    fi
fi

if [ ! -z "$PYTHON_VERSION" ]
then
        python$PYTHON_VERSION -m venv $(dirname "$BASH_SOURCE")/somsiad_env
        source $(dirname "$BASH_SOURCE")/somsiad_env/bin/activate
        echo "Spełnianie zależności..."
        pip$PYTHON_VERSION install -q -U pip
        pip$PYTHON_VERSION install -q -U -r $(dirname "$BASH_SOURCE")/requirements.txt
        echo "Uruchamianie$OPTIONS_PRESENTATION przy użyciu python$PYTHON_VERSION..."
        python$PYTHON_VERSION $OPTIONS $(dirname "$BASH_SOURCE")/run.py
elif [ -z "$ARGUMENT" ]
then
    if [ -z "$PYTHON_VERSION_PRESENTATION" ]
    then
        echo "Zainstalowany jest $PYTHON_VERSION, nie obsługiwany 3.7.* lub 3.8.*!"
    else
        echo "W systemie nie znaleziono Pythona 3!"
    fi
fi
