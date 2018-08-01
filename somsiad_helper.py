import discord
from discord.ext.commands import Bot
import os


client = Bot(description="Bot dyskorda /r/Polska", command_prefix="!")
client.remove_command('help') # Replaced with 'help' plugin

# Check presence of config file holding user tokens

# If file doesn't exist, create one and ask for tokens on first run
conf_file = os.path.join(os.path.expanduser("~"), ".config", "somsiad.conf")
if not os.path.exists(conf_file):
    with open(conf_file, "w") as f:
        f.write("discord: " + str(input("Wprowadź discordowy token bota:\n")) + "\n")
        f.write("youtube: " + str(input("Wprowadź klucz API YouTube (lub pomiń ten krok, jeśli nie chcesz funkcji YT):\n")) + "\n")
        f.write("cooldown: " + str(input("Wprowadź cooldown między wywołaniami bota przez danego użytkownika (w s):\n")) + "\n")
        print("Konfiguracja zapisana w " + os.path.expanduser("~") + "/.config/somsiad.conf.")
    print("Budzenie Somsiada...")

# If file exists, fetch the keys.
conf = {}
with open(conf_file) as f:
    for line in f.readlines():
        line = line.strip()
        line = line.split(":")
        conf[line[0].strip()] = line[1].strip()

bot_dir = os.getcwd()
