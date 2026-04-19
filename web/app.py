import base64
import calendar
import datetime as dt
import functools
import locale
import logging
import os
import random
import secrets
from contextlib import contextmanager
from typing import Optional
from urllib.parse import urlencode

import markdown
import psycopg2
import psycopg2.extras
import psycopg2.sql
import redis
import requests as http_requests
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session as flask_session,
    url_for,
)

logger = logging.getLogger(__name__)

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

MONTHS_PL = [
    (1, 'Styczeń'),
    (2, 'Luty'),
    (3, 'Marzec'),
    (4, 'Kwiecień'),
    (5, 'Maj'),
    (6, 'Czerwiec'),
    (7, 'Lipiec'),
    (8, 'Sierpień'),
    (9, 'Wrzesień'),
    (10, 'Październik'),
    (11, 'Listopad'),
    (12, 'Grudzień'),
]

BIRTHDAY_EDGE_YEAR = 1900
DISCORD_REQUEST_TIMEOUT = 10

# Tables with user_id that must be wiped on data-processing opt-out.
# Keep in sync with data.USER_RELATED_MODELS in the bot codebase.
USER_DATA_TABLES = (
    'invocations',
    'reminders',
    'burnings',
    'image9000s',
    'events',
    'ballots',
    'born_persons',
    'oofers',
)

locale.setlocale(locale.LC_ALL, os.getenv('LC_ALL'))
calendar.setfirstweekday(calendar.MONDAY)

redis_connection = redis.Redis.from_url(os.environ['REDIS_URL'])

application = Flask(__name__)

_secret_key = os.environ.get('SECRET_KEY')
if not _secret_key:
    logger.warning(
        'SECRET_KEY is not set — generating a random key. '
        'Sessions will not persist across restarts or gunicorn workers.'
    )
    _secret_key = secrets.token_hex(32)
application.secret_key = _secret_key

application.permanent_session_lifetime = dt.timedelta(days=30)
application.config['SESSION_COOKIE_HTTPONLY'] = True
application.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
if os.environ.get('SESSION_COOKIE_SECURE', '').lower() in ('1', 'true', 'yes'):
    application.config['SESSION_COOKIE_SECURE'] = True

# Discord OAuth2
DISCORD_CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID', '')
if not DISCORD_CLIENT_ID:
    # Derive from bot token: first segment is base64-encoded application ID
    _token = os.environ.get('DISCORD_TOKEN', '')
    if _token:
        DISCORD_CLIENT_ID = base64.b64decode(_token.split('.')[0] + '==').decode()
DISCORD_CLIENT_SECRET = os.environ.get('DISCORD_CLIENT_SECRET', '')
DISCORD_REDIRECT_URI = os.environ.get('DISCORD_REDIRECT_URI', '')
DISCORD_API_BASE = 'https://discord.com/api/v10'

DATABASE_URL = os.environ.get('DATABASE_URL', '')


# ── Helpers ──────────────────────────────────────────────


@contextmanager
def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()


def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in flask_session:
            return redirect(url_for('panel_login'))
        return f(*args, **kwargs)

    return decorated


def generate_csrf_token():
    if '_csrf_token' not in flask_session:
        flask_session['_csrf_token'] = secrets.token_hex(32)
    return flask_session['_csrf_token']


application.jinja_env.globals['csrf_token'] = generate_csrf_token


def validate_csrf():
    token = flask_session.get('_csrf_token')
    if not token or token != request.form.get('_csrf_token'):
        abort(403)
    flask_session.pop('_csrf_token', None)


def format_birthday(birthday):
    if birthday is None:
        return None
    if birthday.year == BIRTHDAY_EDGE_YEAR:
        return birthday.strftime('%-d %B')
    return birthday.strftime('%-d %B %Y')


def format_datetime(value):
    if value is None:
        return '—'
    return value.strftime('%-d %B %Y, %H:%M')


# ── Landing pages (existing) ────────────────────────────


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


@functools.lru_cache(maxsize=None)
def _load_document(path):
    with open(path, encoding='utf-8') as f:
        return markdown.markdown(f.read())


