#!/usr/bin/env python3

# Copyright 2018–2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from configuration import configuration

if configuration['sentry_dsn'] is not None:
    import sentry_sdk
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from version import __version__
    sentry_sdk.init(
        configuration['sentry_dsn'], release=f'{configuration["sentry_proj"] or "somsiad"}@{__version__}',
        integrations=[SqlalchemyIntegration()]
    )

from core import somsiad
from utilities import setlocale
from data import create_all_tables
from plugins import *

if __name__ == '__main__':
    print('Budzenie Somsiada...')
    setlocale()
    create_all_tables()
    somsiad.controlled_run()
