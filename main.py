# ============================================================
# TASK BOT — MAIN.PY
# Forge Tasks BOT
# Discord Tasks / Coins / XP / Levels
# Python 3.11+
# discord.py 2.6+
# ============================================================

from __future__ import annotations

import os
import asyncio
import sqlite3
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv


# ============================================================
# CONFIG
# ============================================================

load_dotenv()


TOKEN = os.getenv("DISCORD_TOKEN")

# When set, slash commands are synchronized to this server immediately.  A
# global synchronization is used otherwise and Discord can take up to an hour
# to make the commands visible.
GUILD_ID = os.getenv("DISCORD_GUILD_ID")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN غير موجود في Environment Variables"
    )


DATABASE = os.getenv(
    "DATABASE_PATH",
    "data/tasks.db"
)


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


XP_ENABLED_DEFAULT = (
    os.getenv(
        "XP_ENABLED",
        "true"
    ).lower()
    == "true"
)


XP_PER_MESSAGE = int(
    os.getenv(
        "XP_PER_MESSAGE",
        "5"
    )
)


XP_PER_IMAGE = int(
    os.getenv(
        "XP_PER_IMAGE",
        "10"
    )
)


XP_PER_VOICE_MINUTE = int(
    os.getenv(
        "XP_PER_VOICE_MINUTE",
        "2"
    )
)


REMINDERS_ENABLED_DEFAULT = (
    os.getenv(
        "REMINDERS_ENABLED",
        "true"
    ).lower()
    == "true"
)


DAILY_TASKS_ENABLED_DEFAULT = (
    os.getenv(
        "DAILY_TASKS_ENABLED",
        "true"
    ).lower()
    == "true"
)


WEEKLY_TASKS_ENABLED_DEFAULT = (
    os.getenv(
        "WEEKLY_TASKS_ENABLED",
        "true"
    ).lower()
    == "true"
)


MONTHLY_TASKS_ENABLED_DEFAULT = (
    os.getenv(
        "MONTHLY_TASKS_ENABLED",
        "false"
    ).lower()
    == "true"
)


LEVEL_UP_ENABLED_DEFAULT = (
    os.getenv(
        "LEVEL_UP_ENABLED",
        "true"
    ).lower()
    == "true"
)


LEVEL_UP_MENTION_DEFAULT = (
    os.getenv(
        "LEVEL_UP_MENTION",
        "true"
    ).lower()
    == "true"
)


LEVEL_UP_MESSAGE_DEFAULT = os.getenv(
    "LEVEL_UP_MESSAGE",
    "🎉 مبروك {mention}! وصلت إلى المستوى {level}!"
)


# ============================================================
# DATABASE DIRECTORY
# ============================================================

os.makedirs(
    os.path.dirname(DATABASE)
    if os.path.dirname(DATABASE)
    else ".",
    exist_ok=True
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

db = sqlite3.connect(
    DATABASE,
    check_same_thread=False
)

db.row_factory = sqlite3.Row

cursor = db.cursor()


# ============================================================
# DATABASE HELPERS
# ============================================================

def now():

    return datetime.now(
        timezone.utc
    )


def add_column_if_missing(
    table,
    column,
    definition
):

    cursor.execute(
        f"PRAGMA table_info({table})"
    )

    columns = [
        row["name"]
        for row in cursor.fetchall()
    ]

    if column not in columns:

        cursor.execute(
            f"""
            ALTER TABLE {table}
            ADD COLUMN {column} {definition}
            """
        )


# ============================================================
# GUILDS TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS guilds (

    guild_id INTEGER PRIMARY KEY,

    language TEXT DEFAULT 'ar',

    currency_name TEXT DEFAULT 'Coins',

    currency_symbol TEXT DEFAULT '🪙',

    message_channel INTEGER DEFAULT NULL,

    task_channel INTEGER DEFAULT NULL,

    notification_channel INTEGER DEFAULT NULL,

    daily_enabled INTEGER DEFAULT 1,

    weekly_enabled INTEGER DEFAULT 1,

    monthly_enabled INTEGER DEFAULT 0,

    xp_enabled INTEGER DEFAULT 1,

    reminders_enabled INTEGER DEFAULT 1,

    level_up_enabled INTEGER DEFAULT 1,

    level_up_mention INTEGER DEFAULT 1,

    level_up_message TEXT DEFAULT NULL,

    created_at TEXT
)
""")


# ============================================================
# USERS TABLE
# ============================================================

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

    last_xp_message TEXT,

    nickname_changes INTEGER DEFAULT 0,

    PRIMARY KEY (
        guild_id,
        user_id
    )
)
""")