@application.route('/polityka-prywatnosci')
def privacy_policy():
    return render_template(
        '_document.html',
        title="Somsiad / Polityka prywatności",
        content=_load_document('documents/polityka-prywatnosci.md'),
    )


@application.route('/warunki-swiadczenia-uslugi')
def terms_of_service():
    return render_template(
        '_document.html',
        title="Somsiad / Warunki świadczenia usługi",
        content=_load_document('documents/warunki-swiadczenia-uslugi.md'),
    )


# ── Discord OAuth2 ──────────────────────────────────────


@application.route('/panel/login')
def panel_login():
    if 'user' in flask_session:
        return redirect(url_for('panel_dashboard'))
    return render_template('panel_login.html')


@application.route('/panel/auth')
def panel_auth():
    state = secrets.token_urlsafe(32)
    flask_session['oauth_state'] = state
    params = {
        'client_id': DISCORD_CLIENT_ID,
        'redirect_uri': DISCORD_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'identify',
        'state': state,
    }
    return redirect(f'{DISCORD_API_BASE}/oauth2/authorize?' + urlencode(params))


@application.route('/panel/callback')
def panel_callback():
    # Validate OAuth state to prevent login CSRF
    expected_state = flask_session.pop('oauth_state', None)
    received_state = request.args.get('state')
    if not expected_state or expected_state != received_state:
        flash('Nieprawidłowy stan sesji. Spróbuj zalogować się ponownie.', 'error')
        return redirect(url_for('panel_login'))

    code = request.args.get('code')
    if not code:
        flash('Logowanie anulowane.', 'error')
        return redirect(url_for('panel_login'))

    # Exchange code for access token
    token_response = http_requests.post(
        f'{DISCORD_API_BASE}/oauth2/token',
        data={
            'client_id': DISCORD_CLIENT_ID,
            'client_secret': DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': DISCORD_REDIRECT_URI,
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=DISCORD_REQUEST_TIMEOUT,
    )

    if token_response.status_code != 200:
        flash('Nie udało się zalogować. Spróbuj ponownie.', 'error')
        return redirect(url_for('panel_login'))

    token_data = token_response.json()
    access_token = token_data.get('access_token')
    if not access_token:
        flash('Nie udało się zalogować. Spróbuj ponownie.', 'error')
        return redirect(url_for('panel_login'))

    # Get user info
    user_response = http_requests.get(
        f'{DISCORD_API_BASE}/users/@me',
        headers={'Authorization': f'Bearer {access_token}'},
        timeout=DISCORD_REQUEST_TIMEOUT,
    )

    if user_response.status_code != 200:
        flash('Nie udało się pobrać danych użytkownika.', 'error')
        return redirect(url_for('panel_login'))

    user_data = user_response.json()
    user_id = int(user_data['id'])
    display_name = user_data.get('global_name') or user_data['username']

    avatar_hash = user_data.get('avatar')
    if avatar_hash:
        ext = 'gif' if avatar_hash.startswith('a_') else 'png'
        avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{ext}?size=128"
    else:
        default_index = (user_id >> 22) % 6
        avatar_url = f"https://cdn.discordapp.com/embed/avatars/{default_index}.png"

    flask_session['user'] = {
        'id': user_id,
        'username': user_data['username'],
        'display_name': display_name,
        'avatar_url': avatar_url,
    }
    flask_session.permanent = True

    return redirect(url_for('panel_dashboard'))


@application.route('/panel/logout', methods=['POST'])
def panel_logout():
    validate_csrf()
    flask_session.pop('user', None)
    return redirect(url_for('index'))


# ── Panel: Dashboard ────────────────────────────────────


@application.route('/panel/')
@login_required
def panel_dashboard():
    user = flask_session['user']
    user_id = user['id']

    birthday = None
    pending_reminders = 0
    opted_out = False

    try:
        with get_db() as conn:
            cur = conn.cursor()

            cur.execute("SELECT birthday FROM born_persons WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            birthday = row['birthday'] if row else None

            cur.execute(
                "SELECT COUNT(*) AS count FROM reminders WHERE user_id = %s AND has_been_executed = false",
                (user_id,),
            )
            pending_reminders = cur.fetchone()['count']

            cur.execute("SELECT user_id FROM data_processing_opt_outs WHERE user_id = %s", (user_id,))
            opted_out = cur.fetchone() is not None
    except Exception:
        logger.exception('Failed to load dashboard data for user %s', user_id)
        flash('Nie udało się załadować niektórych danych.', 'error')

    # Bot status from Redis
    heartbeat_raw = redis_connection.get('somsiad/heartbeat')
    bot_online = heartbeat_raw is not None
    version_raw = redis_connection.get('somsiad/version')
    bot_version = version_raw.decode('utf-8') if version_raw else None

    return render_template(
        'panel_dashboard.html',
        user=user,
        active_page='dashboard',
        birthday=birthday,
        birthday_display=format_birthday(birthday),
        pending_reminders=pending_reminders,
        opted_out=opted_out,
        bot_online=bot_online,
        bot_version=bot_version,
        status_emoji=random.choice(EMOJIS),
    )


# ── Panel: Birthday ─────────────────────────────────────


@application.route('/panel/urodziny')
@login_required
def panel_birthday():
    user = flask_session['user']
    user_id = user['id']

    birthday = None
    public_server_count = None

    try:
        with get_db() as conn:
            cur = conn.cursor()

            cur.execute("SELECT birthday FROM born_persons WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            birthday = row['birthday'] if row else None

            if birthday:
                cur.execute(
                    "SELECT COUNT(*) AS count FROM birthday_publicness_links WHERE born_person_user_id = %s",
                    (user_id,),
                )
                public_server_count = cur.fetchone()['count']
    except Exception:
        logger.exception('Failed to load birthday data for user %s', user_id)
        flash('Nie udało się załadować danych urodzinowych.', 'error')

    return render_template(
        'panel_birthday.html',
        user=user,
        active_page='birthday',
        birthday=birthday,
        months=MONTHS_PL,
        current_year=dt.date.today().year,
        public_server_count=public_server_count,
    )


@application.route('/panel/urodziny/zapisz', methods=['POST'])
@login_required
def panel_birthday_update():
    validate_csrf()
    user = flask_session['user']
    user_id = user['id']

    try:
        day = int(request.form.get('day', 1))
        month = int(request.form.get('month', 1))
        year_str = request.form.get('year', '').strip()
        year = int(year_str) if year_str else BIRTHDAY_EDGE_YEAR

        if year != BIRTHDAY_EDGE_YEAR and (year <= BIRTHDAY_EDGE_YEAR or year > dt.date.today().year):
            flash('Podaj poprawny rok urodzenia.', 'error')
            return redirect(url_for('panel_birthday'))

        birthday = dt.date(year, month, day)

        if year != BIRTHDAY_EDGE_YEAR and birthday > dt.date.today():
            flash('Data urodzin nie może być w przyszłości.', 'error')
            return redirect(url_for('panel_birthday'))

    except (ValueError, TypeError):
        flash('Nieprawidłowa data.', 'error')
        return redirect(url_for('panel_birthday'))

    try:
        with get_db() as conn:
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO born_persons (user_id, birthday) VALUES (%s, %s) "
                "ON CONFLICT (user_id) DO UPDATE SET birthday = EXCLUDED.birthday",
                (user_id, birthday),
            )

            conn.commit()
    except Exception:
        logger.exception('Failed to update birthday for user %s', user_id)
        flash('Wystąpił błąd podczas zapisywania.', 'error')
        return redirect(url_for('panel_birthday'))

    flash('Zaktualizowano datę urodzin.', 'success')
    return redirect(url_for('panel_birthday'))


@application.route('/panel/urodziny/usun', methods=['POST'])
@login_required
def panel_birthday_delete():
    validate_csrf()
    user = flask_session['user']
    user_id = user['id']

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE born_persons SET birthday = NULL WHERE user_id = %s", (user_id,))
            conn.commit()
    except Exception:
        logger.exception('Failed to delete birthday for user %s', user_id)
        flash('Wystąpił błąd.', 'error')
        return redirect(url_for('panel_birthday'))

    flash('Usunięto datę urodzin.', 'success')
    return redirect(url_for('panel_birthday'))


# ── Panel: Reminders ─────────────────────────────────────


@application.route('/panel/przypomnienia')
@login_required
def panel_reminders():
    user = flask_session['user']
    user_id = user['id']

    pending = []
    past = []

    try:
        with get_db() as conn:
            cur = conn.cursor()

            cur.execute(
                "SELECT content, execute_at, requested_at FROM reminders "
                "WHERE user_id = %s AND has_been_executed = false "
                "ORDER BY execute_at ASC",
                (user_id,),
            )
            for row in cur.fetchall():
                pending.append(
                    {
                        'content': row['content'],
                        'execute_at': format_datetime(row['execute_at']),
                        'requested_at': format_datetime(row['requested_at']),
                    }
                )

            cur.execute(
                "SELECT content, execute_at FROM reminders "
                "WHERE user_id = %s AND has_been_executed = true "
                "ORDER BY execute_at DESC LIMIT 15",
                (user_id,),
            )
            for row in cur.fetchall():
                past.append(
                    {
                        'content': row['content'],
                        'execute_at': format_datetime(row['execute_at']),
                    }
                )
    except Exception:
        logger.exception('Failed to load reminders for user %s', user_id)
        flash('Nie udało się załadować przypomnień.', 'error')

    return render_template(
        'panel_reminders.html',
        user=user,
        active_page='reminders',
        pending_reminders=pending,
        past_reminders=past,
    )


# ── Panel: Privacy ───────────────────────────────────────


@application.route('/panel/prywatnosc')
@login_required
def panel_privacy():
    user = flask_session['user']
    user_id = user['id']

    opted_out = False

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM data_processing_opt_outs WHERE user_id = %s", (user_id,))
            opted_out = cur.fetchone() is not None
    except Exception:
        logger.exception('Failed to load privacy status for user %s', user_id)
        flash('Nie udało się załadować statusu prywatności.', 'error')

    return render_template(
        'panel_privacy.html',
        user=user,
        active_page='privacy',
        opted_out=opted_out,
    )


@application.route('/panel/prywatnosc/zapisz', methods=['POST'])
@login_required
def panel_privacy_update():
    validate_csrf()
    user = flask_session['user']
    user_id = user['id']
    action = request.form.get('action')

    if action not in ('opt_out', 'opt_in'):
        flash('Nieprawidłowa akcja.', 'error')
        return redirect(url_for('panel_privacy'))

    try:
        with get_db() as conn:
            cur = conn.cursor()

            if action == 'opt_out':
                # Delete user data from all related tables.
                # This list mirrors data.USER_RELATED_MODELS in the bot.
                cur.execute("DELETE FROM birthday_publicness_links WHERE born_person_user_id = %s", (user_id,))
                for table in USER_DATA_TABLES:
                    cur.execute(
                        psycopg2.sql.SQL("DELETE FROM {} WHERE user_id = %s").format(
                            psycopg2.sql.Identifier(table)
                        ),
                        (user_id,),
                    )
                cur.execute(
                    "INSERT INTO data_processing_opt_outs (user_id) VALUES (%s) ON CONFLICT DO NOTHING",
                    (user_id,),
                )
                conn.commit()
                flash('Wypisano z przetwarzania danych. Twoje dane zostały usunięte.', 'success')

            elif action == 'opt_in':
                cur.execute("DELETE FROM data_processing_opt_outs WHERE user_id = %s", (user_id,))
                conn.commit()
                flash('Przywrócono przetwarzanie danych.', 'success')
    except Exception:
        logger.exception('Failed to update privacy setting for user %s', user_id)
        flash('Wystąpił błąd.', 'error')

    return redirect(url_for('panel_privacy'))
