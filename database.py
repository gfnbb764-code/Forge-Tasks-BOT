# ============================================================
# TASK BOT — DATABASE.PY
# Forge Tasks BOT
# SQLite Database Manager
# Python 3.11+
# ============================================================

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone


# ============================================================
# CONFIG
# ============================================================

DATABASE_FOLDER = "data"

DEFAULT_DATABASE_FILE = os.path.join(
    DATABASE_FOLDER,
    "tasks.db"
)

DATABASE_FILE = os.getenv(
    "DATABASE_PATH",
    DEFAULT_DATABASE_FILE
)


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_LANGUAGE = os.getenv(
    "DEFAULT_LANGUAGE",
    "ar"
)

DEFAULT_CURRENCY = os.getenv(
    "DEFAULT_CURRENCY",
    "Coins"
)

DEFAULT_CURRENCY_SYMBOL = os.getenv(
    "DEFAULT_CURRENCY_SYMBOL",
    "🪙"
)

DEFAULT_XP_ENABLED = (
    os.getenv(
        "XP_ENABLED",
        "true"
    ).lower()
    == "true"
)

DEFAULT_REMINDERS_ENABLED = (
    os.getenv(
        "REMINDERS_ENABLED",
        "true"
    ).lower()
    == "true"
)

DEFAULT_DAILY_ENABLED = (
    os.getenv(
        "DAILY_TASKS_ENABLED",
        "true"
    ).lower()
    == "true"
)

DEFAULT_WEEKLY_ENABLED = (
    os.getenv(
        "WEEKLY_TASKS_ENABLED",
        "true"
    ).lower()
    == "true"
)

DEFAULT_MONTHLY_ENABLED = (
    os.getenv(
        "MONTHLY_TASKS_ENABLED",
        "false"
    ).lower()
    == "true"
)

DEFAULT_LEVEL_UP_ENABLED = (
    os.getenv(
        "LEVEL_UP_ENABLED",
        "true"
    ).lower()
    == "true"
)

DEFAULT_LEVEL_UP_MENTION = (
    os.getenv(
        "LEVEL_UP_MENTION",
        "true"
    ).lower()
    == "true"
)

DEFAULT_LEVEL_UP_MESSAGE = os.getenv(
    "LEVEL_UP_MESSAGE",
    "🎉 مبروك {mention}! وصلت إلى المستوى {level}!"
)


# ============================================================
# DATABASE DIRECTORY
# ============================================================

database_directory = os.path.dirname(
    DATABASE_FILE
)

if database_directory:

    os.makedirs(
        database_directory,
        exist_ok=True
    )

else:

    os.makedirs(
        DATABASE_FOLDER,
        exist_ok=True
    )


# ============================================================
# DATABASE CONNECTION
# ============================================================

connection = sqlite3.connect(
    DATABASE_FILE,
    check_same_thread=False
)

connection.row_factory = sqlite3.Row

cursor = connection.cursor()


# ============================================================
# SQLITE SETTINGS
# ============================================================

cursor.execute(
    "PRAGMA foreign_keys = ON"
)

cursor.execute(
    "PRAGMA journal_mode = WAL"
)

cursor.execute(
    "PRAGMA synchronous = NORMAL"
)

connection.commit()


# ============================================================
# TIME
# ============================================================

def now():

    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# DATABASE MIGRATION HELPER
# ============================================================

def column_exists(
    table,
    column
):

    cursor.execute(
        f"PRAGMA table_info({table})"
    )

    columns = cursor.fetchall()

    for row in columns:

        if row["name"] == column:

            return True

    return False


def add_column_if_missing(
    table,
    column,
    definition
):

    if column_exists(
        table,
        column
    ):

        return

    cursor.execute(
        f"""
        ALTER TABLE {table}
        ADD COLUMN {column} {definition}
        """
    )


# ============================================================
# TABLES
# ============================================================

