# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from discord.ext import commands
from core import cooldown


class BotOwnerTools(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def v2_embed(self) -> discord.Embed:
        embed = self.bot.generate_embed(
            '📢', 'Somsiad 2.0.0', 'Nowa wersja już tu jest, a w niej wiele nowych funkcji i usprawnień. Poniżej najważniejsze z nich.'
        )
        embed.add_field(
            name='🔧',
            value='Administratorzy serwera mogą teraz ustawić na nim własny prefiks komend Somsiada z użyciem komendy `prefiks`.\nWięcej informacji pod `prefiks` bez podkomendy.',
            inline=False
        )
        embed.add_field(
            name='🍅',
            value='Z nową komendą `przypomnij` bot przypomni o każdej ważnej sprawie.',
            inline=False
        )
        embed.add_field(
            name='🎥',
            value='Zamiast [OMDb](https://www.omdbapi.com/) poprzez komendę `omdb` lepsze informacje o filmach i serialach można teraz uzyskać z [TMDb](https://www.themoviedb.org/) poprzez komendę `tmdb`. Dodatkowo dostępne są też informacje o osobach z przemysłu, np. aktorkach bądź reżyserach. W ramach tej funkcji działają również odrębne komendy `film` i `serial`.\nWięcej informacji pod `tmdb` bez podkomendy.',
            inline=False
        )
        embed.add_field(
            name='🧠',
            value='Nowa komenda `wolframalpha` pozwala na dostęp do całych zasobów wiedzy i mocy obliczeniowej [Wolfram Alpha](https://www.wolframalpha.com/). Zastępuje komendy `oblicz` i `waluta`.',
            inline=False
        )
        embed.add_field(
            name='🎂',
            value='Ulepszona komenda `urodziny` zapamiętuje teraz datę urodzin globalnie z upublicznianiem jej osobno na każdym serwerze. Dodatkowo administratorzy serwera mogą z użyciem `urodziny powiadomienia` włączyć na wybranym kanale automatyczne powiadomienia o urodzinach użytkowników serwera, wraz z życzeniami. Z powodu tak dużych zmian w działaniu funkcji daty urodzin zostały w aktualizacji zresetowane.\nWięcej informacji pod `urodziny` bez podkomendy.',
            inline=False
        )
        embed.add_field(
            name='👽',
            value='Całkowicie przepisane komendy `r` i `u` oprócz linku dostarczają teraz też informacje o znalezionym, odpowiednio, subreddicie lub użytkowniku Reddita.',
            inline=False
        )
        embed.add_field(
            name='🎓',
            value='Do `ilejeszcze` dodano podkomendę `matura` odliczającą do pierwszego dnia matur.',
            inline=False
        )
        embed.add_field(
            name='🎨',
            value='Z nową komendą `kolory` użytkownicy mogą sami wybierać sobie kolor nicku spośród utworzonych przez administrację serwera specjalnych ról.\nWięcej informacji pod `kolory` bez podkomendy.',
            inline=False
        )
        embed.add_field(
            name='✍️',
            value='Nowa komenda moderacyjna `przebacz` pozwala administratorom serwera usunąć ostrzeżenia z kartoteki użytkownika.',
            inline=False
        )
        embed.add_field(
            name='🇫',
            value='Do komendy własnych reakcji `reaguj` dodano obsługę spacji (w ich miejsca wstawiane są losowe emoji) oraz serwerowych emoji.',
            inline=False
        )
        embed.add_field(
            name='📈',
            value='Do raportów aktywności komendy `stat` dodano nowe informacje i wykresy, a także znacznie usprawniono ich generowanie.',
            inline=False
        )
        embed.add_field(
            name='🖼',
            value='Dodano komendę obracania obrazków `obróć` i ulepszono `deepfry`.',
            inline=False
        )
        embed.add_field(
            name='🔄',
            value='Przepisano komendy `głosowanie` i `spal` tak, by wykonywały się również po restarcie bota.',
            inline=False
        )
        embed.add_field(
            name='⚠️',
            value='Dodano rejestrowanie błędów i okoliczności ich zajścia, co będzie ułatwiać ich naprawę. Błędy można do tego zgłaszać na [serwerze Somsiad Labs](http://discord.gg/xRCpDs7). Mile widziane również sugestie nowych funkcji i innych usprawnień.',
            inline=False
        )
        return embed

    @commands.command(aliases=['wejdź'])
    @cooldown()
    @commands.is_owner()
    async def enter(self, ctx, *, server_name_or_id):
        """Generates an invite to the provided server."""
        invite = None
        for server in ctx.bot.guilds:
            if server_name_or_id in (server.name, str(server.id)):
                for channel in server.channels:
                    if (
                            not isinstance(channel, discord.CategoryChannel)
                            and server.me.permissions_in(channel).create_instant_invite
                    ):
                        invite = await channel.create_invite(max_uses=1)
                        break
                break

        if invite is not None:
            await self.bot.send(ctx, invite.url)

    @commands.group(aliases=['ogłoś', 'oglos'], case_insensitive=True)
    @cooldown()
    @commands.is_owner()
    async def announce(self, _):
        pass

    @announce.command(aliases=['globalnie'])
    @cooldown()
    @commands.is_owner()
    async def announce_globally(self, ctx, *, raw_announcement):
        """Makes an announcement on all servers smaller than 10000 members not containing "bot" in their name."""
        if raw_announcement == 'v2':
            embed = self.v2_embed()
        else:
            announcement = raw_announcement.replace('\\n','\n').strip(';').split(';')
            if announcement[0].startswith('!'):
                description = announcement[0].lstrip('!').strip()
                announcement = announcement[1:]
            else:
                description = None

            embed = self.bot.generate_embed('📢', 'Ogłoszenie somsiedzkie', description)

            for n in range(0, len(announcement) - 1, 2):
                embed.add_field(name=announcement[n].strip(), value=announcement[n+1].strip(), inline=False)

        for server in ctx.bot.guilds:
            if 'bot' not in server.name.lower():
                for channel in server.text_channels:
                    if not channel.is_news():
                        try:
                            await channel.send(embed=embed)
                        except:
                            continue
                        else:
                            break

    @announce.command(aliases=['lokalnie'])
    @cooldown()
    @commands.is_owner()
    @commands.guild_only()
    async def announce_locally(self, ctx, *, raw_announcement):
        """Makes an announcement only on the server where the command was invoked."""
        if raw_announcement == 'v2':
            embed = self.v2_embed()
        else:
            announcement = raw_announcement.replace('\\n','\n').strip(';').split(';')
            if announcement[0].startswith('!'):
                description = announcement[0].lstrip('!').strip()
                announcement = announcement[1:]
            else:
                description = None

            embed = self.bot.generate_embed('📢', 'Ogłoszenie somsiedzkie', description)

            for n in range(0, len(announcement) - 1, 2):
                embed.add_field(name=announcement[n].strip(), value=announcement[n+1].strip(), inline=False)

        for channel in ctx.guild.text_channels:
            if channel.permissions_for(ctx.me).send_messages:
                await channel.send(embed=embed)
                break

    @commands.command(aliases=['wyłącz', 'wylacz', 'stop'])
    @cooldown()
    @commands.is_owner()
    async def shutdown(self, ctx):
        """Shuts down the bot."""
        embed = self.bot.generate_embed('🛑', 'Wyłączanie bota…')
        await self.bot.send(ctx, embed=embed)
        await ctx.bot.close()

    @commands.command(aliases=['błąd', 'blad', 'błont', 'blont'])
    @cooldown()
    @commands.is_owner()
    async def error(self, ctx):
        """Causes an error."""
        await self.bot.send(ctx, 1 / 0)


def setup(bot: commands.Bot):
    bot.add_cog(BotOwnerTools(bot))
