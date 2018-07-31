#!/bin/bash

if command -V python3 &>/dev/null
then
    if ! test -d somsiad_env
    then
        echo Tworzenie środowiska wirtualnego...
        python3 -m venv --system-site-packages somsiad_env
    fi
    source ./somsiad_env/bin/activate
    if ! command pip3 show wikipedia &>/dev/null
    then
        pip3 install wikipedia
    fi
    if ! command pip3 show google-api-python-client &>/dev/null
    then
        pip3 install google-api-python-client
    fi
    if ! command pip3 show discord.py &>/dev/null
    then
        pip3 install git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py[voice]
    fi
    echo Budzenie Somsiada...
    python3 somsiad.py
else
    echo W systemie nie znaleziono Pythona 3! Somsiad nie może wstać.
fi
