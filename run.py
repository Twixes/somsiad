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

import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from configuration import configuration
from core import Essentials, Prefix, Somsiad, somsiad
from version import __version__


def run() -> Somsiad:
    if configuration['sentry_dsn']:
        print('Inicjowanie połączenia z Sentry...')
        sentry_sdk.init(
            configuration['sentry_dsn'],
            release=f'{configuration.get("sentry_proj") or "somsiad"}@{__version__}',
            integrations=[SqlalchemyIntegration(), AioHttpIntegration()],
        )
    somsiad.load_and_run((Essentials, Prefix))
    return somsiad


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, somsiad.signal_handler)
    signal.signal(signal.SIGINT, somsiad.signal_handler)
    run()
