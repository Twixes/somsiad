# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import json
import os
import datetime as dt
from typing import Union, Dict


class TextFormatter:
    """Text formatting utilities."""
    @staticmethod
    def limit_text_length(text: str, limit: int) -> str:
        words = text.split()
        cut_text = ''
        for word in words:
            if len(cut_text) + len(word) <= limit:
                cut_text += word + ' '

        if cut_text[-2:] == '. ':
            cut_text = cut_text.rstrip()
        else:
            cut_text = cut_text.rstrip().rstrip(',') + '...'

        return cut_text

    @staticmethod
    def with_preposition_variant(number: int) -> str:
        """Returns the gramatically correct variant of the 'with' preposition in Polish."""
        return 'ze' if 100 <= number < 200 else 'z'

    @staticmethod
    def noun_variant(number: int, singular_form: str, plural_form: str, *, include_number: bool = True) -> str:
        """Returns the gramatically correct variant of the given noun in Polish."""
        proper_form = singular_form if number == 1 else plural_form

        if include_number:
            return f'{number} {proper_form}'
        else:
            return proper_form

    @staticmethod
    def adjective_variant(
            number: int, singular_form: str, plural_form_2_to_4: str, plural_form_5_to_1: str,
            *, include_number: bool = True
    ) -> str:
        """Returns the gramatically correct variant of the given adjective in Polish."""
        if number == 1:
            proper_form = singular_form
        elif (
                (str(number)[-1] == '2' or str(number)[-1] == '3' or str(number)[-1] == '4')
                and number not in (12, 13, 14)
        ):
            proper_form = plural_form_2_to_4
        else:
            proper_form = plural_form_5_to_1

        if include_number:
            return f'{number} {proper_form}'
        else:
            return proper_form

    @classmethod
    def human_readable_time_ago(cls, utc_datetime: dt.datetime, *, date=True, time=True, days=True) -> str:
        local_datetime = utc_datetime.replace(tzinfo=dt.timezone.utc).astimezone()
        delta = dt.datetime.now().astimezone() - local_datetime

        combined_information = []
        if date:
            date_string = local_datetime.strftime('%d.%m.%Y')
            combined_information.append(date_string)
        if time:
            time_string = local_datetime.strftime('%H:%M')
            if date:
                combined_information.append(f' o {time_string}')
            else:
                combined_information.append(time_string)
        if days:
            days_since = delta.days
            if days_since == 0:
                days_since_string = 'dzisiaj'
            elif days_since == 1:
                days_since_string = 'wczoraj'
            else:
                days_since_string = f'{cls.noun_variant(days_since, "dzień", "dni")} temu'

            if date or time:
                combined_information.append(f', {days_since_string}')
            else:
                combined_information.append(days_since_string)

        return ''.join(combined_information)

    @staticmethod
    def separator(block: str, width: int = os.get_terminal_size()[0]) -> str:
        """Generates a separator string to the specified length out of given blocks. Can print to the console."""
        pattern = (block * int(width / len(block)) + block)[:width].strip()
        return pattern

    @classmethod
    def generate_console_block(
            cls, info_lines: list, separator_block: str = None, *, first_console_block: bool = True
    ) -> str:
        """Takes a list of lines and returns a string ready for printing in the console."""
        info_block = []
        separator = None
        if separator_block is not None:
            separator = cls.separator(separator_block)
        if separator is not None and first_console_block:
            info_block.append(separator)
        for line in info_lines:
            info_block.append(line)
        if separator is not None:
            info_block.append(separator)

        return '\n'.join(info_block)


