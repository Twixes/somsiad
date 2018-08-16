import discord
from discord.ext import commands
from version import __version__
from somsiad_helper import *

@client.command(aliases=['pomógł', 'pomogl'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def helped(ctx, *args):
    """Adds "POMOGL" to the provided user's last non-command message in the form of reactions.
        If no user was provided, adds "POMOGL" to the last non-command message sent by any non-bot user."""
    reactions = ('🇵', '🇴', '🇲', '🅾', '🇬', '🇱')
    was_message_found = False

    if len(args) == 0:
        async for message in ctx.channel.history(limit=5):
            if (not was_message_found and not message.author.bot and
                not message.content.startswith(conf['command_prefix'])):
                for reaction in reactions:
                    await message.add_reaction(reaction)
                was_message_found = True

    else:
        if len(args) == 1 and args[0].startswith('<@') and args[0].endswith('>'):
            commended_user = ctx.guild.get_member(int(args[0].strip('<@!>')))
        else:
            commended_user_username = ''
            for arg in args:
                commended_user_username += arg + ' '
            commended_user_username = commended_user_username.strip()
            commended_user = ctx.guild.get_member_named(commended_user_username)

        async for message in ctx.channel.history(limit=10):
            message.content
            if (not was_message_found and message.author == commended_user and
                not message.content.startswith(conf['command_prefix'])):
                for reaction in reactions:
                    await message.add_reaction(reaction)
                was_message_found = True
