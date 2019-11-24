#!/usr/bin/python3

# Copyright 2019 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import sys
import os
import json


def migrate_from_json_to_env():
    print('Migrating configuration from .json to .env... ', end='')
    json_f_path = os.path.join(os.path.expanduser('~'), '.config', 'somsiad.json')
    env_f_path = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), '.env')
    if os.path.exists(json_f_path):
        with open(json_f_path, 'r') as json_f:
            configuration = json.load(json_f)
        with open(env_f_path, 'a') as env_f:
            for key, value in configuration.items():
                env_f.write(f'{key.upper()}={value}\n')
        os.remove(json_f_path)
        print(f'Done: moved from {json_f_path} to {env_f_path}')
    else:
        print(f'Skipped: no file at {json_f_path}')


migrate_from_json_to_env()