def initialize_database(
    database_path=None
):

    global connection
    global cursor
    global DATABASE_FILE

    if database_path:

        requested_path = os.path.abspath(
            database_path
        )

        current_path = os.path.abspath(
            DATABASE_FILE
        )

        if requested_path != current_path:

            try:

                connection.close()

            except Exception:

                pass

            DATABASE_FILE = requested_path

            database_directory = os.path.dirname(
                DATABASE_FILE
            )

            if database_directory:

                os.makedirs(
                    database_directory,
                    exist_ok=True
                )

            connection = sqlite3.connect(
                DATABASE_FILE,
                check_same_thread=False
            )

            connection.row_factory = sqlite3.Row

            cursor = connection.cursor()

            cursor.execute(
                "PRAGMA foreign_keys = ON"
            )

            cursor.execute(
                "PRAGMA journal_mode = WAL"
            )

            cursor.execute(
                "PRAGMA synchronous = NORMAL"
            )


    # ========================================================
    # GUILDS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guilds (

            guild_id INTEGER PRIMARY KEY,

            language TEXT DEFAULT 'ar',

            currency_name TEXT DEFAULT 'Coins',

            currency_symbol TEXT DEFAULT '🪙',

            message_channel INTEGER DEFAULT NULL,

            task_channel INTEGER DEFAULT NULL,

            log_channel INTEGER DEFAULT NULL,

            notification_channel INTEGER DEFAULT NULL,

            daily_enabled INTEGER DEFAULT 1,

            weekly_enabled INTEGER DEFAULT 1,

            monthly_enabled INTEGER DEFAULT 0,

            xp_enabled INTEGER DEFAULT 1,

            reminders_enabled INTEGER DEFAULT 1,

            level_up_enabled INTEGER DEFAULT 1,

            level_up_mention INTEGER DEFAULT 1,

            level_up_message TEXT DEFAULT NULL,

            reminder_minutes INTEGER DEFAULT 60,

            created_at TEXT

        )
    """)


    # ========================================================
    # USERS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            guild_id INTEGER,

            user_id INTEGER,

            coins INTEGER DEFAULT 0,

            xp INTEGER DEFAULT 0,

            level INTEGER DEFAULT 1,

            messages INTEGER DEFAULT 0,

            images INTEGER DEFAULT 0,

            invites INTEGER DEFAULT 0,

            voice_seconds INTEGER DEFAULT 0,

            afk_seconds INTEGER DEFAULT 0,

            last_message TEXT,

            last_voice TEXT,

            last_xp_message TEXT,

            nickname_changes INTEGER DEFAULT 0,

            created_at TEXT,

            PRIMARY KEY (
                guild_id,
                user_id
            )

        )
    """)


    # ========================================================
    # TASK PROGRESS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_progress (

            guild_id INTEGER,

            user_id INTEGER,

            task_id TEXT,

            progress INTEGER DEFAULT 0,

            period TEXT,

            updated_at TEXT,

            PRIMARY KEY (
                guild_id,
                user_id,
                task_id,
                period
            )

        )
    """)


    # ========================================================
    # COMPLETED TASKS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS completed_tasks (

            guild_id INTEGER,

            user_id INTEGER,

            task_id TEXT,

            period TEXT,

            reward INTEGER DEFAULT 0,

            completed_at TEXT,

            PRIMARY KEY (
                guild_id,
                user_id,
                task_id,
                period
            )

        )
    """)


    # ========================================================
    # ACTIVE TASKS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_tasks (

            guild_id INTEGER,

            user_id INTEGER,

            period TEXT,

            task_index INTEGER DEFAULT 0,

            started_at TEXT,

            PRIMARY KEY (
                guild_id,
                user_id,
                period
            )

        )
    """)


    # ========================================================
    # CUSTOM CURRENCIES
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS currencies (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            guild_id INTEGER,

            name TEXT,

            symbol TEXT,

            coins_required INTEGER,

            external_amount INTEGER,

            enabled INTEGER DEFAULT 1,

            created_at TEXT,

            UNIQUE (
                guild_id,
                name
            )

        )
    """)


    # ========================================================
    # EXCHANGE LOG
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exchanges (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            guild_id INTEGER,

            user_id INTEGER,

            currency_id INTEGER,

            coins_spent INTEGER,

            external_amount INTEGER,

            created_at TEXT

        )
    """)


    # ========================================================
    # REMINDERS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            guild_id INTEGER,

            user_id INTEGER,

            task_id TEXT,

            period TEXT,

            enabled INTEGER DEFAULT 1,

            last_sent TEXT

        )
    """)


    # ========================================================
    # VOICE SESSIONS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voice_sessions (

            guild_id INTEGER,

            user_id INTEGER,

            channel_id INTEGER DEFAULT NULL,

            joined_at TEXT,

            last_update TEXT,

            is_afk INTEGER DEFAULT 0,

            afk_started_at TEXT,

            PRIMARY KEY (
                guild_id,
                user_id
            )

        )
    """)


    # ========================================================
    # INVITE CACHE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invite_cache (

            guild_id INTEGER,

            invite_code TEXT,

            uses INTEGER DEFAULT 0,

            inviter_id INTEGER DEFAULT NULL,

            created_at TEXT,

            updated_at TEXT,

            PRIMARY KEY (
                guild_id,
                invite_code
            )

        )
    """)


    # ========================================================
    # DATABASE MIGRATIONS
    # ========================================================

    add_column_if_missing(
        "guilds",
        "task_channel",
        "INTEGER DEFAULT NULL"
    )

    add_column_if_missing(
        "guilds",
        "log_channel",
        "INTEGER DEFAULT NULL"
    )

    add_column_if_missing(
        "guilds",
        "notification_channel",
        "INTEGER DEFAULT NULL"
    )

    add_column_if_missing(
        "guilds",
        "log_channel",
        "INTEGER DEFAULT NULL"
    )

    add_column_if_missing(
        "guilds",
        "daily_enabled",
        "INTEGER DEFAULT 1"
    )

    add_column_if_missing(
        "guilds",
        "weekly_enabled",
        "INTEGER DEFAULT 1"
    )

    add_column_if_missing(
        "guilds",
        "monthly_enabled",
        "INTEGER DEFAULT 0"
    )

    add_column_if_missing(
        "guilds",
        "xp_enabled",
        "INTEGER DEFAULT 1"
    )

    add_column_if_missing(
        "guilds",
        "reminders_enabled",
        "INTEGER DEFAULT 1"
    )

    add_column_if_missing(
        "guilds",
        "level_up_enabled",
        "INTEGER DEFAULT 1"
    )

    add_column_if_missing(
        "guilds",
        "level_up_mention",
        "INTEGER DEFAULT 1"
    )

    add_column_if_missing(
        "guilds",
        "level_up_message",
        "TEXT DEFAULT NULL"
    )

    add_column_if_missing(
        "guilds",
        "reminder_minutes",
        "INTEGER DEFAULT 60"
    )

    add_column_if_missing(
        "users",
        "last_xp_message",
        "TEXT"
    )

    add_column_if_missing(
        "users",
        "created_at",
        "TEXT"
    )

    add_column_if_missing(
        "users",
        "nickname_changes",
        "INTEGER DEFAULT 0"
    )

    add_column_if_missing(
        "currencies",
        "enabled",
        "INTEGER DEFAULT 1"
    )

    add_column_if_missing(
        "currencies",
        "created_at",
        "TEXT"
    )

    add_column_if_missing(
        "users",
        "last_voice",
        "TEXT"
    )

    add_column_if_missing(
        "completed_tasks",
        "reward",
        "INTEGER DEFAULT 0"
    )


    # ========================================================
    # DEFAULT VALUES
    # ========================================================

    cursor.execute("""
        UPDATE guilds

        SET language = ?

        WHERE language IS NULL
        OR language = ''
    """, (
        DEFAULT_LANGUAGE,
    ))


    cursor.execute("""
        UPDATE guilds

        SET currency_name = ?

        WHERE currency_name IS NULL
        OR currency_name = ''
    """, (
        DEFAULT_CURRENCY,
    ))


    cursor.execute("""
        UPDATE guilds

        SET currency_symbol = ?

        WHERE currency_symbol IS NULL
        OR currency_symbol = ''
    """, (
        DEFAULT_CURRENCY_SYMBOL,
    ))


    cursor.execute("""
        UPDATE guilds

        SET xp_enabled = ?

        WHERE xp_enabled IS NULL
    """, (
        int(
            DEFAULT_XP_ENABLED
        ),
    ))


    cursor.execute("""
        UPDATE guilds

        SET reminders_enabled = ?

        WHERE reminders_enabled IS NULL
    """, (
        int(
            DEFAULT_REMINDERS_ENABLED
        ),
    ))


    cursor.execute("""
        UPDATE guilds

        SET daily_enabled = ?

        WHERE daily_enabled IS NULL
    """, (
        int(
            DEFAULT_DAILY_ENABLED
        ),
    ))


    cursor.execute("""
        UPDATE guilds

        SET weekly_enabled = ?

        WHERE weekly_enabled IS NULL
    """, (
        int(
            DEFAULT_WEEKLY_ENABLED
        ),
    ))


    cursor.execute("""
        UPDATE guilds

        SET monthly_enabled = ?

        WHERE monthly_enabled IS NULL
    """, (
        int(
            DEFAULT_MONTHLY_ENABLED
        ),
    ))


    cursor.execute("""
        UPDATE guilds

        SET level_up_enabled = ?

        WHERE level_up_enabled IS NULL
    """, (
        int(
            DEFAULT_LEVEL_UP_ENABLED
        ),
    ))


    cursor.execute("""
        UPDATE guilds

        SET level_up_mention = ?

        WHERE level_up_mention IS NULL
    """, (
        int(
            DEFAULT_LEVEL_UP_MENTION
        ),
    ))


    cursor.execute("""
        UPDATE guilds

        SET level_up_message = ?

        WHERE level_up_message IS NULL
        OR level_up_message = ''
    """, (
        DEFAULT_LEVEL_UP_MESSAGE,
    ))


    cursor.execute("""
        UPDATE guilds

        SET reminder_minutes = 60

        WHERE reminder_minutes IS NULL
        OR reminder_minutes <= 0
    """)


    connection.commit()


