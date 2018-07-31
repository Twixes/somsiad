import discord
from discord.ext.commands import Bot
import os


client = Bot(description="Bot dyskorda /r/Polska", command_prefix=".")
client.remove_command('help')   # Replaced with 'help' plugin

# Check presence of config file holding user tokens

# If file doesn't exist, create one and ask for tokens on first run
conf_file = os.path.join(os.path.expanduser("~"), ".config", "somsiad.conf")
if not os.path.exists(conf_file):
    with open(conf_file, "w") as f:
        print("Wciśnij Enter by pominąć. Jeśli pominiesz ten etap będziesz mógł dodać tokeny w pliku ~/.config/somsiad.conf.")
        f.write("discord: " + str(input("Wprowadź token bota discordowego:\n")) + "\n")
        f.write("youtube: " + str(input("Wprowadź klucz API YouTube:\n")) + "\n")
    print("Ładowanie...")

# If file exists, fetch the keys.
dev_keys = {}
with open(conf_file) as f:
    for line in f.readlines():
        line = line.strip()
        line = line.split(":")
        dev_keys[line[0].strip()] = line[1].strip()

bot_dir = os.getcwd()
