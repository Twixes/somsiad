#!/usr/bin/env bash

# Copyright 2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

ARGUMENT=$1
VENV_DIR="$(dirname "$BASH_SOURCE")/venv"

if [ ! -z "$ARGUMENT" ]
then
    if command -V python$ARGUMENT &>/dev/null
    then
        PYTHON_VERSION_PRESENTATION="$(python$ARGUMENT -V)"
        if [[ $PYTHON_VERSION_PRESENTATION == "Python 3.8."* ]] || [[ $PYTHON_VERSION_PRESENTATION == "Python 3.9."* ]]
        then
            PYTHON_VERSION="$ARGUMENT"
        else
            echo "Podana komenda python$ARGUMENT to $PYTHON_VERSION_PRESENTATION, nie obsługiwany 3.8.* lub 3.9.*!"
        fi
    else
        echo "Podana komenda python$ARGUMENT nie działa!"
    fi
else
    if command -V python3 &>/dev/null
    then
        PYTHON_VERSION_PRESENTATION="$(python3 -V)"
        if [[ $PYTHON_VERSION_PRESENTATION == "Python 3.8."* ]] || [[ $PYTHON_VERSION_PRESENTATION == "Python 3.9."* ]]
        then
            PYTHON_VERSION="3"
        fi
    fi
    if [ -z "$PYTHON_VERSION" ]
    then
        if command -V python3.9 &>/dev/null
        then
            PYTHON_VERSION="3.9"
        elif command -V python3.8 &>/dev/null
        then
            PYTHON_VERSION="3.8"
        fi
    fi
fi

if [ ! -z "$PYTHON_VERSION" ]
then
        if [[ -d $VENV_DIR ]]
        then
            echo "Usuwanie starego środowiska wirtualnego..."
            rm -rf $VENV_DIR
        fi
        echo "Tworzenie świeżego środowiska wirtualnego..."
        python$PYTHON_VERSION -m venv $VENV_DIR
        source $VENV_DIR/bin/activate
        echo "Aktualizowanie paczek podstawowych..."
        python$PYTHON_VERSION -m pip install -U pip setuptools wheel
        echo "Instalowanie zależności produkcyjnych..."
        python$PYTHON_VERSION -m pip install -U -r $(dirname "$BASH_SOURCE")/requirements.txt
        echo "Instalowanie zależności deweloperskich..."
        python$PYTHON_VERSION -m pip install -U -r $(dirname "$BASH_SOURCE")/requirements-dev.txt
        echo "Instalowanie pre-commit hooków..."
        pre-commit install
        echo "Gotowe."
elif [ -z "$ARGUMENT" ]
then
    if [ -z "$PYTHON_VERSION_PRESENTATION" ]
    then
        echo "Zainstalowany jest $PYTHON_VERSION, nie obsługiwany 3.8.* lub 3.9.*!"
    else
        echo "W systemie nie znaleziono Pythona 3!"
    fi
fi
