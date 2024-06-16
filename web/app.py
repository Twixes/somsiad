import calendar
import datetime as dt
import locale
import os
import random
from typing import Optional

import markdown
import redis
from flask import Flask, render_template

EMOJIS = [
    '🐜',
    '🅱️',
    '🔥',
    '🐸',
    '🤔',
    '💥',
    '👌',
    '💩',
    '🐇',
    '🐰',
    '🦅',
    '🙃',
    '😎',
    '😩',
    '👹',
    '🤖',
    '✌️',
    '💭',
    '🙌',
    '👋',
    '💪',
    '👀',
    '👷',
    '🕵️',
    '💃',
    '🎩',
    '🤠',
    '🐕',
    '🐈',
    '🐹',
    '🐨',
    '🐽',
    '🐙',
    '🐧',
    '🐔',
    '🐎',
    '🦄',
    '🐝',
    '🐢',
    '🐬',
    '🐋',
    '🐐',
    '🌵',
    '🌻',
    '🌞',
    '☄️',
    '⚡',
    '🦆',
    '🦉',
    '🦊',
    '🍎',
    '🍉',
    '🍇',
    '🍑',
    '🍍',
    '🍆',
    '🍞',
    '🧀',
    '🍟',
    '🎂',
    '🍬',
    '🍭',
    '🍪',
    '🥑',
    '🥔',
    '🎨',
    '🎷',
    '🎺',
    '👾',
    '🎯',
    '🥁',
    '🚀',
    '🛰️',
    '⚓',
    '🏖️',
    '✨',
    '🌈',
    '💡',
    '💈',
    '🔭',
    '🎈',
    '🎉',
    '💯',
    '💝',
    '☢️',
    '🆘',
    '♨️',
]

locale.setlocale(locale.LC_ALL, os.getenv('LC_ALL'))
calendar.setfirstweekday(calendar.MONDAY)

redis_connection = redis.Redis.from_url(os.environ['REDIS_URL'])
application = Flask(__name__)


@application.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@application.route('/')
def index():
    heartbeat_raw = redis_connection.get('somsiad/heartbeat')
    heartbeat: Optional[dt.datetime] = (
        dt.datetime.fromisoformat(heartbeat_raw.decode('utf-8')) if heartbeat_raw else None
    )

    server_count_raw = redis_connection.get('somsiad/server_count')
    server_count: Optional[int] = int(server_count_raw.decode('utf-8')) if server_count_raw else None
    server_count_display: str = f'{server_count:n}' if server_count else 'Ileś'

    user_count_raw = redis_connection.get('somsiad/user_count')
    user_count: Optional[int] = int(user_count_raw.decode('utf-8')) if user_count_raw else None
    user_count_display: str = f'{user_count:n}' if user_count else 'Ileś'

    version_raw = redis_connection.get('somsiad/version')
    version: str = version_raw.decode('utf-8') if version_raw else '0.0.0'

    emoji: str = random.choice(EMOJIS)

    return render_template(
        'index.html',
        heartbeat=heartbeat,
        server_count_display=server_count_display,
        user_count_display=user_count_display,
        version=version,
        emoji=emoji,
    )


@application.route('/polityka-prywatnosci')
def privacy_policy():
    return render_template(
        '_document.html',
        title="Somsiad / Polityka prywatności",
        content=markdown.markdown(open('documents/polityka-prywatnosci.md').read()),
    )


@application.route('/warunki-swiadczenia-uslugi')
def terms_of_service():
    return render_template(
        '_document.html',
        title="Somsiad / Warunki świadczenia usługi",
        content=markdown.markdown(open('documents/warunki-swiadczenia-uslugi.md').read()),
    )
