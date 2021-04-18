# Copyright 2019-2020 Slavfox & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import io
import time
from typing import BinaryIO, Optional, Tuple

import discord
import imagehash
import PIL.Image
import PIL.ImageEnhance
import psycopg2.errors
from discord.ext import commands

import data
from core import cooldown
from utilities import md_link, utc_to_naive_local, word_number_form


class Image9000(data.Base, data.MemberRelated, data.ChannelRelated):
    HASH_SIZE = 10

    attachment_id = data.Column(data.BigInteger, primary_key=True)
    message_id = data.Column(data.BigInteger, nullable=False)
    hash = data.Column(data.String(25), nullable=False)
    sent_at = data.Column(data.DateTime, nullable=False)

    def calculate_similarity_to(self, other) -> float:
        return (self.HASH_SIZE ** 2 - bin(int(self.hash, 16) ^ int(other.hash, 16)).count('1')) / self.HASH_SIZE ** 2

    async def get_presentation(self, bot: commands.Bot) -> str:
        parts = [self.sent_at.strftime('%-d %B %Y o %-H:%M')]
        discord_channel = self.discord_channel(bot)
        parts.append('na usuniętym kanale' if discord_channel is None else f'na #{discord_channel}')
        discord_user = self.discord_user(bot)
        if discord_user is None:
            discord_user = await bot.fetch_user(self.user_id)
        parts.append(f'przez {"przez usuniętego użytkownika" if discord_user is None else discord_user}')
        return ' '.join(parts)