# ============================================================
# CURRENCIES TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS currencies (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    guild_id INTEGER,

    name TEXT,

    symbol TEXT,

    coins_required INTEGER,

    external_amount INTEGER,

    UNIQUE(
        guild_id,
        name
    )
)
""")


# ============================================================
# COMPLETED TASKS TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS completed_tasks (

    guild_id INTEGER,

    user_id INTEGER,

    task_id TEXT,

    period TEXT,

    completed_at TEXT,

    PRIMARY KEY (
        guild_id,
        user_id,
        task_id,
        period
    )
)
""")


# ============================================================
# ACTIVE TASKS TABLE
# ============================================================

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


# ============================================================
# TASK PERIOD PROGRESS TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS task_progress (

    guild_id INTEGER,

    user_id INTEGER,

    task_id TEXT,

    period TEXT,

    progress INTEGER DEFAULT 0,

    updated_at TEXT,

    PRIMARY KEY (
        guild_id,
        user_id,
        task_id,
        period
    )
)
""")


# ============================================================
# REMINDERS TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS reminders (

    guild_id INTEGER,

    user_id INTEGER,

    task_id TEXT,

    period TEXT,

    last_sent TEXT,

    PRIMARY KEY (
        guild_id,
        user_id,
        task_id,
        period
    )
)
""")


# ============================================================
# DATABASE MIGRATIONS
# ============================================================

add_column_if_missing(
    "guilds",
    "task_channel",
    "INTEGER DEFAULT NULL"
)

add_column_if_missing(
    "guilds",
    "notification_channel",
    "INTEGER DEFAULT NULL"
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
    "users",
    "last_xp_message",
    "TEXT DEFAULT NULL"
)

add_column_if_missing(
    "users",
    "nickname_changes",
    "INTEGER DEFAULT 0"
)


# ============================================================
# DATABASE DEFAULT VALUES
# ============================================================

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
    int(XP_ENABLED_DEFAULT),
))


cursor.execute("""
UPDATE guilds

SET reminders_enabled = ?

WHERE reminders_enabled IS NULL
""", (
    int(REMINDERS_ENABLED_DEFAULT),
))


cursor.execute("""
UPDATE guilds

SET daily_enabled = ?

WHERE daily_enabled IS NULL
""", (
    int(DAILY_TASKS_ENABLED_DEFAULT),
))


cursor.execute("""
UPDATE guilds

SET weekly_enabled = ?

WHERE weekly_enabled IS NULL
""", (
    int(WEEKLY_TASKS_ENABLED_DEFAULT),
))


cursor.execute("""
UPDATE guilds

SET monthly_enabled = ?

WHERE monthly_enabled IS NULL
""", (
    int(MONTHLY_TASKS_ENABLED_DEFAULT),
))


cursor.execute("""
UPDATE guilds

SET level_up_enabled = ?

WHERE level_up_enabled IS NULL
""", (
    int(LEVEL_UP_ENABLED_DEFAULT),
))


cursor.execute("""
UPDATE guilds

SET level_up_mention = ?

WHERE level_up_mention IS NULL
""", (
    int(LEVEL_UP_MENTION_DEFAULT),
))


cursor.execute("""
UPDATE guilds

SET level_up_message = ?

WHERE level_up_message IS NULL
   OR level_up_message = ''
""", (
    LEVEL_UP_MESSAGE_DEFAULT,
))