# ============================================================
# GUILD SETTINGS
# ============================================================

def create_guild(
    guild_id
):

    cursor.execute("""
        INSERT OR IGNORE INTO guilds (

            guild_id,

            language,

            currency_name,

            currency_symbol,

            daily_enabled,

            weekly_enabled,

            monthly_enabled,

            xp_enabled,

            reminders_enabled,

            level_up_enabled,

            level_up_mention,

            level_up_message,

            reminder_minutes,

            created_at

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        guild_id,

        DEFAULT_LANGUAGE,

        DEFAULT_CURRENCY,

        DEFAULT_CURRENCY_SYMBOL,

        int(
            DEFAULT_DAILY_ENABLED
        ),

        int(
            DEFAULT_WEEKLY_ENABLED
        ),

        int(
            DEFAULT_MONTHLY_ENABLED
        ),

        int(
            DEFAULT_XP_ENABLED
        ),

        int(
            DEFAULT_REMINDERS_ENABLED
        ),

        int(
            DEFAULT_LEVEL_UP_ENABLED
        ),

        int(
            DEFAULT_LEVEL_UP_MENTION
        ),

        DEFAULT_LEVEL_UP_MESSAGE,

        60,

        now()
    ))

    connection.commit()


def get_guild(
    guild_id
):

    create_guild(
        guild_id
    )

    cursor.execute("""
        SELECT *

        FROM guilds

        WHERE guild_id = ?
    """, (
        guild_id,
    ))

    return cursor.fetchone()


def update_guild_setting(
    guild_id,
    setting,
    value
):

    allowed = {

        "language",

        "currency_name",

        "currency_symbol",

        "message_channel",

        "task_channel",

        "log_channel",

        "notification_channel",

        "daily_enabled",

        "weekly_enabled",

        "monthly_enabled",

        "xp_enabled",

        "reminders_enabled",

        "level_up_enabled",

        "level_up_mention",

        "level_up_message",

        "reminder_minutes"

    }


    if setting not in allowed:

        raise ValueError(
            "Invalid guild setting."
        )


    create_guild(
        guild_id
    )


    query = f"""
        UPDATE guilds

        SET {setting} = ?

        WHERE guild_id = ?
    """


    cursor.execute(
        query,
        (
            value,

            guild_id
        )
    )


    connection.commit()


def get_guild_setting(
    guild_id,
    setting
):

    allowed = {

        "language",

        "currency_name",

        "currency_symbol",

        "message_channel",

        "task_channel",

        "log_channel",

        "notification_channel",

        "daily_enabled",

        "weekly_enabled",

        "monthly_enabled",

        "xp_enabled",

        "reminders_enabled",

        "level_up_enabled",

        "level_up_mention",

        "level_up_message",

        "reminder_minutes"

    }


    if setting not in allowed:

        raise ValueError(
            "Invalid guild setting."
        )


    guild = get_guild(
        guild_id
    )


    return guild[setting]


# ============================================================
# USERS
# ============================================================

def create_user(
    guild_id,
    user_id
):

    cursor.execute("""
        INSERT OR IGNORE INTO users (

            guild_id,

            user_id,

            created_at

        )

        VALUES (?, ?, ?)
    """, (
        guild_id,

        user_id,

        now()
    ))


    connection.commit()


def get_user(
    guild_id,
    user_id
):

    create_user(
        guild_id,

        user_id
    )


    cursor.execute("""
        SELECT *

        FROM users

        WHERE guild_id = ?

        AND user_id = ?
    """, (
        guild_id,

        user_id
    ))


    return cursor.fetchone()


# ============================================================
# COINS
# ============================================================

def add_coins(
    guild_id,
    user_id,
    amount
):

    create_user(
        guild_id,

        user_id
    )


    cursor.execute("""
        UPDATE users

        SET coins = coins + ?

        WHERE guild_id = ?

        AND user_id = ?
    """, (
        amount,

        guild_id,

        user_id
    ))


    connection.commit()


def remove_coins(
    guild_id,
    user_id,
    amount
):

    user = get_user(
        guild_id,

        user_id
    )


    if amount < 0:

        return False


    if user["coins"] < amount:

        return False


    cursor.execute("""
        UPDATE users

        SET coins = coins - ?

        WHERE guild_id = ?

        AND user_id = ?
    """, (
        amount,

        guild_id,

        user_id
    ))


    connection.commit()


    return True


def get_balance(
    guild_id,
    user_id
):

    user = get_user(
        guild_id,

        user_id
    )


    return user["coins"]


# ============================================================
# XP
# ============================================================

def required_xp(
    level
):

    if level <= 1:

        return 0


    total = 0


    for current_level in range(
        1,

        level
    ):

        total += int(
            100 *
            (
                1.35 **
                (
                    current_level - 1
                )
            )
        )


    return total


def calculate_level(
    xp
):

    if xp < 0:

        xp = 0


    level = 1


    while True:

        next_level = (
            level + 1
        )


        required = required_xp(
            next_level
        )


        if xp < required:

            break


        level = next_level


    return level


def add_xp(
    guild_id,
    user_id,
    amount
):

    if amount <= 0:

        user = get_user(
            guild_id,

            user_id
        )

        return (
            user["level"],

            user["level"]
        )


    user = get_user(
        guild_id,

        user_id
    )


    old_level = user["level"]


    new_xp = (
        user["xp"] +
        amount
    )


    new_level = calculate_level(
        new_xp
    )


    cursor.execute("""
        UPDATE users

        SET xp = ?,

            level = ?

        WHERE guild_id = ?

        AND user_id = ?
    """, (
        new_xp,

        new_level,

        guild_id,

        user_id
    ))


    connection.commit()


    return (
        old_level,

        new_level
    )


def get_level_progress(
    guild_id,
    user_id
):

    user = get_user(
        guild_id,

        user_id
    )


    level = user["level"]

    current_required = required_xp(
        level
    )

    next_required = required_xp(
        level + 1
    )


    progress = (
        user["xp"] -
        current_required
    )


    required = (
        next_required -
        current_required
    )


    if required <= 0:

        percentage = 100

    else:

        percentage = int(
            (
                progress /
                required
            ) *
            100
        )


    percentage = max(
        0,

        min(
            100,

            percentage
        )
    )


    return {
        "level": level,

        "xp": user["xp"],

        "progress": progress,

        "required": required,

        "percentage": percentage
    }


# ============================================================
# MESSAGE STATISTICS
# ============================================================

def add_message(
    guild_id,
    user_id
):

    create_user(
        guild_id,

        user_id
    )


    cursor.execute("""
        UPDATE users

        SET messages = messages + 1,

            last_message = ?

        WHERE guild_id = ?

        AND user_id = ?
    """, (
        now(),

        guild_id,

        user_id
    ))


    connection.commit()


def add_image(
    guild_id,
    user_id
):

    create_user(
        guild_id,

        user_id
    )


    cursor.execute("""
        UPDATE users

        SET images = images + 1

        WHERE guild_id = ?

        AND user_id = ?
    """, (
        guild_id,

        user_id
    ))


    connection.commit()


def add_invite(
    guild_id,
    user_id,
    amount=1
):

    create_user(
        guild_id,

        user_id
    )


    cursor.execute("""
        UPDATE users

        SET invites = invites + ?

        WHERE guild_id = ?

        AND user_id = ?
    """, (
        amount,

        guild_id,

        user_id
    ))


    connection.commit()


def add_nickname_change(
    guild_id,
    user_id
):

    create_user(
        guild_id,

        user_id
    )


    cursor.execute("""
        UPDATE users

        SET nickname_changes =
            nickname_changes + 1

        WHERE guild_id = ?

        AND user_id = ?
    """, (
        guild_id,

        user_id
    ))


    connection.commit()


# ============================================================
# VOICE
# ============================================================

def add_voice_time(
    guild_id,
    user_id,
    seconds
):

    if seconds <= 0:

        return


    create_user(
        guild_id,

        user_id
    )


    cursor.execute("""
        UPDATE users

        SET voice_seconds =
            voice_seconds + ?,

            last_voice = ?

        WHERE guild_id = ?

        AND user_id = ?
    """, (
        seconds,

        now(),

        guild_id,

        user_id
    ))


    connection.commit()


def add_afk_time(
    guild_id,
    user_id,
    seconds
):

    if seconds <= 0:

        return


    create_user(
        guild_id,

        user_id
    )


    cursor.execute("""
        UPDATE users

        SET afk_seconds =
            afk_seconds + ?

        WHERE guild_id = ?

        AND user_id = ?
    """, (
        seconds,

        guild_id,

        user_id
    ))


    connection.commit()


def get_voice_seconds(
    guild_id,
    user_id
):

    user = get_user(
        guild_id,

        user_id
    )


    return user["voice_seconds"]


def get_afk_seconds(
    guild_id,
    user_id
):

    user = get_user(
        guild_id,

        user_id
    )


    return user["afk_seconds"]


# ============================================================
# VOICE SESSIONS
# ============================================================

def create_voice_session(
    guild_id,
    user_id,
    channel_id=None,
    is_afk=False
):

    timestamp = now()


    cursor.execute("""
        INSERT INTO voice_sessions (

            guild_id,

            user_id,

            channel_id,

            joined_at,

            last_update,

            is_afk,

            afk_started_at

        )

        VALUES (?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT (
            guild_id,
            user_id
        )

        DO UPDATE SET

            channel_id = excluded.channel_id,

            last_update = excluded.last_update,

            is_afk = excluded.is_afk,

            afk_started_at =
                excluded.afk_started_at
    """, (
        guild_id,

        user_id,

        channel_id,

        timestamp,

        timestamp,

        int(is_afk),

        timestamp if is_afk else None
    ))


    connection.commit()


def get_voice_session(
    guild_id,
    user_id
):

    cursor.execute("""
        SELECT *

        FROM voice_sessions

        WHERE guild_id = ?

        AND user_id = ?
    """, (
        guild_id,

        user_id
    ))


    return cursor.fetchone()


def update_voice_session(
    guild_id,
    user_id,
    channel_id=None,
    is_afk=False,
    afk_started_at=None
):

    create_voice_session(
        guild_id,

        user_id,

        channel_id,

        is_afk
    )


    cursor.execute("""
        UPDATE voice_sessions

        SET channel_id = ?,

            last_update = ?,

            is_afk = ?,

            afk_started_at = ?

        WHERE guild_id = ?

        AND user_id = ?
    """, (
        channel_id,

        now(),

        int(is_afk),

        afk_started_at,

        guild_id,

        user_id
    ))


    connection.commit()


def delete_voice_session(
    guild_id,
    user_id
):

    cursor.execute("""
        DELETE FROM voice_sessions

        WHERE guild_id = ?

        AND user_id = ?
    """, (
        guild_id,

        user_id
    ))


    connection.commit()


# ============================================================
# TASK PROGRESS
# ============================================================

def get_task_progress(
    guild_id,
    user_id,
    task_id,
    period
):

    cursor.execute("""
        SELECT *

        FROM task_progress

        WHERE guild_id = ?

        AND user_id = ?

        AND task_id = ?

        AND period = ?
    """, (
        guild_id,

        user_id,

        task_id,

        period
    ))


    row = cursor.fetchone()


    if row:

        return row["progress"]


    return 0


def set_task_progress(
    guild_id,
    user_id,
    task_id,
    period,
    progress
):

    if progress < 0:

        progress = 0


    cursor.execute("""
        INSERT INTO task_progress (

            guild_id,

            user_id,

            task_id,

            progress,

            period,

            updated_at

        )

        VALUES (?, ?, ?, ?, ?, ?)

        ON CONFLICT (
            guild_id,
            user_id,
            task_id,
            period
        )

        DO UPDATE SET

            progress =
                excluded.progress,

            updated_at =
                excluded.updated_at

    """, (
        guild_id,

        user_id,

        task_id,

        progress,

        period,

        now()
    ))


    connection.commit()


def increase_task_progress(
    guild_id,
    user_id,
    task_id,
    period,
    amount=1
):

    current = get_task_progress(
        guild_id,

        user_id,

        task_id,

        period
    )


    new_progress = (
        current +
        amount
    )


    set_task_progress(
        guild_id,

        user_id,

        task_id,

        period,

        new_progress
    )


    return new_progress


# ============================================================
# ACTIVE TASKS
# ============================================================

def get_active_task_index(
    guild_id,
    user_id,
    period
):

    cursor.execute("""
        SELECT task_index

        FROM active_tasks

        WHERE guild_id = ?

        AND user_id = ?

        AND period = ?
    """, (
        guild_id,

        user_id,

        period
    ))


    row = cursor.fetchone()


    if not row:

        cursor.execute("""
            INSERT INTO active_tasks (

                guild_id,

                user_id,

                period,

                task_index,

                started_at

            )

            VALUES (?, ?, ?, 0, ?)
        """, (
            guild_id,

            user_id,

            period,

            now()
        ))


        connection.commit()


        return 0


    return row["task_index"]


def set_active_task_index(
    guild_id,
    user_id,
    period,
    task_index
):

    cursor.execute("""
        INSERT INTO active_tasks (

            guild_id,

            user_id,

            period,

            task_index,

            started_at

        )

        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT (
            guild_id,
            user_id,
            period
        )

        DO UPDATE SET

            task_index =
                excluded.task_index,

            started_at =
                excluded.started_at
    """, (
        guild_id,

        user_id,

        period,

        task_index,

        now()
    ))


    connection.commit()


def get_active_task_state(
    guild_id,
    user_id,
    period
):

    cursor.execute("""
        SELECT *

        FROM active_tasks

        WHERE guild_id = ?

        AND user_id = ?

        AND period = ?
    """, (
        guild_id,

        user_id,

        period
    ))


    return cursor.fetchone()


def reset_active_task(
    guild_id,
    user_id,
    period
):

    cursor.execute("""
        DELETE FROM active_tasks

        WHERE guild_id = ?

        AND user_id = ?

        AND period = ?
    """, (
        guild_id,

        user_id,

        period
    ))


    connection.commit()


# Backwards-compatible task-state helpers used by tasks.py.  The database
# schema stores the active position as `task_index`; the task module used the
# older `current_index` name.
def get_task_state(
    guild_id,
    user_id,
    period
):

    index = get_active_task_index(
        guild_id,
        user_id,
        period
    )

    return {
        "current_index": index,
        "task_index": index,
    }


def set_task_index(
    guild_id,
    user_id,
    period,
    task_index
):

    set_active_task_index(
        guild_id,
        user_id,
        period,
        task_index
    )


def advance_task_index(
    guild_id,
    user_id,
    period
):

    next_index = get_active_task_index(
        guild_id,
        user_id,
        period
    ) + 1

    set_active_task_index(
        guild_id,
        user_id,
        period,
        next_index
    )

    return next_index


def get_period_stats(
    guild_id,
    user_id,
    period
):
    """Return the tracked user stats consumed by the task progress helpers."""

    return get_user(
        guild_id,
        user_id
    )


# ============================================================
# COMPLETED TASKS
# ============================================================

def is_task_completed(
    guild_id,
    user_id,
    task_id,
    period
):

    cursor.execute("""
        SELECT 1

        FROM completed_tasks

        WHERE guild_id = ?

        AND user_id = ?

        AND task_id = ?

        AND period = ?
    """, (
        guild_id,

        user_id,

        task_id,

        period
    ))


    return (
        cursor.fetchone()
        is not None
    )


def complete_task(
    guild_id,
    user_id,
    task_id,
    period,
    reward
):

    if is_task_completed(
        guild_id,

        user_id,

        task_id,

        period
    ):

        return False


    create_user(
        guild_id,

        user_id
    )


    cursor.execute("""
        INSERT INTO completed_tasks (

            guild_id,

            user_id,

            task_id,

            period,

            reward,

            completed_at

        )

        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        guild_id,

        user_id,

        task_id,

        period,

        reward,

        now()
    ))


    cursor.execute("""
        UPDATE users

        SET coins = coins + ?

        WHERE guild_id = ?

        AND user_id = ?
    """, (
        reward,

        guild_id,

        user_id
    ))


    connection.commit()


    return True


