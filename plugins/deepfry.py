# Copyright 2019 Slavfox

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with Somsiad. If not, see <https://www.gnu.org/licenses/>.
from typing import BinaryIO, Optional, Tuple
from io import BytesIO
from random import choice
from PIL import Image, ImageEnhance
import discord
from somsiad import somsiad

_DEEPFRY_EMOJI = (
    ':shallow_pan_of_food:',
    ':fried_shrimp:',
    ':fries:',
    ':cooking:',
    ':stew:'
)


def deepfry_image(im: BinaryIO):
    image = Image.open(im)
    image = ImageEnhance.Contrast(image).enhance(1.5)
    image = ImageEnhance.Sharpness(image).enhance(2)
    result = BytesIO()
    image.save(result, 'JPEG', quality=1)
    return result


async def find_attached_image(
    message: discord.Message
) -> Tuple[Optional[str], Optional[BinaryIO]]:
    filename = None
    image = None
    for attachment in message.attachments:
        if attachment.height and attachment.width:
            try:
                tmp = BytesIO()
                await attachment.save(tmp)
            except (discord.HTTPException, discord.NotFound):
                pass
            else:
                filename = attachment.filename
                image = tmp
                break
    return filename, image


@somsiad.bot.command(aliases=['usmaż', 'głębokosmaż', 'usmaz', 'glebokosmaz'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'],
    discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def deepfry(ctx: discord.ext.commands.context.Context):
    """
    Deepfries an image.
    Deepfries the attached image, or, if there is none, the last image sent
    in the channel.
    """
    filename, input_image = await find_attached_image(ctx.message)
    if not input_image:
        async for message in ctx.history(limit=15):
            filename, input_image = await find_attached_image(message)
            if input_image:
                break
        else:
            embed = discord.Embed(
                title=':warning: Nie znaleziono obrazka do usmażenia!',
                color=somsiad.color
            )
            return await ctx.send(ctx.author.mention, embed=embed)
    output_image = deepfry_image(input_image)
    return await ctx.send(
        choice(_DEEPFRY_EMOJI),
        file=discord.File(output_image, filename=filename or 'deepfried.jpg')
    )