db.commit()


# ============================================================
# BOT INTENTS
# ============================================================

intents = discord.Intents.default()

intents.guilds = True

intents.members = True

intents.messages = True

intents.message_content = True

intents.voice_states = True

intents.invites = True


# ============================================================
# BOT
# ============================================================

class TaskBot(commands.Bot):

    def __init__(self):

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):

        if GUILD_ID:

            guild = discord.Object(id=int(GUILD_ID))

            self.tree.copy_global_to(guild=guild)

            synced_commands = await self.tree.sync(guild=guild)

        else:

            synced_commands = await self.tree.sync()

        if not event_manager.voice_loop_task:
            await event_manager.start()
            event_manager.voice_loop_task = asyncio.create_task(event_manager.voice_loop())

        print(
            "========================================"
        )

        print(
            " FORGE TASKS BOT"
        )

        print(
            "========================================"
        )

        print(
            "Bot started successfully."
        )

        print(
            f"Synchronized {len(synced_commands)} slash commands "
            f"({'guild' if GUILD_ID else 'global'} scope)."
        )

        print(
            "Voice / AFK tracker started."
        )

        print(
            "========================================"
        )


bot = TaskBot()


# Register application commands before setup_hook() synchronizes the command
# tree with Discord.  Previously this entry point only synced an empty tree,
# because the command definitions in commands.py were never loaded.
from commands import register_commands, setup_error_handler
from events import register_events

register_commands(bot)
bot.tree.on_error = setup_error_handler
event_manager = register_events(bot)


# ============================================================
# GENERAL HELPERS
# ============================================================

def get_guild(
    guild_id
):

    cursor.execute(
        """
        SELECT *
        FROM guilds
        WHERE guild_id = ?
        """,
        (
            guild_id,
        )
    )

    row = cursor.fetchone()

    if row:

        return row


    cursor.execute(
        """
        INSERT INTO guilds (

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

            created_at

        )

        VALUES (

            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?

        )
        """,
        (
            guild_id,

            DEFAULT_LANGUAGE,

            DEFAULT_CURRENCY,

            DEFAULT_CURRENCY_SYMBOL,

            int(DAILY_TASKS_ENABLED_DEFAULT),

            int(WEEKLY_TASKS_ENABLED_DEFAULT),

            int(MONTHLY_TASKS_ENABLED_DEFAULT),

            int(XP_ENABLED_DEFAULT),

            int(REMINDERS_ENABLED_DEFAULT),

            int(LEVEL_UP_ENABLED_DEFAULT),

            int(LEVEL_UP_MENTION_DEFAULT),

            LEVEL_UP_MESSAGE_DEFAULT,

            now().isoformat()
        )
    )

    db.commit()


    cursor.execute(
        """
        SELECT *
        FROM guilds
        WHERE guild_id = ?
        """,
        (
            guild_id,
        )
    )

    return cursor.fetchone()


def get_user(
    guild_id,
    user_id
):

    cursor.execute(
        """
        SELECT *
        FROM users

        WHERE guild_id = ?
        AND user_id = ?
        """,
        (
            guild_id,
            user_id
        )
    )

    row = cursor.fetchone()

    if row:

        return row


    cursor.execute(
        """
        INSERT INTO users (

            guild_id,

            user_id

        )

        VALUES (
            ?,
            ?
        )
        """,
        (
            guild_id,
            user_id
        )
    )

    db.commit()


    cursor.execute(
        """
        SELECT *
        FROM users

        WHERE guild_id = ?
        AND user_id = ?
        """,
        (
            guild_id,
            user_id
        )
    )

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

        "notification_channel",

        "daily_enabled",

        "weekly_enabled",

        "monthly_enabled",

        "xp_enabled",

        "reminders_enabled",

        "level_up_enabled",

        "level_up_mention",

        "level_up_message"

    }

    if setting not in allowed:

        raise ValueError(
            f"Invalid guild setting: {setting}"
        )


    get_guild(
        guild_id
    )


    cursor.execute(
        f"""
        UPDATE guilds

        SET {setting} = ?

        WHERE guild_id = ?
        """,
        (
            value,
            guild_id
        )
    )

    db.commit()


