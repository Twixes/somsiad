#!/usr/bin/env python3

# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import locale
import calendar
import somsiad
import server_data
from plugins import *

ACCEPTED_LOCALES = ('pl_PL.utf8', 'pl_PL.UTF-8')


def setlocale(locale_index: int = 0):
    """Set program locale and first day of the week."""
    try:
        locale.setlocale(locale.LC_ALL, ACCEPTED_LOCALES[locale_index])
    except locale.Error:
        return setlocale(locale_index + 1)
    except IndexError:
        raise Exception(
            f'no locale from the list of accepted ones ({", ".join(ACCEPTED_LOCALES)}) was found in the system'
        )
    calendar.setfirstweekday(calendar.MONDAY)


if __name__ == '__main__':
    print('Budzenie Somsiada...')
    setlocale()
    somsiad.somsiad.controlled_run()
