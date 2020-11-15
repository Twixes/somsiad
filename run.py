#!/usr/bin/env python3

import os

env_ptvsd = os.getenv('PTVSD')
if env_ptvsd:
    import ptvsd
    print('Oczekiwanie na połączenie debuggera VS Code…')
    ptvsd.enable_attach(address=('0.0.0.0', 5678))
    if env_ptvsd.lower() == 'wait':
        ptvsd.wait_for_attach()

import signal
from configuration import configuration
import sentry_sdk
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from core import Essentials, Prefix, somsiad
from version import __version__

if __name__ == '__main__':
    signal.signal(signal.SIGINT, somsiad.signal_handler)
    if configuration['sentry_dsn']:
        print('Inicjowanie połączenia z Sentry...')
        sentry_sdk.init(
            configuration['sentry_dsn'], release=f'{configuration["sentry_proj"] or "somsiad"}@{__version__}',
            integrations=[SqlalchemyIntegration(), AioHttpIntegration()]
        )
    somsiad.load_and_run((Essentials, Prefix))
