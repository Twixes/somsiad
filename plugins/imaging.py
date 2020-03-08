# Copyright 2019-2020 Slavfox & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import BinaryIO, Optional, Tuple
import io
import PIL.Image
import PIL.ImageEnhance
import discord
from discord.ext import commands
from core import cooldown


class Imaging(commands.Cog):
    ExtractedImage = Tuple[Optional[str], Optional[BinaryIO]]

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _rotate(image_bytes: BinaryIO, times: int):
        image = PIL.Image.open(image_bytes)
        image_format = image.format
        image = image.rotate(-90 * times, expand=True)
        image_bytes = io.BytesIO()
        image.save(image_bytes, image_format)
        image_bytes.seek(0)
        return image_bytes

    @staticmethod
    def _deepfry(image_bytes: BinaryIO, number_of_passes: int) -> BinaryIO:
        MAX_SIZE = 1000
        if number_of_passes < 1:
            number_of_passes = 1
        elif number_of_passes > 3:
            number_of_passes = 3
        for _ in range(number_of_passes):
            image = PIL.Image.open(image_bytes).convert('RGB')
            aspect_ratio = image.width / image.height
            if image.width > MAX_SIZE and image.width > image.height:
                image = image.resize((MAX_SIZE, int(MAX_SIZE / aspect_ratio)))
            elif image.height > MAX_SIZE:
                image = image.resize((int(MAX_SIZE * aspect_ratio), MAX_SIZE))
            image = PIL.ImageEnhance.Color(image).enhance(1.25)
            image = PIL.ImageEnhance.Contrast(image).enhance(2)
            image = PIL.ImageEnhance.Sharpness(image).enhance(2)
            image_bytes = io.BytesIO()
            image.save(image_bytes, 'JPEG', quality=1)
            image_bytes.seek(0)
        return image_bytes

    @staticmethod
    async def extract_image(message: discord.Message) -> ExtractedImage:
        filename, image_bytes = None, None
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

    async def find_image(self, ctx: commands.Context, limit: int = 15) -> ExtractedImage:
        filename, input_image_bytes = None, None
        async with ctx.typing():
            async for message in ctx.history(limit=limit):
                filename, input_image_bytes = await self.extract_image(message)
                if input_image_bytes:
                    break
        return filename, input_image_bytes

    @commands.command(aliases=['obróć', 'obroc', 'niewytrzymie'])
    @cooldown()
    @commands.guild_only()
    async def rotate(self, ctx, times: int = 1):
        """Rotates an image."""
        filename, input_image_bytes = await self.find_image(ctx)
        if input_image_bytes:
            output_image_bytes = await self.bot.loop.run_in_executor(None, self._rotate, input_image_bytes, times)
            await self.bot.send(ctx, file=discord.File(output_image_bytes, filename=filename or 'rotated.jpeg'))
        else:
            await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', 'Nie znaleziono obrazka do obrócenia'))

    @commands.command(aliases=['usmaż', 'głębokosmaż', 'usmaz', 'glebokosmaz'])
    @cooldown()
    @commands.guild_only()
    async def deepfry(self, ctx, doneness: int = 2):
        """Deep-fries an image.
        Deep-fries the attached image, or, if there is none, the last image attached in the channel.
        Doneness is an integer between 1 and 3 inclusive signifying the number of deep-frying passes.
        """
        filename, input_image_bytes = await self.find_image(ctx)
        if input_image_bytes:
            output_image_bytes = await self.bot.loop.run_in_executor(None, self._deepfry, input_image_bytes, doneness)
            await self.bot.send(ctx, file=discord.File(output_image_bytes, filename=filename or 'deepfried.jpeg'))
        else:
            await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', 'Nie znaleziono obrazka do usmażenia'))


def setup(bot: commands.Bot):
    bot.add_cog(Imaging(bot))
