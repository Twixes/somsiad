#!/usr/bin/env python3

import asyncio
import logging
import os
from re import M
import resource
from tkinter.tix import MAX

logger = logging.getLogger(__name__)

env_ptvsd = os.getenv('PTVSD')
if env_ptvsd:
    import ptvsd

    logger.info('Awaiting VS Code debugger connection...')
    ptvsd.enable_attach(address=('0.0.0.0', 5678))
    if env_ptvsd.lower() == 'wait':
        ptvsd.wait_for_attach()

import signal

import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from discord.utils import setup_logging

from configuration import configuration
from core import Essentials, Prefix, somsiad
from version import __version__

logger = logging.getLogger(__name__)

MAX_MEMORY = 2_000_000_000 # Limit to 2 GB to keep costs down

if __name__ == '__main__':
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    resource.setrlimit(resource.RLIMIT_AS, (MAX_MEMORY, hard))
    setup_logging()
    signal.signal(signal.SIGTERM, somsiad.signal_handler)
    signal.signal(signal.SIGINT, somsiad.signal_handler)
    if configuration['sentry_dsn']:
        sentry_sdk.init(
            configuration['sentry_dsn'],
            release=f'{configuration.get("sentry_proj") or "somsiad"}@{__version__}',
            integrations=[SqlalchemyIntegration(), AioHttpIntegration()],
        )
    asyncio.run(somsiad.load_and_start((Essentials, Prefix)))
