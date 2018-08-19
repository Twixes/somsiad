import discord
from discord.ext import commands
from version import __version__
from somsiad_helper import *

async def smart_add_reactions(server, channel, args, reactions):
    """Adds provided emojis to the specified user's last non-command message in the form of reactions.
        If no user was specified, adds emojis to the last non-command message sent by any non-bot user
        in the given channel."""
    was_message_found = False

    if len(args) == 0:
        async for message in channel.history(limit=5):
            if (not was_message_found and not message.author.bot and
                not message.content.startswith(conf['command_prefix'])):
                for reaction in reactions:
                    await message.add_reaction(reaction)
                was_message_found = True

    else:
        async for message in channel.history(limit=10):
            if (not was_message_found and message.author == get_fellow_server_member(server, args) and
                not message.content.startswith(conf['command_prefix'])):
                for reaction in reactions:
                    await message.add_reaction(reaction)
                was_message_found = True


@client.command(aliases=['pomógł', 'pomogl'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def helped(ctx, *args):
    """Adds "POMOGL" with smart_add_reactions()."""
    reactions = ('🇵', '🇴', '🇲', '🅾', '🇬', '🇱')
    await smart_add_reactions(ctx.guild, ctx.channel, args, reactions)

@client.command(aliases=['niepomógł', 'niepomogl'])
@commands.cooldown(1, conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def didnothelp(ctx, *args):
    """Adds "NIEPOMOGL" with smart_add_reactions()."""
    reactions = ('🇳', '🇮', '🇪', '🇵', '🇴', '🇲', '🅾', '🇬', '🇱')
    await smart_add_reactions(ctx.guild, ctx.channel, args, reactions)
