import discord
from discord.ext.commands import Bot
import os


client = Bot(description="Bot dyskorda r/polska", command_prefix=".")
client.remove_command('help')   # Replaced with 'help' plugin

# Check presence of config file holding user tokens

# If file doesn't exist, create one and ask for tokens on first run
conf_file = os.path.join(os.path.expanduser("~"), ".config", "somsiad.conf")
if not os.path.exists(conf_file):
    with open(conf_file, "w") as f:
        print("Press Enter to skip. If you skip this step you'll be able to add tokens later" + 
            " in ~/.config/somsiad.conf file.")
        f.write("discord: " + str(input("Please input Discord Bot token:\n")) + "\n")
        f.write("youtube: " + str(input("Please input YouTube API key:\n")) + "\n")
    print("Loading...")

# If file exists, fetch the keys.
dev_keys = {}
with open(conf_file) as f:
    for line in f.readlines():
        line = line.strip()
        line = line.split(":")
        dev_keys[line[0].strip()] = line[1].strip()

bot_dir = os.getcwd()