# ============================================================
# CUSTOM CURRENCIES
# ============================================================

def add_currency(
    guild_id,
    name,
    symbol,
    coins_required,
    external_amount
):

    try:

        cursor.execute("""
            INSERT INTO currencies (

                guild_id,

                name,

                symbol,

                coins_required,

                external_amount,

                enabled,

                created_at

            )

            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (
            guild_id,

            name,

            symbol,

            coins_required,

            external_amount,

            now()
        ))


        connection.commit()


        return True


    except sqlite3.IntegrityError:

        return False


def update_currency(
    guild_id,
    currency_id,
    name=None,
    symbol=None,
    coins_required=None,
    external_amount=None,
    enabled=None
):

    currency = get_currency(
        guild_id,

        currency_id,

        include_disabled=True
    )


    if not currency:

        return False


    values = []

    updates = []


    if name is not None:

        updates.append(
            "name = ?"
        )

        values.append(
            name
        )


    if symbol is not None:

        updates.append(
            "symbol = ?"
        )

        values.append(
            symbol
        )


    if coins_required is not None:

        updates.append(
            "coins_required = ?"
        )

        values.append(
            coins_required
        )


    if external_amount is not None:

        updates.append(
            "external_amount = ?"
        )

        values.append(
            external_amount
        )


    if enabled is not None:

        updates.append(
            "enabled = ?"
        )

        values.append(
            int(enabled)
        )


    if not updates:

        return True


    values.extend([
        guild_id,

        currency_id
    ])


    cursor.execute(
        f"""
        UPDATE currencies

        SET {", ".join(updates)}

        WHERE guild_id = ?

        AND id = ?
        """,
        tuple(values)
    )


    connection.commit()


    return True


def get_currencies(
    guild_id,
    include_disabled=False
):

    if include_disabled:

        cursor.execute("""
            SELECT *

            FROM currencies

            WHERE guild_id = ?

            ORDER BY id ASC
        """, (
            guild_id,
        ))

    else:

        cursor.execute("""
            SELECT *

            FROM currencies

            WHERE guild_id = ?

            AND enabled = 1

            ORDER BY id ASC
        """, (
            guild_id,
        ))


    return cursor.fetchall()


def get_currency(
    guild_id,
    currency_id,
    include_disabled=False
):

    if include_disabled:

        cursor.execute("""
            SELECT *

            FROM currencies

            WHERE guild_id = ?

            AND id = ?
        """, (
            guild_id,

            currency_id
        ))

    else:

        cursor.execute("""
            SELECT *

            FROM currencies

            WHERE guild_id = ?

            AND id = ?

            AND enabled = 1
        """, (
            guild_id,

            currency_id
        ))


    return cursor.fetchone()


# ============================================================
# EXCHANGE
# ============================================================

def exchange_coins(
    guild_id,
    user_id,
    currency_id
):

    currency = get_currency(
        guild_id,

        currency_id
    )


    if not currency:

        return (
            False,

            "currency_not_found"
        )


    user = get_user(
        guild_id,

        user_id
    )


    required = currency[
        "coins_required"
    ]


    if user["coins"] < required:

        return (
            False,

            "not_enough_coins"
        )


    cursor.execute("""
        UPDATE users

        SET coins = coins - ?

        WHERE guild_id = ?

        AND user_id = ?
    """, (
        required,

        guild_id,

        user_id
    ))


    cursor.execute("""
        INSERT INTO exchanges (

            guild_id,

            user_id,

            currency_id,

            coins_spent,

            external_amount,

            created_at

        )

        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        guild_id,

        user_id,

        currency_id,

        required,

        currency[
            "external_amount"
        ],

        now()
    ))


    connection.commit()


    return (
        True,

        currency[
            "external_amount"
        ]
    )


