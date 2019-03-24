# Copyright 2019 Slavfox & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import BinaryIO, Optional, Tuple
import io
import PIL.Image, PIL.ImageEnhance
import discord
from somsiad import somsiad

class DeepFrier:
    @staticmethod
    def fry(image_bytes: BinaryIO, number_of_passes: int) -> BinaryIO:
        if number_of_passes < 1:
            number_of_passes = 1
        elif number_of_passes > 3:
            number_of_passes = 3
        for _ in range(number_of_passes):
            image = PIL.Image.open(image_bytes).convert('RGB')
            image = PIL.ImageEnhance.Contrast(image).enhance(2)
            image = PIL.ImageEnhance.Sharpness(image).enhance(2)
            image_bytes = io.BytesIO()
            image.save(image_bytes, 'JPEG', quality=1)
            image_bytes.seek(0)
        return image_bytes

    @staticmethod
    async def find_image(message: discord.Message) -> Tuple[Optional[str], Optional[BinaryIO]]:
        filename = None
        image_bytes = None
        for attachment in message.attachments:
            if attachment.height and attachment.width:
                try:
                    image_bytes_cache = io.BytesIO()
                    await attachment.save(image_bytes_cache)
                except (discord.HTTPException, discord.NotFound):
                    pass
                else:
                    filename = attachment.filename
                    image_bytes = image_bytes_cache
                    image_bytes.seek(0)
                    break
        return filename, image_bytes


@somsiad.bot.command(aliases=['usmaż', 'głębokosmaż', 'usmaz', 'glebokosmaz'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def deepfry(ctx, doneness: int = 2):
    """Deep-fries an image.
    Deep-fries the attached image, or, if there is none, the last image attached in the channel.
    Doneness is an integer between 1 and 3 inclusive signifying the number of deep-frying passes.
    """
    filename = None
    input_image_bytes = None
    async for message in ctx.history(limit=15):
        filename, input_image_bytes = await DeepFrier.find_image(message)
        if input_image_bytes:
            break
    else:
        embed = discord.Embed(
            title=':warning: Nie znaleziono obrazka do usmażenia!',
            color=somsiad.color
        )
        return await ctx.send(ctx.author.mention, embed=embed)
    output_image_bytes = await somsiad.bot.loop.run_in_executor(None, DeepFrier.fry, input_image_bytes, doneness)

    return await ctx.send(
        f'{ctx.author.mention}', file=discord.File(output_image_bytes, filename=filename or 'deepfried.jpg')
    )