# ============================================================
# XP / LEVEL SYSTEM
# ============================================================

def calculate_level(
    xp
):

    level = 1

    required = 100

    remaining_xp = xp


    while remaining_xp >= required:

        remaining_xp -= required

        level += 1

        required = int(
            100 *
            (
                1.35 **
                (level - 1)
            )
        )


    return level


def level_required(
    level
):

    if level <= 1:

        return 0


    total = 0


    for current in range(
        1,
        level
    ):

        total += int(
            100 *
            (
                1.35 **
                (current - 1)
            )
        )


    return total


def add_xp(
    guild_id,
    user_id,
    amount
):

    if amount <= 0:

        return (
            get_user(
                guild_id,
                user_id
            )["level"],
            get_user(
                guild_id,
                user_id
            )["level"]
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


    cursor.execute(
        """
        UPDATE users

        SET xp = ?,
            level = ?

        WHERE guild_id = ?
        AND user_id = ?
        """,
        (
            new_xp,

            new_level,

            guild_id,

            user_id
        )
    )

    db.commit()


    return (
        old_level,
        new_level
    )


# ============================================================
# COINS
# ============================================================

def add_coins(
    guild_id,
    user_id,
    amount
):

    get_user(
        guild_id,
        user_id
    )


    cursor.execute(
        """
        UPDATE users

        SET coins = coins + ?

        WHERE guild_id = ?
        AND user_id = ?
        """,
        (
            amount,

            guild_id,

            user_id
        )
    )

    db.commit()


# ============================================================
# TASK DEFINITIONS
# ============================================================

DAILY_TASKS = [

    {
        "id": "daily_messages",

        "name": "إرسال 50 رسالة",

        "name_en": "Send 50 Messages",

        "description":
            "أرسل 50 رسالة في الروم المحدد.",

        "description_en":
            "Send 50 messages in the configured channel.",

        "start_hint":
            "ابدأ من روم المهام المحدد وأرسل الرسائل.",

        "start_hint_en":
            "Start in the configured task channel and send messages.",

        "target": 50,

        "reward": 10,

        "type": "messages"

    },

    {
        "id": "daily_invites",

        "name": "دعوة 3 أشخاص",

        "name_en": "Invite 3 People",

        "description":
            "ادعُ 3 أشخاص إلى السيرفر.",

        "description_en":
            "Invite 3 people to the server.",

        "start_hint":
            "ابدأ بإنشاء رابط دعوة للسيرفر وإرساله لأشخاص جدد.",

        "start_hint_en":
            "Create a server invite and invite new members.",

        "target": 3,

        "reward": 20,

        "type": "invites"

    },

    {
        "id": "daily_afk",

        "name": "AFK لمدة 30 دقيقة",

        "name_en": "AFK for 30 Minutes",

        "description":
            "ابقَ في أي روم صوتي لمدة 30 دقيقة.",

        "description_en":
            "Stay in any voice channel for 30 minutes.",

        "start_hint":
            "ادخل أي روم صوتي واترك نفسك فيه لمدة 30 دقيقة.",

        "start_hint_en":
            "Join any voice channel and stay there for 30 minutes.",

        "target": 1800,

        "reward": 30,

        "type": "afk"

    },

    {
        "id": "daily_level5",

        "name": "الوصول إلى Level 5",

        "name_en": "Reach Level 5",

        "description":
            "وصل إلى المستوى الخامس.",

        "description_en":
            "Reach level 5.",

        "start_hint":
            "اكسب XP من التفاعل مع السيرفر حتى تصل إلى Level 5.",

        "start_hint_en":
            "Earn XP through server activity until you reach Level 5.",

        "target": 5,

        "reward": 50,

        "type": "level"

    },

    {
        "id": "daily_images",

        "name": "إرسال 10 صور",

        "name_en": "Send 10 Images",

        "description":
            "أرسل 10 صور.",

        "description_en":
            "Send 10 images.",

        "start_hint":
            "ابدأ بإرسال الصور في الروم المحدد للمهمة.",

        "start_hint_en":
            "Start sending images in the configured task channel.",

        "target": 10,

        "reward": 20,

        "type": "images"

    }

]


WEEKLY_TASKS = [

    {
        "id": "weekly_afk",

        "name": "AFK لمدة ساعة",

        "name_en": "AFK for 1 Hour",

        "description":
            "ابقَ في روم صوتي لمدة ساعة.",

        "description_en":
            "Stay in a voice channel for one hour.",

        "start_hint":
            "ادخل أي روم صوتي وابقَ فيه لمدة ساعة.",

        "start_hint_en":
            "Join any voice channel and stay for one hour.",

        "target": 3600,

        "reward": 30,

        "type": "afk"

    },

    {
        "id": "weekly_messages",

        "name": "إرسال 200 رسالة",

        "name_en": "Send 200 Messages",

        "description":
            "أرسل 200 رسالة في الروم المحدد.",

        "description_en":
            "Send 200 messages in the configured channel.",

        "start_hint":
            "ابدأ من روم المهام المحدد وأرسل الرسائل.",

        "start_hint_en":
            "Start in the configured task channel and send messages.",

        "target": 200,

        "reward": 50,

        "type": "messages"

    },

    {
        "id": "weekly_invites",

        "name": "دعوة 10 أشخاص",

        "name_en": "Invite 10 People",

        "description":
            "ادعُ 10 أشخاص للسيرفر.",

        "description_en":
            "Invite 10 people to the server.",

        "start_hint":
            "ابدأ بدعوة أعضاء جدد إلى السيرفر.",

        "start_hint_en":
            "Start inviting new members to the server.",

        "target": 10,

        "reward": 70,

        "type": "invites"

    },

    {
        "id": "weekly_images",

        "name": "إرسال 30 صورة",

        "name_en": "Send 30 Images",

        "description":
            "أرسل 30 صورة.",

        "description_en":
            "Send 30 images.",

        "start_hint":
            "ابدأ بإرسال الصور في الروم المحدد.",

        "start_hint_en":
            "Start sending images in the configured channel.",

        "target": 30,

        "reward": 50,

        "type": "images"

    },

    {
        "id": "weekly_nickname",

        "name": "تغيير الاسم المستعار",

        "name_en": "Change Nickname",

        "description":
            "غيّر اسمك المستعار في السيرفر.",

        "description_en":
            "Change your server nickname.",

        "start_hint":
            "ابدأ بتغيير اسمك المستعار من إعدادات ملفك في السيرفر.",

        "start_hint_en":
            "Change your server nickname from your server profile settings.",

        "target": 1,

        "reward": 20,

        "type": "nickname"

    }

]


MONTHLY_TASKS = []


# ============================================================
# TASK HELPERS
# ============================================================

def get_task_list(
    period
):

    if period == "daily":

        return DAILY_TASKS

    if period == "weekly":

        return WEEKLY_TASKS

    if period == "monthly":

        return MONTHLY_TASKS

    return []


def get_task_by_id(
    task_id,
    period
):

    for task in get_task_list(
        period
    ):

        if task["id"] == task_id:

            return task


    return None


def get_active_task(
    guild_id,
    user_id,
    period
):

    task_list = get_task_list(
        period
    )


    if not task_list:

        return None


    cursor.execute(
        """
        SELECT *
        FROM active_tasks

        WHERE guild_id = ?
        AND user_id = ?
        AND period = ?
        """,
        (
            guild_id,

            user_id,

            period
        )
    )


    row = cursor.fetchone()


    if not row:

        cursor.execute(
            """
            INSERT INTO active_tasks (

                guild_id,

                user_id,

                period,

                task_index,

                started_at

            )

            VALUES (
                ?,
                ?,
                ?,
                0,
                ?
            )
            """,
            (
                guild_id,

                user_id,

                period,

                now().isoformat()
            )
        )

        db.commit()


        return task_list[0]


    index = row["task_index"]


    if index >= len(task_list):

        return None


    return task_list[index]


def set_active_task_index(
    guild_id,
    user_id,
    period,
    task_index
):

    cursor.execute(
        """
        INSERT INTO active_tasks (

            guild_id,

            user_id,

            period,

            task_index,

            started_at

        )

        VALUES (
            ?,
            ?,
            ?,
            ?,
            ?
        )

        ON CONFLICT (
            guild_id,
            user_id,
            period
        )

        DO UPDATE SET

            task_index = excluded.task_index,

            started_at = excluded.started_at
        """,
        (
            guild_id,

            user_id,

            period,

            task_index,

            now().isoformat()
        )
    )

    db.commit()


def get_task_index(
    guild_id,
    user_id,
    period
):

    cursor.execute(
        """
        SELECT task_index
        FROM active_tasks

        WHERE guild_id = ?
        AND user_id = ?
        AND period = ?
        """,
        (
            guild_id,

            user_id,

            period
        )
    )


    row = cursor.fetchone()


    if not row:

        get_active_task(
            guild_id,
            user_id,
            period
        )

        return 0


    return row["task_index"]


# ============================================================
# TASK COMPLETION
# ============================================================

def is_task_completed(
    guild_id,
    user_id,
    task_id,
    period
):

    cursor.execute(
        """
        SELECT 1

        FROM completed_tasks

        WHERE guild_id = ?
        AND user_id = ?
        AND task_id = ?
        AND period = ?
        """,
        (
            guild_id,

            user_id,

            task_id,

            period
        )
    )


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


    active_task = get_active_task(
        guild_id,
        user_id,
        period
    )


    if not active_task:

        return False


    if active_task["id"] != task_id:

        return False


    cursor.execute(
        """
        INSERT INTO completed_tasks (

            guild_id,

            user_id,

            task_id,

            period,

            completed_at

        )

        VALUES (
            ?,
            ?,
            ?,
            ?,
            ?
        )
        """,
        (
            guild_id,

            user_id,

            task_id,

            period,

            now().isoformat()
        )
    )


    add_coins(
        guild_id,

        user_id,

        reward
    )


    current_index = get_task_index(
        guild_id,

        user_id,

        period
    )


    set_active_task_index(
        guild_id,

        user_id,

        period,

        current_index + 1
    )


    db.commit()


    return True


# ============================================================
# TASK PROGRESS
# ============================================================

def get_task_progress(
    guild_id,
    user_id,
    task_id,
    period
):

    cursor.execute(
        """
        SELECT progress

        FROM task_progress

        WHERE guild_id = ?
        AND user_id = ?
        AND task_id = ?
        AND period = ?
        """,
        (
            guild_id,

            user_id,

            task_id,

            period
        )
    )


    row = cursor.fetchone()


    if not row:

        return 0


    return row["progress"]


def set_task_progress(
    guild_id,
    user_id,
    task_id,
    period,
    progress
):

    cursor.execute(
        """
        INSERT INTO task_progress (

            guild_id,

            user_id,

            task_id,

            period,

            progress,

            updated_at

        )

        VALUES (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )

        ON CONFLICT (
            guild_id,
            user_id,
            task_id,
            period
        )

        DO UPDATE SET

            progress = excluded.progress,

            updated_at = excluded.updated_at
        """,
        (
            guild_id,

            user_id,

            task_id,

            period,

            progress,

            now().isoformat()
        )
    )

    db.commit()


# ============================================================
# BASE EMBED
# ============================================================

def base_embed(
    title,
    description="",
    color=None
):

    if color is None:

        color = discord.Color.blurple()


    embed = discord.Embed(
        title=title,

        description=description,

        color=color,

        timestamp=now()
    )


    embed.set_footer(
        text="Forge Tasks BOT"
    )


    return embed


# ============================================================
# LANGUAGE HELPERS
# ============================================================

def get_language(
    guild_id
):

    guild = get_guild(
        guild_id
    )

    language = guild["language"]


    if language not in (
        "ar",
        "en"
    ):

        return "ar"


    return language


def localized(
    guild_id,
    arabic,
    english
):

    if get_language(
        guild_id
    ) == "en":

        return english


    return arabic


# ============================================================
# TASK RESET
# ============================================================

def reset_period(
    guild_id,
    period
):

    cursor.execute(
        """
        DELETE FROM completed_tasks

        WHERE guild_id = ?
        AND period = ?
        """,
        (
            guild_id,

            period
        )
    )


    cursor.execute(
        """
        DELETE FROM task_progress

        WHERE guild_id = ?
        AND period = ?
        """,
        (
            guild_id,

            period
        )
    )


    cursor.execute(
        """
        DELETE FROM active_tasks

        WHERE guild_id = ?
        AND period = ?
        """,
        (
            guild_id,

            period
        )
    )


    db.commit()


# ============================================================
# VOICE / AFK TRACKER
# ============================================================

@tasks.loop(
    seconds=60
)
async def voice_tracker():

    for guild in bot.guilds:

        guild_settings = get_guild(
            guild.id
        )


        for member in guild.members:

            if member.bot:

                continue


            if not member.voice:

                continue


            if not member.voice.channel:

                continue


            user = get_user(
                guild.id,

                member.id
            )


            # ----------------------------------------
            # VOICE TIME
            # ----------------------------------------

            cursor.execute(
                """
                UPDATE users

                SET voice_seconds =
                    voice_seconds + 60

                WHERE guild_id = ?
                AND user_id = ?
                """,
                (
                    guild.id,

                    member.id
                )
            )

            db.commit()


            voice_seconds = (
                user["voice_seconds"] +
                60
            )


            # ----------------------------------------
            # DAILY AFK TASK
            # ----------------------------------------

            daily_task = get_active_task(
                guild.id,

                member.id,

                "daily"
            )


            if (

                daily_task

                and

                daily_task["id"]
                == "daily_afk"

                and

                voice_seconds >= 1800

            ):

                complete_task(
                    guild.id,

                    member.id,

                    "daily_afk",

                    "daily",

                    30
                )


            # ----------------------------------------
            # WEEKLY AFK TASK
            # ----------------------------------------

            weekly_task = get_active_task(
                guild.id,

                member.id,

                "weekly"
            )


            if (

                weekly_task

                and

                weekly_task["id"]
                == "weekly_afk"

                and

                voice_seconds >= 3600

            ):

                complete_task(
                    guild.id,

                    member.id,

                    "weekly_afk",

                    "weekly",

                    30
                )


            # ----------------------------------------
            # VOICE XP
            # ----------------------------------------
            #
            # مهم:
            # XP هنا بسبب وقت الـVoice فقط.
            #
            # لا يوجد أي XP إضافي بسبب
            # Discord Server AFK status.
            #
            # نظام مهمة AFK الصوتية ما زال يعمل.
            # ----------------------------------------

            if guild_settings["xp_enabled"]:

                add_xp(
                    guild.id,

                    member.id,

                    XP_PER_VOICE_MINUTE
                )


# ============================================================
# VOICE TRACKER ERROR
# ============================================================

@voice_tracker.error
async def voice_tracker_error(
    error
):

    print(
        "Voice tracker error:",
        error
    )


# ============================================================
# BOT READY
# ============================================================

@bot.event
async def on_ready():

    print(
        f"Logged in as "
        f"{bot.user} "
        f"(ID: {bot.user.id})"
    )


# ============================================================
# RUN
# ============================================================

bot.run(
    TOKEN
)