# ============================================================
# EXCHANGE HISTORY
# ============================================================

def get_exchange_history(
    guild_id,
    user_id,
    limit=10
):

    cursor.execute("""
        SELECT *

        FROM exchanges

        WHERE guild_id = ?

        AND user_id = ?

        ORDER BY id DESC

        LIMIT ?
    """, (
        guild_id,

        user_id,

        limit
    ))


    return cursor.fetchall()


# ============================================================
# REMINDERS
# ============================================================

def create_reminder(
    guild_id,
    user_id,
    task_id,
    period,
    enabled=True
):

    cursor.execute("""
        INSERT INTO reminders (

            guild_id,

            user_id,

            task_id,

            period,

            enabled,

            last_sent

        )

        VALUES (?, ?, ?, ?, ?, NULL)

        ON CONFLICT DO NOTHING
    """, (
        guild_id,

        user_id,

        task_id,

        period,

        int(enabled)
    ))


    connection.commit()


def get_reminder(
    guild_id,
    user_id,
    task_id,
    period
):

    cursor.execute("""
        SELECT *

        FROM reminders

        WHERE guild_id = ?

        AND user_id = ?

        AND task_id = ?

        AND period = ?
    """, (
        guild_id,

        user_id,

        task_id,

        period
    ))


    return cursor.fetchone()


