import locale
import os
from typing import Any, Optional, Sequence


class Setting:
    __slots__ = ('name', 'description', 'unit', 'value_type', 'default_value', 'optional', 'value')

    def __init__(
        self,
        name: str,
        *,
        description: str,
        unit: Optional[Sequence[str]] = None,
        value_type: Optional[type] = None,
        default_value: Any = None,
        optional: Optional[bool] = None,
    ):
        self.name = name
        self.description = description
        self.unit = unit
        self.value_type = value_type or (type(default_value) if default_value is not None else str)
        self.default_value = default_value
        self.optional = optional or default_value is not None

    def __repr__(self) -> str:
        return (
            'Setting('
            f'name={self.name}, description={self.description}, unit={self.unit},'
            f'value_type={self.value_type}, default_value={self.default_value}'
            ')'
        )

    def __str__(self) -> str:
        return f'{self.description}: {self.human_value()}'

    def human_value(self) -> str:
        if self.value is None:
            return 'brak'
        elif self.unit is not None:
            return f'{self.value} {self.unit}'
        else:
            return str(self.value)

    def set_value_with_env(self):
        try:
            value_obtained = os.environ[self.name.upper()]
        except KeyError:
            if self.optional:
                value_obtained = self.default_value
            else:
                raise Exception(
                    f'mandatory setting {self.name.upper()} could not be loaded from os.environ nor from .env'
                )
        self.value = self._convert_value_to_type(value_obtained)

    def _convert_value_to_type(self, value: Any) -> Any:
        if value is None:
            return None
        if self.value_type == int:
            try:
                return locale.atoi(value)
            except ValueError:
                return int(value)
        if self.value_type == float:
            try:
                return locale.atof(value)
            except ValueError:
                return float(value)
        return self.value_type(value)


class Configuration:
    __slots__ = ('settings',)

    def __init__(self, settings: Sequence[Setting]):
        for setting in settings:
            setting.set_value_with_env()
        self.settings = {setting.name: setting for setting in settings}

    def __getitem__(self, key: str) -> Any:
        try:
            return self.settings[key].value
        except KeyError:
            try:
                return os.environ[key.upper()]
            except KeyError:
                raise KeyError(f'{key.upper()} is neither recognized nor set as an environment variable')

    def get(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError:
            return None


SETTINGS = (
    Setting('discord_token', description='Token bota'),
    Setting('command_prefix', description='Domyślny prefiks komend', default_value='!'),
    Setting(
        'command_cooldown_per_user_in_seconds',
        description='Cooldown wywołania komendy przez użytkownika',
        unit='s',
        default_value=1.0,
    ),
    Setting('database_url', description='URL Postgresa'),
    Setting('clickhouse_address', description='Adres ClickHouse'),
    Setting('clickhouse_user', description='Nazwa użytkownika ClickHouse'),
    Setting('clickhouse_password', description='Hasło użytkownika ClickHouse'),
    Setting('sentry_dsn', description='DSN Sentry', optional=True),
    Setting('google_key', description='Klucz API Google'),
    Setting('google_custom_search_engine_id', description='Identyfikator CSE Google'),
    Setting('wolfram_alpha_app_id', description='Identyfikator aplikacji Wolfram Alpha'),
    Setting('goodreads_key', description='Klucz API Goodreads'),
    Setting('tmdb_key', description='Klucz API TMDb'),
    Setting('last_fm_key', description='Klucz API Last.fm'),
    Setting(
        'yandex_translate_key',
        description='Klucz API Yandex Translate',
    ),
    Setting(
        'disco_max_file_size_in_mib', description='Maksymalny rozmiar pliku utworu disco', unit='MiB', default_value=16
    ),
)

configuration = Configuration(SETTINGS)