class Configurator:
    """Handles bot configuration."""
    def __init__(self, configuration_file_path: str, required_settings: tuple = None):
        self.configuration_file_path = configuration_file_path
        self.required_settings = required_settings
        self.configuration = {}

        self.ensure_completeness()

    def load(self) -> Dict[str, Union[str, float, int]]:
        """Loads the configuration from the file specified during class initialization."""
        # FUTURE
        if os.path.exists(self.configuration_file_path):
            with open(self.configuration_file_path, 'r') as configuration_file:
                self.configuration = json.load(configuration_file)
        # LEGACY; FOR REMOVAL
        else:
            with open(os.path.join(os.path.expanduser('~'), '.config', 'somsiad.conf'), 'r') as configuration_file:
                for line in configuration_file.readlines():
                    if not line.strip().startswith('#'):
                        line = line.strip().split('=', 1)
                        self.configuration[line[0].strip()] = line[1]
            with open(self.configuration_file_path, 'w') as configuration_file:
                json.dump(self.configuration, configuration_file, indent=4, ensure_ascii=False)

        return self.configuration

    def input_setting(self, setting, step_number: int = None):
        """Asks the CLI user to input a setting."""
        setting.input(step_number)
        self.write_setting(setting)

    def write_setting(self, setting):
        """Writes a key-value pair to the configuration file."""
        self.configuration[setting.name] = setting.value

        # LEGACY; FOR REMOVAL
        with open(os.path.join(os.path.expanduser('~'), '.config', 'somsiad.conf'), 'a') as configuration_file:
            configuration_file.write(f'{setting.name}={self.configuration[setting.name]}\n')

        # FUTURE
        with open(self.configuration_file_path, 'w') as configuration_file:
            json.dump(self.configuration, configuration_file, indent=4, ensure_ascii=False)

    def ensure_completeness(self) -> dict:
        """Loads the configuration from the file specified during class initialization and ensures
        that all required keys are present. If not, the CLI user is asked to input missing settings.
        If the file doesn't exist yet, configuration is started from scratch.
        """
        was_configuration_changed = False
        step_number = 1

        # LEGACY; FOR CHANGE
        if os.path.exists(os.path.join(os.path.expanduser('~'), '.config', 'somsiad.conf')):
            self.load()

        if self.required_settings is not None:
            if not self.configuration:
                for required_setting in self.required_settings:
                    self.input_setting(required_setting, step_number)
                    step_number += 1
                was_configuration_changed = True
            else:
                for required_setting in self.required_settings:
                    is_setting_present = False
                    for setting in self.configuration:
                        if setting == required_setting.name:
                            is_setting_present = True
                            break
                    if not is_setting_present:
                        self.input_setting(required_setting, step_number)
                        was_configuration_changed = True
                    step_number += 1

        if was_configuration_changed:
            print(f'Gotowe! Konfigurację zapisano w {self.configuration_file_path}.')

        return self.configuration

    def info(self) -> str:
        """Returns a string presenting the current configuration in a human-readable form."""
        if self.required_settings is None:
            return ''
        else:
            info = ''
            for setting in self.required_settings:
                # Handle the unit
                if setting.unit is None:
                    line = f'{setting}: {self.configuration[setting.name]}'
                elif isinstance(setting.unit, tuple) and len(setting.unit) == 2:
                    unit_variant = (
                        setting.unit[0] if int(self.configuration[setting.name]) == 1 else setting.unit[1]
                    )
                    line = f'{setting}: {self.configuration[setting.name]} {unit_variant}'
                else:
                    line = f'{setting}: {self.configuration[setting.name]} {setting.unit}'
                info = f'{info}{line}\n'

            line = f'Ścieżka pliku konfiguracyjnego: {self.configuration_file_path}'
            info = f'{info}{line}'

            return info


class Setting:
    """A setting used for configuration."""
    __slots__ = '_name', '_description', '_input_instruction', '_unit', '_value_type', '_default_value', '_value'

    def __init__(
            self, name: str, *, description: str, input_instruction: str, unit: Union[tuple, str] = None,
            value_type: str = None, default_value=None, value=None
    ):
        self._name = str(name)
        self._input_instruction = str(input_instruction)
        self._description = str(description)
        self._value_type = value_type
        self._default_value = None if default_value is None else self._convert_to_value_type(default_value)
        if unit is None:
            self._unit = None
        else:
            self._unit = tuple(map(str, unit)) if isinstance(unit, (list, tuple)) else str(unit)
        self._value = self._convert_to_value_type(value)

    def __repr__(self) -> str:
        return f'Setting(\'{self._name}\')'

    def __str__(self) -> str:
        return self._description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def input_instruction(self) -> str:
        return self._input_instruction

    @property
    def unit(self) -> Union[tuple, str]:
        return self._unit

    @property
    def value_type(self):
        return self._value_type

    @property
    def default_value(self):
        return self._default_value

    @property
    def value(self):
        return self._value

    @property
    def input_instruction_with_default_value(self) -> str:
        if self.default_value is None:
            return self.input_instruction
        else:
            return f'{self.input_instruction} (domyślnie {self.default_value})'

    @property
    def value_with_unit(self) -> str:
        if self._value is None:
            return 'brak'
        else:
            if isinstance(self._unit, (list, tuple)):
                if self._value_type in ('int', 'float') and abs(self._value) == 1:
                    return f'{self._value} {self._unit[0]}'
                else:
                    return f'{self._value} {self._unit[1]}'
            else:
                return f'{self.input_instruction} {self._unit})'

    def as_dict(self) -> str:
        return {
            'name': self._name,
            'description': self._description,
            'input_instruction': self._input_instruction,
            'unit': self._unit,
            'value_type': self._value_type,
            'default_value': self._default_value,
            'value': self._value
        }

    def _convert_to_value_type(self, value):
        if value is not None:
            if self._value_type == 'str':
                return str(value)
            elif self._value_type == 'int':
                return int(value)
            elif self._value_type == 'float':
                return float(value)
            else:
                return value
        else:
            return None

    def set_value(self, value=None):
        if value is None:
            self._value = self._default_value
        else:
            self._value = self._convert_to_value_type(value)

        return self._value

    def input(self, step_number: int = None):
        while True:
            if step_number is None:
                input_buffer = input(f'{self.input_instruction_with_default_value}:\n').strip()
            else:
                input_buffer = input(f'{step_number}. {self.input_instruction_with_default_value}:\n').strip()

            if input_buffer == '':
                if self._default_value is None:
                    print('Nie podano obowiązkowej wartości!')
                    continue
                else:
                    self.set_value()
                    break
            else:
                try:
                    self.set_value(input_buffer)
                    break
                except ValueError:
                    print(f'Podana wartość nie pasuje do typu {self._value_type}!')
                    continue

        return self.value