def set_reminder_enabled(
    guild_id,
    user_id,
    task_id,
    period,
    enabled
):

    reminder = get_reminder(
        guild_id,

        user_id,

        task_id,

        period
    )


    if reminder:

        cursor.execute("""
            UPDATE reminders

            SET enabled = ?

            WHERE guild_id = ?

            AND user_id = ?

            AND task_id = ?

            AND period = ?
        """, (
            int(enabled),

            guild_id,

            user_id,

            task_id,

            period
        ))

    else:

        create_reminder(
            guild_id,

            user_id,

            task_id,

            period,

            enabled
        )


    connection.commit()


def update_reminder_sent(
    guild_id,
    user_id,
    task_id,
    period
):

    reminder = get_reminder(
        guild_id,

        user_id,

        task_id,

        period
    )


    if reminder:

        cursor.execute("""
            UPDATE reminders

            SET last_sent = ?

            WHERE guild_id = ?

            AND user_id = ?

            AND task_id = ?

            AND period = ?
        """, (
            now(),

            guild_id,

            user_id,

            task_id,

            period
        ))

    else:

        create_reminder(
            guild_id,

            user_id,

            task_id,

            period,

            True
        )

        cursor.execute("""
            UPDATE reminders

            SET last_sent = ?

            WHERE guild_id = ?

            AND user_id = ?

            AND task_id = ?

            AND period = ?
        """, (
            now(),

            guild_id,

            user_id,

            task_id,

            period
        ))


    connection.commit()


