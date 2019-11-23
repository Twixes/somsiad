from typing import Any, Sequence
import locale
import os
from dotenv import load_dotenv

class Setting:
    __slots__ = ('name', 'description', 'unit', 'value_type', 'default_value', 'value')

    def __init__(
            self, name: str, *, description: str, unit: Sequence[str] = None, value_type = str,
            default_value: Any = None
    ):
        self.name = name
        self.description = description
        self.unit = unit
        self.value_type = value_type
        self.default_value = default_value

    def __repr__(self) -> str:
        return (
            'Setting('
            f'name=\'{self.name}\', description=\'{self.description}\', unit=\'{self.unit}\','
            f'value_type=\'{self.value_type}\', default_value=\'{self.default_value}\''
            ')'
        )

    def __str__(self) -> str:
        return f'{self.description}: {self.human_value()}'

    def human_value(self) -> str:
        if self.value is None:
            return 'brak!' if self.default_value is None else 'brak'
        if self.unit is not None:
            return f'{self.value} {self.unit}'
        return str(self.value)

    def set_value_with_env(self):
        value_obtained = os.getenv(self.name.upper(), self.default_value)
        self.value = self._convert_value_to_type(value_obtained)

    def _convert_value_to_type(self, value: Any) -> Any:
        if value is None:
            return None
        if self.value_type == int:
            try:
                return int(value)
            except ValueError:
                return locale.atoi(value)
        if self.value_type == float:
            try:
                return float(value)
            except ValueError:
                return locale.atof(value)
        return self.value_type(value)


class Configuration:
    __slots__ = ('settings',)

    def __init__(self, settings: Sequence[Setting]):
        load_dotenv()
        for setting in settings:
            setting.set_value_with_env()
        self.settings = {setting.name: setting for setting in settings}

    def __getitem__(self, key: str):
        return self.settings[key].value


SETTINGS = (
    Setting('discord_token', description='Token bota'),
    Setting('command_prefix', description='Domyślny prefiks komend', default_value='!'),
    Setting(
        'command_cooldown_per_user_in_seconds', description='Cooldown wywołania komendy przez użytkownika',
        unit='s', value_type=float, default_value=1.0
    ),
    Setting('database_url', description='URL bazy danych'),
    Setting('google_key', description='Klucz API Google'),
    Setting('google_custom_search_engine_id', description='Identyfikator CSE Google'),
    Setting('goodreads_key', description='Klucz API Goodreads'),
    Setting('omdb_key', description='Klucz API OMDb'),
    Setting('last_fm_key', description='Klucz API Last.fm'),
    Setting('yandex_translate_key', description='Klucz API Yandex Translate',),
    Setting('reddit_id', description='ID aplikacji redditowej'),
    Setting('reddit_secret', description='Szyfr aplikacji redditowej'),
    Setting('reddit_username', description='Redditowa nazwa użytkownika'),
    Setting('reddit_password', description='Hasło do konta na Reddicie'),
    Setting(
        'disco_max_file_size_in_mib', description='Maksymalny rozmiar pliku utworu disco', unit='MiB', value_type=int,
        default_value=16
    )
)

configuration = Configuration(SETTINGS)
