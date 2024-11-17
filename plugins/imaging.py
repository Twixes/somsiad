# Copyright 2019-2020 Slavfox & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from asyncio import sleep
import asyncio
from collections import defaultdict
import io
import time
from sentry_sdk import capture_exception

from sqlalchemy import func, desc, literal
from sqlalchemy.dialects.postgresql import BIT

from somsiad import SomsiadMixin
from typing import BinaryIO, DefaultDict, Dict, Optional, Tuple, TypedDict
import aiopytesseract
from aiopytesseract.exceptions import TesseractError
import discord
import imagehash
import PIL.Image
import PIL.ImageEnhance
import psycopg2.errors
from discord.ext import commands
import data
from core import cooldown, is_user_opted_out_of_data_processing
from utilities import md_link, utc_to_naive_local, word_number_form


class Similarity(TypedDict, total=False):
    visual: float
    textual: float


class Perceptualization(TypedDict):
    text: Optional[str]
    visual_hash: str


class Image9000(data.Base, data.MemberRelated, data.ChannelRelated):
    HASH_SIZE = 10

    attachment_id = data.Column(data.BigInteger, primary_key=True)
    message_id = data.Column(data.BigInteger, nullable=False)
    hash = data.Column(data.String(25), nullable=False)
    text = data.Column(data.UnicodeText(), nullable=True)
    sent_at = data.Column(data.DateTime, nullable=False)

    async def get_presentation(self, bot: commands.Bot) -> str:
        parts = [self.sent_at.strftime("%-d %B %Y o %-H:%M")]
        discord_channel = self.discord_channel(bot)
        parts.append("na usuniętym kanale" if discord_channel is None else f"na #{discord_channel}")
        discord_user = self.discord_user(bot)
        if discord_user is None:
            try:
                discord_user = await bot.fetch_user(self.user_id)
            except discord.NotFound:
                pass
        parts.append(f'przez {"przez usuniętego użytkownika" if discord_user is None else discord_user.display_name}')
        return " ".join(parts)