def get_user_reminders(
    guild_id,
    user_id
):

    cursor.execute("""
        SELECT *

        FROM reminders

        WHERE guild_id = ?

        AND user_id = ?

        ORDER BY id ASC
    """, (
        guild_id,

        user_id
    ))


    return cursor.fetchall()


# ============================================================
# INVITE CACHE
# ============================================================

def save_invite(
    guild_id,
    invite_code,
    uses,
    inviter_id=None
):

    cursor.execute("""
        INSERT INTO invite_cache (

            guild_id,

            invite_code,

            uses,

            inviter_id,

            created_at,

            updated_at

        )

        VALUES (?, ?, ?, ?, ?, ?)

        ON CONFLICT (
            guild_id,
            invite_code
        )

        DO UPDATE SET

            uses = excluded.uses,

            inviter_id =
                excluded.inviter_id,

            updated_at =
                excluded.updated_at
    """, (
        guild_id,

        invite_code,

        uses,

        inviter_id,

        now(),

        now()
    ))


    connection.commit()


def get_invite(
    guild_id,
    invite_code
):

    cursor.execute("""
        SELECT *

        FROM invite_cache

        WHERE guild_id = ?

        AND invite_code = ?
    """, (
        guild_id,

        invite_code
    ))


    return cursor.fetchone()


def get_guild_invites(
    guild_id
):

    cursor.execute("""
        SELECT *

        FROM invite_cache

        WHERE guild_id = ?

        ORDER BY invite_code ASC
    """, (
        guild_id,
    ))


    return cursor.fetchall()


def delete_invite(
    guild_id,
    invite_code
):

    cursor.execute("""
        DELETE FROM invite_cache

        WHERE guild_id = ?

        AND invite_code = ?
    """, (
        guild_id,

        invite_code
    ))


    connection.commit()


# ============================================================
# LEADERBOARD
# ============================================================

def get_top_users(
    guild_id,
    limit=10
):

    if limit <= 0:

        limit = 10


    cursor.execute("""
        SELECT *

        FROM users

        WHERE guild_id = ?

        ORDER BY coins DESC,

                 xp DESC

        LIMIT ?
    """, (
        guild_id,

        limit
    ))


    return cursor.fetchall()


# ============================================================
# USER RANK
# ============================================================

def get_user_rank(
    guild_id,
    user_id
):

    user = get_user(
        guild_id,

        user_id
    )


    cursor.execute("""
        SELECT COUNT(*) + 1 AS rank

        FROM users

        WHERE guild_id = ?

        AND (

            coins > ?

            OR (

                coins = ?

                AND xp > ?

            )

        )
    """, (
        guild_id,

        user["coins"],

        user["coins"],

        user["xp"]
    ))


    row = cursor.fetchone()


    return row["rank"]


# ============================================================
# PERIOD RESET
# ============================================================

def reset_period(
    guild_id,
    period
):

    cursor.execute("""
        DELETE FROM task_progress

        WHERE guild_id = ?

        AND period = ?
    """, (
        guild_id,

        period
    ))


    cursor.execute("""
        DELETE FROM completed_tasks

        WHERE guild_id = ?

        AND period = ?
    """, (
        guild_id,

        period
    ))


    cursor.execute("""
        DELETE FROM active_tasks

        WHERE guild_id = ?

        AND period = ?
    """, (
        guild_id,

        period
    ))


    cursor.execute("""
        DELETE FROM reminders

        WHERE guild_id = ?

        AND period = ?
    """, (
        guild_id,

        period
    ))


    connection.commit()


# ============================================================
# RESET USER TASK STATE
# ============================================================

def reset_user_task_state(
    guild_id,
    user_id,
    period
):

    cursor.execute("""
        DELETE FROM task_progress

        WHERE guild_id = ?

        AND user_id = ?

        AND period = ?
    """, (
        guild_id,

        user_id,

        period
    ))


    cursor.execute("""
        DELETE FROM completed_tasks

        WHERE guild_id = ?

        AND user_id = ?

        AND period = ?
    """, (
        guild_id,

        user_id,

        period
    ))


    cursor.execute("""
        DELETE FROM active_tasks

        WHERE guild_id = ?

        AND user_id = ?

        AND period = ?
    """, (
        guild_id,

        user_id,

        period
    ))


    connection.commit()


