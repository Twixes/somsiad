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
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
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
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_TOKEN', '')


@functools.lru_cache(maxsize=512)
def _resolve_guild_name(guild_id: int) -> str:
    """Fetch guild name from Discord API using the bot token. Falls back to the ID string."""
    try:
        resp = http_requests.get(
            f'{DISCORD_API_BASE}/guilds/{guild_id}',
            headers={'Authorization': f'Bot {DISCORD_BOT_TOKEN}'},
            timeout=DISCORD_REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            return resp.json().get('name', str(guild_id))
    except Exception:
        pass
    return str(guild_id)


@functools.lru_cache(maxsize=512)
def _resolve_channel_info(channel_id: int) -> tuple:
    """Fetch channel name and guild ID from Discord API. Returns (name, guild_id_or_None)."""
    try:
        resp = http_requests.get(
            f'{DISCORD_API_BASE}/channels/{channel_id}',
            headers={'Authorization': f'Bot {DISCORD_BOT_TOKEN}'},
            timeout=DISCORD_REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            ch = resp.json()
            guild_id = ch.get('guild_id')
            return ch.get('name', str(channel_id)), int(guild_id) if guild_id else None
    except Exception:
        pass
    return str(channel_id), None


def _make_location(server_id, channel_id):
    """Build a location dict with server/channel names resolved via Discord API."""
    loc = {}
    if channel_id:
        channel_name, inferred_guild_id = _resolve_channel_info(int(channel_id))
        loc['channel_id'] = str(channel_id)
        loc['channel_name'] = channel_name
        if not server_id and inferred_guild_id:
            server_id = inferred_guild_id
    if server_id:
        loc['server_id'] = str(server_id)
        loc['server_name'] = _resolve_guild_name(int(server_id))
    return loc


EVENT_TYPE_LABELS = {
    'warned': 'Ostrzeżenie',
    'kicked': 'Wyrzucenie',
    'banned': 'Ban',
    'unbanned': 'Unban',
    'pardoned': 'Przebaczenie',
    'joined': 'Dołączenie',
    'left': 'Opuszczenie',
}

EVENT_TYPE_ICONS = {
    'warned': '⚠️',
    'kicked': '👢',
    'banned': '🔨',
    'unbanned': '🔓',
    'pardoned': '🕊️',
    'joined': '📥',
    'left': '📤',
}


def format_event_type(type_str):
    return EVENT_TYPE_LABELS.get(type_str, type_str)

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
application.url_map.strict_slashes = False

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


def generate_csrf_token():
    if '_csrf_token' not in flask_session:
        flask_session['_csrf_token'] = secrets.token_hex(32)
    return flask_session['_csrf_token']


application.jinja_env.globals['csrf_token'] = generate_csrf_token


def api_login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in flask_session:
            return jsonify({'error': 'unauthorized'}), 401
        return f(*args, **kwargs)

    return decorated


def validate_api_csrf():
    token = flask_session.get('_csrf_token')
    if not token or token != request.headers.get('X-CSRF-Token'):
        abort(403)
    flask_session.pop('_csrf_token', None)


def format_birthday(birthday):
    if birthday is None:
        return None
    if birthday.year == BIRTHDAY_EDGE_YEAR:
        return birthday.strftime('%-d %B')
    return birthday.strftime('%-d %B %Y')


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
    return redirect('/panel/')


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

    return redirect('/panel/')


# ── Panel SPA ────────────────────────────────────────────

PANEL_DIST_DIR = os.path.join(os.path.dirname(__file__), 'panel', 'dist')


@application.route('/panel/assets/<path:filename>')
def panel_assets(filename):
    return send_from_directory(os.path.join(PANEL_DIST_DIR, 'assets'), filename)


@application.route('/panel/')
@application.route('/panel/<path:path>')
def panel_spa(path=''):
    return send_from_directory(PANEL_DIST_DIR, 'index.html')


# ── Panel API ────────────────────────────────────────────


def _ballot_type(letters, numeric_scale_max):
    if letters:
        return f"Wieloliterowe ({', '.join(letters.upper())})"
    if numeric_scale_max is not None:
        return f"Skala 1\u2013{numeric_scale_max}"
    return "Za / Przeciw"


@application.route('/panel/api/me')
def api_me():
    if 'user' not in flask_session:
        return jsonify({'error': 'unauthorized'}), 401
    return jsonify({'user': flask_session['user'], 'csrf_token': generate_csrf_token()})


@application.route('/panel/api/dashboard')
@api_login_required
def api_dashboard():
    user = flask_session['user']
    user_id = user['id']

    birthday = None
    pending_reminders = 0
    total_commands = 0
    total_ai_messages = 0
    total_oofs = 0
    active_polls = 0
    pending_burns = 0
    moderation_events = 0
    commands_by_week = []

    try:
        with get_db() as conn:
            cur = conn.cursor()

            # Fetch all scalar stats in a single round-trip using CTEs
            cur.execute(
                """
                WITH
                    b AS (SELECT birthday FROM born_persons WHERE user_id = %(uid)s),
                    r AS (SELECT COUNT(*) AS c FROM reminders WHERE user_id = %(uid)s AND has_been_executed = false),
                    cmd AS (SELECT COUNT(*) AS c FROM invocations WHERE user_id = %(uid)s AND full_command != 'hey'),
                    ai AS (SELECT COUNT(*) AS c FROM invocations WHERE user_id = %(uid)s AND full_command = 'hey'),
                    o AS (SELECT COALESCE(SUM(oofs), 0) AS c FROM oofers WHERE user_id = %(uid)s),
                    p AS (SELECT COUNT(*) AS c FROM ballots WHERE user_id = %(uid)s AND has_been_concluded = false),
                    bu AS (SELECT COUNT(*) AS c FROM burnings WHERE user_id = %(uid)s AND has_been_executed = false),
                    m AS (SELECT COUNT(*) AS c FROM events WHERE user_id = %(uid)s)
                SELECT
                    (SELECT birthday FROM b) AS birthday,
                    (SELECT c FROM r) AS pending_reminders,
                    (SELECT c FROM cmd) AS total_commands,
                    (SELECT c FROM ai) AS total_ai_messages,
                    (SELECT c FROM o) AS total_oofs,
                    (SELECT c FROM p) AS active_polls,
                    (SELECT c FROM bu) AS pending_burns,
                    (SELECT c FROM m) AS moderation_events
                """,
                {'uid': user_id},
            )
            stats = cur.fetchone()
            birthday = stats['birthday']
            pending_reminders = stats['pending_reminders']
            total_commands = stats['total_commands']
            total_ai_messages = stats['total_ai_messages']
            total_oofs = stats['total_oofs']
            active_polls = stats['active_polls']
            pending_burns = stats['pending_burns']
            moderation_events = stats['moderation_events']

            # Commands and AI messages per week for the last 12 weeks
            cur.execute(
                """
                SELECT date_trunc('week', created_at)::date AS week,
                       COUNT(*) FILTER (WHERE full_command != 'hey') AS commands,
                       COUNT(*) FILTER (WHERE full_command = 'hey') AS ai_messages
                FROM invocations
                WHERE user_id = %s AND created_at >= now() - interval '12 weeks'
                GROUP BY week ORDER BY week
                """,
                (user_id,),
            )
            week_data = {row['week']: (row['commands'], row['ai_messages']) for row in cur.fetchall()}
            today = dt.date.today()
            # Monday of the current week
            current_monday = today - dt.timedelta(days=today.weekday())
            for i in range(11, -1, -1):
                week_start = current_monday - dt.timedelta(weeks=i)
                cmds, ai = week_data.get(week_start, (0, 0))
                commands_by_week.append({
                    'week': week_start.isoformat(),
                    'commands': cmds,
                    'ai_messages': ai,
                })
    except Exception:
        logger.exception('Failed to load dashboard data for user %s', user_id)

    return jsonify({
        'birthday_display': format_birthday(birthday),
        'pending_reminders': pending_reminders,
        'total_commands': total_commands,
        'total_ai_messages': total_ai_messages,
        'total_oofs': total_oofs,
        'active_polls': active_polls,
        'pending_burns': pending_burns,
        'moderation_events': moderation_events,
        'commands_by_week': commands_by_week,
    })


@application.route('/panel/api/birthday')
@api_login_required
def api_birthday():
    user = flask_session['user']
    user_id = user['id']

    birthday = None
    public_servers = []

    try:
        with get_db() as conn:
            cur = conn.cursor()

            cur.execute("SELECT birthday FROM born_persons WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            birthday = row['birthday'] if row else None

            if birthday:
                cur.execute(
                    """
                    SELECT bpl.server_id FROM birthday_publicness_links bpl
                    JOIN servers s ON s.id = bpl.server_id
                    WHERE bpl.born_person_user_id = %s
                    ORDER BY bpl.server_id
                    """,
                    (user_id,),
                )
                public_servers = [
                    {'server_id': row['server_id'], 'server_name': _resolve_guild_name(row['server_id'])}
                    for row in cur.fetchall()
                ]
    except Exception:
        logger.exception('Failed to load birthday data for user %s', user_id)

    birthday_json = None
    if birthday:
        birthday_json = {
            'day': birthday.day,
            'month': birthday.month,
            'year': birthday.year if birthday.year != BIRTHDAY_EDGE_YEAR else None,
        }

    return jsonify({
        'birthday': birthday_json,
        'months': MONTHS_PL,
        'current_year': dt.date.today().year,
        'public_server_count': len(public_servers) if birthday else None,
        'public_servers': public_servers,
    })


@application.route('/panel/api/birthday', methods=['POST'])
@api_login_required
def api_birthday_update():
    validate_api_csrf()
    user = flask_session['user']
    user_id = user['id']

    data = request.get_json(silent=True) or {}

    try:
        day = int(data.get('day', 1))
        month = int(data.get('month', 1))
        year_str = str(data.get('year', '')).strip()
        year = int(year_str) if year_str else BIRTHDAY_EDGE_YEAR

        if year != BIRTHDAY_EDGE_YEAR and (year <= BIRTHDAY_EDGE_YEAR or year > dt.date.today().year):
            return jsonify({'error': 'Podaj poprawny rok urodzenia.'})

        birthday = dt.date(year, month, day)

        if year != BIRTHDAY_EDGE_YEAR and birthday > dt.date.today():
            return jsonify({'error': 'Data urodzin nie może być w przyszłości.'})

    except (ValueError, TypeError):
        return jsonify({'error': 'Nieprawidłowa data.'})

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO born_persons (user_id, birthday) VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE SET birthday = EXCLUDED.birthday
                """,
                (user_id, birthday),
            )
            conn.commit()
    except Exception:
        logger.exception('Failed to update birthday for user %s', user_id)
        return jsonify({'error': 'Wystąpił błąd podczas zapisywania.'})

    return jsonify({'ok': True, 'message': 'Zaktualizowano datę urodzin.'})


@application.route('/panel/api/birthday', methods=['DELETE'])
@api_login_required
def api_birthday_delete():
    validate_api_csrf()
    user = flask_session['user']
    user_id = user['id']

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE born_persons SET birthday = NULL WHERE user_id = %s", (user_id,))
            conn.commit()
    except Exception:
        logger.exception('Failed to delete birthday for user %s', user_id)
        return jsonify({'error': 'Wystąpił błąd.'})

    return jsonify({'ok': True, 'message': 'Usunięto datę urodzin.'})


@application.route('/panel/api/birthday/hide', methods=['POST'])
@api_login_required
def api_birthday_hide():
    validate_api_csrf()
    user = flask_session['user']
    user_id = user['id']

    data = request.get_json(silent=True) or {}
    server_id = data.get('server_id')
    if not server_id:
        return jsonify({'error': 'Nie podano serwera.'})

    try:
        server_id = int(server_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Nieprawidłowy identyfikator serwera.'})

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                DELETE FROM birthday_publicness_links
                WHERE born_person_user_id = %s AND server_id = %s
                """,
                (user_id, server_id),
            )
            conn.commit()
    except Exception:
        logger.exception('Failed to hide birthday on server %s for user %s', server_id, user_id)
        return jsonify({'error': 'Wystąpił błąd.'})

    return jsonify({'ok': True, 'message': 'Utajniono datę urodzin na serwerze.'})


@application.route('/panel/api/reminders')
@api_login_required
def api_reminders():
    user = flask_session['user']
    user_id = user['id']

    pending = []
    past = []

    try:
        with get_db() as conn:
            cur = conn.cursor()

            cur.execute(
                """
                SELECT confirmation_message_id, content, execute_at, requested_at, channel_id FROM reminders
                WHERE user_id = %s AND has_been_executed = false
                ORDER BY execute_at ASC
                """,
                (user_id,),
            )
            for row in cur.fetchall():
                pending.append({
                    'id': row['confirmation_message_id'],
                    'content': row['content'],
                    'execute_at': row['execute_at'].isoformat() if row['execute_at'] else None,
                    'requested_at': row['requested_at'].isoformat() if row['requested_at'] else None,
                    **_make_location(None, row['channel_id']),
                })

            cur.execute(
                """
                SELECT content, execute_at, channel_id FROM reminders
                WHERE user_id = %s AND has_been_executed = true
                ORDER BY execute_at DESC LIMIT 15
                """,
                (user_id,),
            )
            for row in cur.fetchall():
                past.append({
                    'content': row['content'],
                    'execute_at': row['execute_at'].isoformat() if row['execute_at'] else None,
                    **_make_location(None, row['channel_id']),
                })
    except Exception:
        logger.exception('Failed to load reminders for user %s', user_id)

    return jsonify({'pending': pending, 'past': past})


@application.route('/panel/api/reminders/<int:reminder_id>', methods=['DELETE'])
@api_login_required
def api_reminder_delete(reminder_id):
    validate_api_csrf()
    user = flask_session['user']
    user_id = user['id']

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                DELETE FROM reminders
                WHERE confirmation_message_id = %s AND user_id = %s AND has_been_executed = false
                """,
                (reminder_id, user_id),
            )
            deleted = cur.rowcount
            conn.commit()
    except Exception:
        logger.exception('Failed to delete reminder %s for user %s', reminder_id, user_id)
        return jsonify({'error': 'Wystąpił błąd podczas usuwania przypomnienia.'})

    if deleted:
        return jsonify({'ok': True, 'message': 'Anulowano przypomnienie.'})
    else:
        return jsonify({'error': 'Nie znaleziono przypomnienia do anulowania.'})


@application.route('/panel/api/commands')
@api_login_required
def api_commands():
    user = flask_session['user']
    user_id = user['id']

    total_count = 0
    unique_count = 0
    total_ai_messages = 0
    top_commands = []
    recent = []
    recent_ai = []

    try:
        with get_db() as conn:
            cur = conn.cursor()

            # Fetch command and AI counts in a single round-trip
            cur.execute(
                """
                WITH
                    cmd AS (
                        SELECT COUNT(*) AS total, COUNT(DISTINCT full_command) AS uniq
                        FROM invocations WHERE user_id = %s AND full_command != 'hey'
                    ),
                    ai AS (
                        SELECT COUNT(*) AS total
                        FROM invocations WHERE user_id = %s AND full_command = 'hey'
                    )
                SELECT
                    (SELECT total FROM cmd) AS total_count,
                    (SELECT uniq FROM cmd) AS unique_count,
                    (SELECT total FROM ai) AS total_ai_messages
                """,
                (user_id, user_id),
            )
            counts = cur.fetchone()
            total_count = counts['total_count']
            unique_count = counts['unique_count']
            total_ai_messages = counts['total_ai_messages']

            cur.execute(
                """
                SELECT full_command, server_id, COUNT(*) AS count FROM invocations
                WHERE user_id = %s AND full_command != 'hey'
                GROUP BY full_command, server_id ORDER BY count DESC LIMIT 20
                """,
                (user_id,),
            )
            top_commands = [
                {
                    'full_command': row['full_command'],
                    'count': row['count'],
                    **_make_location(row['server_id'], None),
                }
                for row in cur.fetchall()
            ]

            cur.execute(
                """
                SELECT full_command, server_id, channel_id, created_at FROM invocations
                WHERE user_id = %s AND full_command != 'hey'
                ORDER BY created_at DESC LIMIT 15
                """,
                (user_id,),
            )
            recent = [
                {
                    'full_command': row['full_command'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    **_make_location(row['server_id'], row['channel_id']),
                }
                for row in cur.fetchall()
            ]

            if total_ai_messages:
                cur.execute(
                    """
                    SELECT server_id, channel_id, created_at FROM invocations
                    WHERE user_id = %s AND full_command = 'hey'
                    ORDER BY created_at DESC LIMIT 15
                    """,
                    (user_id,),
                )
                recent_ai = [
                    {
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                        **_make_location(row['server_id'], row['channel_id']),
                    }
                    for row in cur.fetchall()
                ]
    except Exception:
        logger.exception('Failed to load command stats for user %s', user_id)

    most_used = top_commands[0]['full_command'] if top_commands else None

    return jsonify({
        'total_count': total_count,
        'unique_count': unique_count,
        'total_ai_messages': total_ai_messages,
        'most_used': most_used,
        'top_commands': top_commands,
        'recent': recent,
        'recent_ai': recent_ai,
    })


@application.route('/panel/api/commands/chart')
@api_login_required
def api_commands_chart():
    user = flask_session['user']
    user_id = user['id']

    weeks_count = request.args.get('weeks', 12, type=int)
    weeks_count = max(1, min(weeks_count, 520))  # Cap at ~10 years

    commands_by_week = []

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT date_trunc('week', created_at)::date AS week,
                       COUNT(*) FILTER (WHERE full_command != 'hey') AS commands,
                       COUNT(*) FILTER (WHERE full_command = 'hey') AS ai_messages
                FROM invocations
                WHERE user_id = %s AND created_at >= now() - make_interval(weeks => %s)
                GROUP BY week ORDER BY week
                """,
                (user_id, weeks_count),
            )
            week_data = {row['week']: (row['commands'], row['ai_messages']) for row in cur.fetchall()}
            today = dt.date.today()
            current_monday = today - dt.timedelta(days=today.weekday())
            for i in range(weeks_count - 1, -1, -1):
                week_start = current_monday - dt.timedelta(weeks=i)
                cmds, ai = week_data.get(week_start, (0, 0))
                commands_by_week.append({
                    'week': week_start.isoformat(),
                    'commands': cmds,
                    'ai_messages': ai,
                })
    except Exception:
        logger.exception('Failed to load commands chart for user %s', user_id)

    return jsonify({'commands_by_week': commands_by_week})


@application.route('/panel/api/moderation')
@api_login_required
def api_moderation():
    user = flask_session['user']
    user_id = user['id']

    events = []
    type_counts = []

    try:
        with get_db() as conn:
            cur = conn.cursor()

            # Fetch recent events and type counts in a single round-trip
            cur.execute(
                """
                WITH recent AS (
                    SELECT type, details, occurred_at, server_id, channel_id
                    FROM events WHERE user_id = %s
                    ORDER BY occurred_at DESC LIMIT 50
                ), counts AS (
                    SELECT type, COUNT(*) AS count
                    FROM events WHERE user_id = %s
                    GROUP BY type ORDER BY count DESC
                )
                SELECT 'event' AS _kind, type, details, occurred_at, server_id, channel_id, NULL::bigint AS count FROM recent
                UNION ALL
                SELECT 'count' AS _kind, type, NULL, NULL, NULL::bigint, NULL::bigint, count FROM counts
                """,
                (user_id, user_id),
            )
            for row in cur.fetchall():
                if row['_kind'] == 'event':
                    events.append({
                        'type': row['type'],
                        'type_label': format_event_type(row['type']),
                        'type_icon': EVENT_TYPE_ICONS.get(row['type'], ''),
                        'details': row['details'],
                        'occurred_at': row['occurred_at'].isoformat() if row['occurred_at'] else None,
                        **_make_location(row['server_id'], row['channel_id']),
                    })
                else:
                    type_counts.append({
                        'type': row['type'],
                        'label': format_event_type(row['type']),
                        'icon': EVENT_TYPE_ICONS.get(row['type'], ''),
                        'count': row['count'],
                    })
    except Exception:
        logger.exception('Failed to load moderation data for user %s', user_id)

    return jsonify({'events': events, 'type_counts': type_counts})


@application.route('/panel/api/polls')
@api_login_required
def api_polls():
    user = flask_session['user']
    user_id = user['id']

    active = []
    past = []

    try:
        with get_db() as conn:
            cur = conn.cursor()

            cur.execute(
                """
                SELECT matter, letters, commenced_at, conclude_at, numeric_scale_max, has_been_concluded, channel_id FROM (
                    (SELECT matter, letters, commenced_at, conclude_at, numeric_scale_max, has_been_concluded, channel_id
                     FROM ballots WHERE user_id = %s AND has_been_concluded = false ORDER BY commenced_at ASC)
                    UNION ALL
                    (SELECT matter, letters, commenced_at, conclude_at, numeric_scale_max, has_been_concluded, channel_id
                     FROM ballots WHERE user_id = %s AND has_been_concluded = true ORDER BY conclude_at DESC LIMIT 15)
                ) sub
                """,
                (user_id, user_id),
            )
            for row in cur.fetchall():
                entry = {
                    'matter': row['matter'],
                    'type': _ballot_type(row['letters'], row['numeric_scale_max']),
                    'commenced_at': row['commenced_at'].isoformat() if row['commenced_at'] else None,
                    'conclude_at': row['conclude_at'].isoformat() if row['conclude_at'] else None,
                    **_make_location(None, row['channel_id']),
                }
                if row['has_been_concluded']:
                    past.append(entry)
                else:
                    active.append(entry)
    except Exception:
        logger.exception('Failed to load polls for user %s', user_id)

    return jsonify({'active': active, 'past': past})


@application.route('/panel/api/burns')
@api_login_required
def api_burns():
    user = flask_session['user']
    user_id = user['id']

    pending = []
    past = []

    try:
        with get_db() as conn:
            cur = conn.cursor()

            cur.execute(
                """
                SELECT requested_at, execute_at, has_been_executed, channel_id FROM (
                    (SELECT requested_at, execute_at, has_been_executed, channel_id
                     FROM burnings WHERE user_id = %s AND has_been_executed = false ORDER BY execute_at ASC)
                    UNION ALL
                    (SELECT requested_at, execute_at, has_been_executed, channel_id
                     FROM burnings WHERE user_id = %s AND has_been_executed = true ORDER BY execute_at DESC LIMIT 15)
                ) sub
                """,
                (user_id, user_id),
            )
            for row in cur.fetchall():
                entry = {
                    'requested_at': row['requested_at'].isoformat() if row['requested_at'] else None,
                    'execute_at': row['execute_at'].isoformat() if row['execute_at'] else None,
                    **_make_location(None, row['channel_id']),
                }
                if row['has_been_executed']:
                    past.append(entry)
                else:
                    pending.append(entry)
    except Exception:
        logger.exception('Failed to load burns for user %s', user_id)

    return jsonify({'pending': pending, 'past': past})


@application.route('/panel/api/oof')
@api_login_required
def api_oof():
    user = flask_session['user']
    user_id = user['id']

    total_oofs = 0
    server_count = 0
    per_server = []

    try:
        with get_db() as conn:
            cur = conn.cursor()

            cur.execute(
                """
                SELECT COALESCE(SUM(oofs), 0) AS total, COUNT(*) AS server_count
                FROM oofers WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()
            total_oofs = row['total']
            server_count = row['server_count']

            cur.execute(
                "SELECT server_id, oofs FROM oofers WHERE user_id = %s ORDER BY oofs DESC",
                (user_id,),
            )
            per_server = [
                {
                    'server_id': str(row['server_id']),
                    'server_name': _resolve_guild_name(row['server_id']),
                    'oofs': row['oofs'],
                }
                for row in cur.fetchall()
            ]
    except Exception:
        logger.exception('Failed to load oof data for user %s', user_id)

    return jsonify({
        'total_oofs': total_oofs,
        'server_count': server_count,
        'per_server': per_server,
    })


@application.route('/panel/api/logout', methods=['POST'])
@api_login_required
def api_logout():
    validate_api_csrf()
    flask_session.pop('user', None)
    return jsonify({'ok': True})