class Imaging(commands.Cog, SomsiadMixin):
    ExtractedImage = Tuple[Optional[discord.Attachment], Optional[BinaryIO]]

    IMAGE9000_HASH_BIT_COUNT = 80
    IMAGE9000_VISUAL_SIMILARITY_TRESHOLD = 0.8
    IMAGE9000_TEXTUAL_SIMILARITY_MIN_CHARS = 5

    IMAGE9000_ACCEPTABLE_PERCEPTUAL_DISTANCE = int(
        IMAGE9000_HASH_BIT_COUNT * (1 - IMAGE9000_VISUAL_SIMILARITY_TRESHOLD)
    )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:
            with data.session(commit=True) as session:
                if is_user_opted_out_of_data_processing(session, message.author.id):
                    return  # User opted out of data processing
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
                                perceptualization = await self._perceptualize(image_bytes)
                            except:
                                capture_exception()
                                continue
                            images9000.append(
                                Image9000(
                                    attachment_id=attachment.id,
                                    message_id=message.id,
                                    user_id=message.author.id,
                                    channel_id=message.channel.id,
                                    server_id=message.guild.id,
                                    hash=perceptualization["visual_hash"],
                                    text=perceptualization["text"],
                                    sent_at=utc_to_naive_local(message.created_at),
                                )
                            )
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
            image = PIL.Image.open(image_bytes).convert("RGB")
            aspect_ratio = image.width / image.height
            if image.width > MAX_SIZE and image.width > image.height:
                image = image.resize((MAX_SIZE, int(MAX_SIZE / aspect_ratio)))
            elif image.height > MAX_SIZE:
                image = image.resize((int(MAX_SIZE * aspect_ratio), MAX_SIZE))
            image = PIL.ImageEnhance.Color(image).enhance(1.25)
            image = PIL.ImageEnhance.Contrast(image).enhance(2)
            image = PIL.ImageEnhance.Sharpness(image).enhance(2)
            image_bytes = io.BytesIO()
            image.save(image_bytes, "JPEG", quality=1)
            image_bytes.seek(0)
        return image_bytes

    async def _perceptualize(self, image_bytes: BinaryIO) -> Perceptualization:
        try:
            image_text = await aiopytesseract.image_to_string(
                image_bytes.read(),
                lang="eng+pol",
                psm=11,
                timeout=5,
            )
            image_text = image_text.strip()
        except TesseractError:
            capture_exception()
            image_text = None
        image = PIL.Image.open(image_bytes)
        image_hash = imagehash.phash(image, Image9000.HASH_SIZE)
        return {"text": image_text, "visual_hash": str(image_hash)}

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
        self,
        channel: commands.Context,
        *,
        sent_by: Optional[discord.Member] = None,
        message_id: Optional[int] = None,
        limit: int = 15,
    ) -> ExtractedImage:
        attachment, input_image_bytes = None, None
        if message_id is not None:
            reference_message = await channel.fetch_message(message_id)
            attachment, input_image_bytes = await self.extract_image(reference_message)
        else:
            async for message in channel.history(limit=limit):
                if sent_by is not None and message.author != sent_by:
                    continue
                attachment, input_image_bytes = await self.extract_image(message)
                if input_image_bytes is not None:
                    break
        return attachment, input_image_bytes

    @cooldown()
    @commands.command(aliases=["obróć", "obroc", "niewytrzymie"])
    @commands.guild_only()
    async def rotate(self, ctx, sent_by: Optional[discord.Member] = None, times_or_degrees: int = 1):
        """Rotates an image."""
        attachment, input_image_bytes = await self.find_image(ctx.channel, sent_by=sent_by)
        times = times_or_degrees // 90 if times_or_degrees % 90 == 0 else times_or_degrees
        if input_image_bytes:
            try:
                output_image_bytes = await self.bot.loop.run_in_executor(None, self._rotate, input_image_bytes, times)
            except PIL.Image.UnidentifiedImageError:
                await self.bot.send(ctx, embed=self.bot.generate_embed("⚠️", "Nie znaleziono obrazka do obrócenia"))
            else:
                await self.bot.send(
                    ctx, file=discord.File(output_image_bytes, filename=attachment.filename or "rotated.jpeg")
                )
        else:
            await self.bot.send(ctx, embed=self.bot.generate_embed("⚠️", "Nie znaleziono obrazka do obrócenia"))

    @cooldown()
    @commands.command(aliases=["usmaż", "głębokosmaż", "usmaz", "glebokosmaz"])
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
                await self.bot.send(ctx, embed=self.bot.generate_embed("⚠️", "Nie znaleziono obrazka do usmażenia"))
            else:
                await self.bot.send(
                    ctx, file=discord.File(output_image_bytes, filename=attachment.filename or "deepfried.jpeg")
                )
        else:
            await self.bot.send(ctx, embed=self.bot.generate_embed("⚠️", "Nie znaleziono obrazka do usmażenia"))

    @cooldown()
    @commands.command(aliases=["r9k", "było", "bylo", "byo"])
    @commands.guild_only()
    async def robot9000(self, ctx: commands.Context, *, text_query: Optional[str] = None):
        """Finds previous occurences of the image being sent."""
        async with ctx.typing():
            if text_query:
                search_results: Dict[Image9000, float] = {}
                with data.session() as session:
                    for image9000, textual_similarity in sorted(
                        session.query(Image9000)
                        .add_column(func.word_similarity(text_query, Image9000.text).label("textual_similarity"))
                        .filter(Image9000.server_id == ctx.guild.id, Image9000.text.op("%>")(text_query))
                        .limit(20),
                        key=lambda x: x[1],
                        reverse=True,
                    ):
                        search_results[image9000] = textual_similarity
                if search_results:
                    embed = self.bot.generate_embed(
                        "🤖",
                        f'Znaleziono {word_number_form(len(search_results), "obrazek pasujący", "obrazki pasujące", "obrazków pasujących")} do zapytania "{text_query}"',
                    )
                    field_parts = await asyncio.gather(
                        *(
                            self._image_to_embed_field(image9000, {"textual": textual_similarity})
                            for image9000, textual_similarity in search_results.items()
                        ),
                    )
                    for name, value in field_parts:
                        if len(embed) + len(name) + len(value) > 6000:
                            break
                        embed.add_field(name=name, value=value, inline=False)
                else:
                    embed = self.bot.generate_embed(
                        "🤖",
                        f'Nie znalazłem żadnego obrazka pasującego do zapytania "{text_query}"',
                    )
                return await self.bot.send(ctx, embed=embed)
            attachment, _ = await self.find_image(
                ctx.channel,
                message_id=ctx.message.reference.message_id
                if ctx.message is not None and ctx.message.reference is not None
                else None,
            )
            if attachment is not None:
                with data.session() as session:
                    similar: DefaultDict[Image9000, Similarity] = defaultdict(Similarity)
                    base_image9000: Optional[Image9000] = session.query(Image9000).get(attachment.id)
                    if base_image9000 is None:
                        embed = self.bot.generate_embed("⚠️", "Obrazek do wyszukania nie został jeszcze zindeksowany")
                        for wait_seconds in [0.5, 1, 2, 4, 8]:  # Exponential backoff
                            await sleep(wait_seconds)
                            base_image9000 = session.query(Image9000).get(attachment.id)
                            if base_image9000 is not None:
                                break
                    if base_image9000 is not None:
                        init_time = time.time()
                        server_images = session.query(Image9000).filter(
                            Image9000.server_id == ctx.guild.id, Image9000.attachment_id != attachment.id
                        )
                        sent_by = ctx.guild.get_member(base_image9000.user_id)

                        perceptual_distance_column = (
                            literal("x")
                            .op("||")(Image9000.hash)
                            .cast(BIT(self.IMAGE9000_HASH_BIT_COUNT))
                            .op("<~>")(
                                literal("x").op("||")(base_image9000.hash).cast(BIT(self.IMAGE9000_HASH_BIT_COUNT))
                            )
                            .label("perceptual_distance")
                        )

                        if (
                            base_image9000.text
                            and len(base_image9000.text) >= self.IMAGE9000_TEXTUAL_SIMILARITY_MIN_CHARS
                        ):
                            textual_similarity_column = func.word_similarity(base_image9000.text, Image9000.text).label(
                                "textual_similarity"
                            )
                            perceptual_matches = (
                                server_images.add_column(perceptual_distance_column)
                                .add_column(textual_similarity_column)
                                .filter(perceptual_distance_column <= self.IMAGE9000_ACCEPTABLE_PERCEPTUAL_DISTANCE)
                                .order_by("perceptual_distance")
                                .limit(20)
                            )
                            textual_matches = (
                                server_images.add_column(perceptual_distance_column)
                                .add_column(textual_similarity_column)
                                .filter(Image9000.text.op("%>")(base_image9000.text))
                            )
                            for other_image9000, perceptual_distance, textual_similarity in (
                                perceptual_matches.union(textual_matches)
                                .order_by("perceptual_distance", desc("textual_similarity"))
                                .limit(20)
                            ):
                                similar[other_image9000]["visual"] = (
                                    1 - perceptual_distance / self.IMAGE9000_HASH_BIT_COUNT
                                )
                                similar[other_image9000]["textual"] = textual_similarity
                        else:
                            for other_image9000, perceptual_distance in (
                                server_images.add_column(perceptual_distance_column)
                                .filter(perceptual_distance_column <= self.IMAGE9000_ACCEPTABLE_PERCEPTUAL_DISTANCE)
                                .order_by("perceptual_distance")
                                .limit(20)
                            ):
                                similar[other_image9000]["visual"] = (
                                    1 - perceptual_distance / self.IMAGE9000_HASH_BIT_COUNT
                                )

                        if similar:
                            embed = self.bot.generate_embed()
                            field_parts = await asyncio.gather(
                                *(
                                    self._image_to_embed_field(image9000, similarity)
                                    for image9000, similarity in similar.items()
                                ),
                            )
                            for name, value in field_parts:
                                # Respect the embed size limit of 6000 characters, setting aside 200 for the title
                                if len(embed) + len(name) + len(value) >= 5800:
                                    break
                                embed.add_field(name=name, value=value, inline=False)
                            occurences_form = word_number_form(
                                len(embed.fields),
                                "wcześniejsze wystąpienie",
                                "wcześniejsze wystąpienia",
                                "wcześniejszych wystąpień",
                            )
                            embed.title = (
                                f"🤖 Wykryłem {occurences_form} na serwerze obrazka wysłanego "
                                + (f"przez {sent_by.display_name} " if sent_by is not None else "")
                                + f'o {base_image9000.sent_at.strftime("%-H:%M")}'
                            )
                        else:
                            embed = self.bot.generate_embed(
                                "🤖",
                                f'Nie wykryłem, aby obrazek wysłany przez {sent_by.display_name} '
                                f'o {base_image9000.sent_at.strftime("%-H:%M")} wystąpił wcześniej na serwerze',
                            )
                        comparison_time = time.time() - init_time
                        seen_image_form = word_number_form(
                            server_images.count(), "obrazek zobaczony", "obrazki zobaczone", "obrazków zobaczonych"
                        )
                        embed.set_footer(
                            text=f"Przejrzano {seen_image_form} do tej pory na serwerze w {round(comparison_time, 2):n} s."
                        )
            else:
                embed = self.bot.generate_embed("⚠️", "Nie znaleziono obrazka do sprawdzenia")
            await self.bot.send(ctx, embed=embed)

    async def _image_to_embed_field(self, image9000: Image9000, similarity: Similarity) -> Tuple[str, str]:
        channel = image9000.discord_channel(self.bot)
        message = None
        info = ""
        if channel is not None:
            try:
                message = await channel.fetch_message(image9000.message_id)
            except discord.NotFound:
                info = " (wiadomość usunięta)"
        else:
            info = " (kanał usunięty)"
        similarity_presentantion_parts = []
        if "visual" in similarity:
            similarity_presentantion_parts.append(f'{similarity["visual"]:.0%} podobieństwa wizualnego')
        if "textual" in similarity:
            similarity_presentantion_parts.append(f'{similarity["textual"]:.0%} podobieństwa tekstu')
        return (
            await image9000.get_presentation(self.bot),
            md_link(
                ", ".join(similarity_presentantion_parts),
                message.jump_url if message is not None else None,
            )
            + info,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Imaging(bot))