# ============================================================
# DATABASE STATISTICS
# ============================================================

def get_guild_user_count(
    guild_id
):

    cursor.execute("""
        SELECT COUNT(*) AS count

        FROM users

        WHERE guild_id = ?
    """, (
        guild_id,
    ))


    row = cursor.fetchone()


    return row["count"]


def get_guild_task_completion_count(
    guild_id,
    period=None
):

    if period:

        cursor.execute("""
            SELECT COUNT(*) AS count

            FROM completed_tasks

            WHERE guild_id = ?

            AND period = ?
        """, (
            guild_id,

            period
        ))

    else:

        cursor.execute("""
            SELECT COUNT(*) AS count

            FROM completed_tasks

            WHERE guild_id = ?
        """, (
            guild_id,
        ))


    row = cursor.fetchone()


    return row["count"]


# ============================================================
# LANGUAGE
# ============================================================

def set_language(
    guild_id,
    language
):

    if language not in (
        "ar",
        "en"
    ):

        return False


    update_guild_setting(
        guild_id,

        "language",

        language
    )


    return True


def get_language(
    guild_id
):

    return get_guild_setting(
        guild_id,

        "language"
    )


# ============================================================
# CURRENCY SETTINGS
# ============================================================

def set_currency(
    guild_id,
    name,
    symbol
):

    if not name:

        return False


    if not symbol:

        return False


    update_guild_setting(
        guild_id,

        "currency_name",

        name
    )


    update_guild_setting(
        guild_id,

        "currency_symbol",

        symbol
    )


    return True


def get_currency_settings(
    guild_id
):

    guild = get_guild(
        guild_id
    )


    return {
        "name": guild["currency_name"],

        "symbol": guild["currency_symbol"]
    }


# ============================================================
# LEVEL UP SETTINGS
# ============================================================

def set_level_up_settings(
    guild_id,
    enabled=None,
    mention=None,
    message=None
):

    create_guild(
        guild_id
    )


    if enabled is not None:

        update_guild_setting(
            guild_id,

            "level_up_enabled",

            int(enabled)
        )


    if mention is not None:

        update_guild_setting(
            guild_id,

            "level_up_mention",

            int(mention)
        )


    if message is not None:

        update_guild_setting(
            guild_id,

            "level_up_message",

            message
        )


    return True


def get_level_up_settings(
    guild_id
):

    guild = get_guild(
        guild_id
    )


    return {
        "enabled":
            bool(
                guild["level_up_enabled"]
            ),

        "mention":
            bool(
                guild["level_up_mention"]
            ),

        "message":
            guild["level_up_message"]
            or DEFAULT_LEVEL_UP_MESSAGE
    }


# ============================================================
# CHANNEL SETTINGS
# ============================================================

def set_task_channel(
    guild_id,
    channel_id
):

    update_guild_setting(
        guild_id,

        "task_channel",

        channel_id
    )


def get_task_channel(
    guild_id
):

    return get_guild_setting(
        guild_id,

        "task_channel"
    )


def set_message_channel(
    guild_id,
    channel_id
):

    update_guild_setting(
        guild_id,

        "message_channel",

        channel_id
    )


def get_message_channel(
    guild_id
):

    return get_guild_setting(
        guild_id,

        "message_channel"
    )


def set_notification_channel(
    guild_id,
    channel_id
):

    update_guild_setting(
        guild_id,

        "notification_channel",

        channel_id
    )


def get_notification_channel(
    guild_id
):

    return get_guild_setting(
        guild_id,

        "notification_channel"
    )


def set_log_channel(
    guild_id,
    channel_id
):

    update_guild_setting(
        guild_id,

        "log_channel",

        channel_id
    )


def get_log_channel(
    guild_id
):

    return get_guild_setting(
        guild_id,

        "log_channel"
    )


# ============================================================
# FEATURE TOGGLES
# ============================================================

def set_feature_enabled(
    guild_id,
    feature,
    enabled
):

    mapping = {

        "daily":
            "daily_enabled",

        "weekly":
            "weekly_enabled",

        "monthly":
            "monthly_enabled",

        "xp":
            "xp_enabled",

        "reminders":
            "reminders_enabled",

        "level_up":
            "level_up_enabled"

    }


    setting = mapping.get(
        feature
    )


    if not setting:

        return False


    update_guild_setting(
        guild_id,

        setting,

        int(enabled)
    )


    return True


def is_feature_enabled(
    guild_id,
    feature
):

    mapping = {

        "daily":
            "daily_enabled",

        "weekly":
            "weekly_enabled",

        "monthly":
            "monthly_enabled",

        "xp":
            "xp_enabled",

        "reminders":
            "reminders_enabled",

        "level_up":
            "level_up_enabled"

    }


    setting = mapping.get(
        feature
    )


    if not setting:

        return False


    return bool(
        get_guild_setting(
            guild_id,

            setting
        )
    )


# ============================================================
# REMINDER SETTINGS
# ============================================================

def set_reminder_minutes(
    guild_id,
    minutes
):

    if minutes < 1:

        minutes = 1


    update_guild_setting(
        guild_id,

        "reminder_minutes",

        minutes
    )


def get_reminder_minutes(
    guild_id
):

    return int(
        get_guild_setting(
            guild_id,

            "reminder_minutes"
        )
    )


# ============================================================
# DATABASE CLOSE
# ============================================================

def close_database():

    try:

        connection.commit()

    except Exception:

        pass


    try:

        connection.close()

    except Exception:

        pass


# ============================================================
# INITIALIZE
# ============================================================

initialize_database()