class Imaging(commands.Cog):
    ExtractedImage = Tuple[Optional[discord.Attachment], Optional[BinaryIO]]

    IMAGE9000_SIMILARITY_TRESHOLD = 0.75

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.attachments or message.guild is None:
            return
        images9000 = []
        for attachment in message.attachments:
            if attachment.height and attachment.width:
                image_bytes = io.BytesIO()
                try:
                    await attachment.save(image_bytes)
                except (discord.HTTPException, discord.NotFound):
                    continue
                else:
                    try:
                        hash_string = self._hash(image_bytes)
                    except:
                        continue
                    images9000.append(
                        Image9000(
                            attachment_id=attachment.id,
                            message_id=message.id,
                            user_id=message.author.id,
                            channel_id=message.channel.id,
                            server_id=message.guild.id,
                            hash=hash_string,
                            sent_at=utc_to_naive_local(message.created_at),
                        )
                    )
        try:
            with data.session(commit=True) as session:
                session.bulk_save_objects(images9000)
        except (psycopg2.errors.ForeignKeyViolation, psycopg2.errors.UniqueViolation):
            pass

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
    def _hash(image_bytes: BinaryIO) -> str:
        image = PIL.Image.open(image_bytes)
        image_hash = imagehash.phash(image, Image9000.HASH_SIZE)
        return str(image_hash)

    @staticmethod
    async def extract_image(message: discord.Message) -> ExtractedImage:
        attachment, image_bytes = None, None
        for i_attachment in message.attachments:
            if i_attachment.height and i_attachment.width:
                image_bytes_cache = io.BytesIO()
                try:
                    await i_attachment.save(image_bytes_cache)
                except (discord.HTTPException, discord.NotFound):
                    continue
                else:
                    attachment = i_attachment
                    image_bytes = image_bytes_cache
                    image_bytes.seek(0)
                    break
        return attachment, image_bytes

    async def find_image(
        self, channel: commands.Context, *, sent_by: Optional[discord.Member] = None, limit: int = 15
    ) -> ExtractedImage:
        attachment, input_image_bytes = None, None
        async with channel.typing():
            async for message in channel.history(limit=limit):
                if sent_by is not None and message.author != sent_by:
                    continue
                attachment, input_image_bytes = await self.extract_image(message)
                if input_image_bytes is not None:
                    break
        return attachment, input_image_bytes

    @commands.command(aliases=['obróć', 'obroc', 'niewytrzymie'])
    @cooldown()
    @commands.guild_only()
    async def rotate(self, ctx, sent_by: Optional[discord.Member] = None, times_or_degrees: int = 1):
        """Rotates an image."""
        attachment, input_image_bytes = await self.find_image(ctx.channel, sent_by=sent_by)
        times = times_or_degrees // 90 if times_or_degrees % 90 == 0 else times_or_degrees
        if input_image_bytes:
            try:
                output_image_bytes = await self.bot.loop.run_in_executor(None, self._rotate, input_image_bytes, times)
            except PIL.Image.UnidentifiedImageError:
                await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', 'Nie znaleziono obrazka do obrócenia'))
            else:
                await self.bot.send(
                    ctx, file=discord.File(output_image_bytes, filename=attachment.filename or 'rotated.jpeg')
                )
        else:
            await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', 'Nie znaleziono obrazka do obrócenia'))

    @commands.command(aliases=['usmaż', 'głębokosmaż', 'usmaz', 'glebokosmaz'])
    @cooldown()
    @commands.guild_only()
    async def deepfry(self, ctx, sent_by: Optional[discord.Member] = None, doneness: int = 2):
        """Deep-fries an image.
        Deep-fries the attached image, or, if there is none, the last image attached in the channel.
        Doneness is an integer between 1 and 3 inclusive signifying the number of deep-frying passes.
        """
        attachment, input_image_bytes = await self.find_image(ctx.channel, sent_by=sent_by)
        if input_image_bytes:
            try:
                output_image_bytes = await self.bot.loop.run_in_executor(
                    None, self._deepfry, input_image_bytes, doneness
                )
            except PIL.Image.UnidentifiedImageError:
                await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', 'Nie znaleziono obrazka do usmażenia'))
            else:
                await self.bot.send(
                    ctx, file=discord.File(output_image_bytes, filename=attachment.filename or 'deepfried.jpeg')
                )
        else:
            await self.bot.send(ctx, embed=self.bot.generate_embed('⚠️', 'Nie znaleziono obrazka do usmażenia'))

    @commands.command(aliases=['r9k', 'było', 'bylo', 'byo'])
    @cooldown()
    @commands.guild_only()
    async def robot9000(self, ctx, sent_by: discord.Member = None):
        """Finds previous occurences of the image being sent."""
        attachment, _ = await self.find_image(ctx.channel, sent_by=sent_by)
        if attachment is not None:
            with data.session() as session:
                similar = []
                base_image9000 = session.query(Image9000).get(attachment.id)
                if base_image9000 is None:
                    embed = self.bot.generate_embed('⚠️', 'Nie znaleziono obrazka do sprawdzenia')
                else:
                    init_time = time.time()
                    comparison_count = 0
                    sent_by = ctx.guild.get_member(base_image9000.user_id)
                    for other_image9000 in session.query(Image9000).filter(
                        Image9000.server_id == ctx.guild.id, Image9000.attachment_id != attachment.id
                    ):
                        comparison_count += 1
                        similarity = base_image9000.calculate_similarity_to(other_image9000)
                        if similarity >= self.IMAGE9000_SIMILARITY_TRESHOLD:
                            similar.append((other_image9000, similarity))
                    if similar:
                        embed = self.bot.generate_embed()
                        for image9000, similarity in similar:
                            channel = image9000.discord_channel(self.bot)
                            message = None
                            info = ''
                            if channel is not None:
                                try:
                                    message = await channel.fetch_message(image9000.message_id)
                                except discord.NotFound:
                                    info = ' (wiadomość usunięta)'
                            else:
                                info = ' (kanał usunięty)'
                            similarity_presentantion = f'{int(round(similarity*100))}% podobieństwa'
                            embed.add_field(
                                name=await image9000.get_presentation(self.bot),
                                value=md_link(
                                    similarity_presentantion, message.jump_url if message is not None else None
                                )
                                + info,
                                inline=False,
                            )
                        occurences_form = word_number_form(
                            len(embed.fields),
                            'wcześniejsze wystąpienie',
                            'wcześniejsze wystąpienia',
                            'wcześniejszych wystąpień',
                        )
                        embed.title = (
                            f'🤖 Wykryłem {occurences_form} na serwerze obrazka wysłanego przez {sent_by} o '
                            f'{base_image9000.sent_at.strftime("%-H:%M")}'
                        )
                    else:
                        embed = self.bot.generate_embed(
                            '🤖',
                            f'Nie wykryłem, aby obrazek wysłany przez {sent_by} '
                            f'o {base_image9000.sent_at.strftime("%-H:%M")} wystąpił wcześniej na serwerze',
                        )
                    comparison_time = time.time() - init_time
                    seen_image_form = word_number_form(
                        comparison_count, 'obrazek zobaczony', 'obrazki zobaczone', 'obrazków zobaczonych'
                    )
                    embed.set_footer(
                        text=f'Przejrzano {seen_image_form} do tej pory na serwerze w {round(comparison_time, 2):n} s.'
                    )
        else:
            embed = self.bot.generate_embed('⚠️', 'Nie znaleziono obrazka do sprawdzenia')
        await self.bot.send(ctx, embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Imaging(bot))
