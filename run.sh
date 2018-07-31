if command -V python3 &>/dev/null
then
    python3 -m venv --system-site-packages somsiad_env
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
    python3 somsiad.py
else
    echo Somsiad nie może wstać, bo w systemie nie znaleziono Pythona 3!
fi
