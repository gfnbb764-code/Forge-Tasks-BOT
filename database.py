# ============================================================
# TASK BOT — DATABASE.PY
# SQLite Database Manager
# Python 3.11+
# ============================================================

import os
import sqlite3
from datetime import datetime, timezone


# ============================================================
# CONFIG
# ============================================================

DATABASE_FOLDER = "data"
DATABASE_FILE = os.path.join(
    DATABASE_FOLDER,
    "tasks.db"
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

os.makedirs(
    DATABASE_FOLDER,
    exist_ok=True
)


connection = sqlite3.connect(
    DATABASE_FILE,
    check_same_thread=False
)

connection.row_factory = sqlite3.Row

cursor = connection.cursor()


# ============================================================
# TIME
# ============================================================

def now():

    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# TABLES
# ============================================================

def initialize_database():

    # ----------------------------------------
    # GUILDS
    # ----------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guilds (

            guild_id INTEGER PRIMARY KEY,

            language TEXT DEFAULT 'ar',

            currency_name TEXT DEFAULT 'Coins',

            currency_symbol TEXT DEFAULT '🪙',

            message_channel INTEGER DEFAULT NULL,

            task_channel INTEGER DEFAULT NULL,

            log_channel INTEGER DEFAULT NULL,

            daily_enabled INTEGER DEFAULT 1,

            weekly_enabled INTEGER DEFAULT 1,

            monthly_enabled INTEGER DEFAULT 1,

            xp_enabled INTEGER DEFAULT 1,

            reminders_enabled INTEGER DEFAULT 1,

            created_at TEXT

        )
    """)


    # ----------------------------------------
    # USERS
    # ----------------------------------------

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

            created_at TEXT,

            PRIMARY KEY (
                guild_id,
                user_id
            )

        )
    """)


    # ----------------------------------------
    # TASK PROGRESS
    # ----------------------------------------

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


    # ----------------------------------------
    # COMPLETED TASKS
    # ----------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS completed_tasks (

            guild_id INTEGER,

            user_id INTEGER,

            task_id TEXT,

            period TEXT,

            reward INTEGER,

            completed_at TEXT,

            PRIMARY KEY (
                guild_id,
                user_id,
                task_id,
                period
            )

        )
    """)


    # ----------------------------------------
    # CUSTOM CURRENCIES
    # ----------------------------------------

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


    # ----------------------------------------
    # EXCHANGE LOG
    # ----------------------------------------

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


    # ----------------------------------------
    # REMINDERS
    # ----------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            guild_id INTEGER,

            user_id INTEGER,

            task_id TEXT,

            enabled INTEGER DEFAULT 1,

            last_sent TEXT

        )
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

            created_at

        )

        VALUES (?, ?)
    """, (
        guild_id,
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

        "daily_enabled",

        "weekly_enabled",

        "monthly_enabled",

        "xp_enabled",

        "reminders_enabled"

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
                (current_level - 1)
            )
        )

    return total


def calculate_level(
    xp
):

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


# ============================================================
# VOICE
# ============================================================

def add_voice_time(
    guild_id,
    user_id,
    seconds
):

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

            progress = excluded.progress,

            updated_at = excluded.updated_at

    """, (
        guild_id,
        user_id,
        task_id,
        progress,
        period,
        now()
    ))

    connection.commit()


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
# CURRENCIES
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

                created_at

            )

            VALUES (?, ?, ?, ?, ?, ?)
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


def get_currencies(
    guild_id
):

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
    currency_id
):

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

        return False, "currency_not_found"


    user = get_user(
        guild_id,
        user_id
    )

    required = currency[
        "coins_required"
    ]

    if user["coins"] < required:

        return False, "not_enough_coins"


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
        currency["external_amount"],
        now()
    ))


    connection.commit()

    return (
        True,
        currency["external_amount"]
    )


# ============================================================
# LEADERBOARD
# ============================================================

def get_top_users(
    guild_id,
    limit=10
):

    cursor.execute("""
        SELECT *

        FROM users

        WHERE guild_id = ?

        ORDER BY coins DESC

        LIMIT ?
    """, (
        guild_id,
        limit
    ))

    return cursor.fetchall()


# ============================================================
# RESET PERIOD
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


    connection.commit()


# ============================================================
# DATABASE CLOSE
# ============================================================

def close_database():

    connection.close()


# ============================================================
# INITIALIZE
# ============================================================

initialize_database()
