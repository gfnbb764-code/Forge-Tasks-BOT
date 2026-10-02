# ============================================================
# TASK BOT — MAIN.PY
# Forge Tasks BOT
# Discord Tasks / Coins / XP / Levels
# Python 3.11+
# discord.py 2.6+
# ============================================================

from __future__ import annotations

import os
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
    ).lower() == "true"
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
    ).lower() == "true"
)

DAILY_TASKS_ENABLED_DEFAULT = (
    os.getenv(
        "DAILY_TASKS_ENABLED",
        "true"
    ).lower() == "true"
)

WEEKLY_TASKS_ENABLED_DEFAULT = (
    os.getenv(
        "WEEKLY_TASKS_ENABLED",
        "true"
    ).lower() == "true"
)

MONTHLY_TASKS_ENABLED_DEFAULT = (
    os.getenv(
        "MONTHLY_TASKS_ENABLED",
        "false"
    ).lower() == "true"
)

LEVEL_UP_ENABLED_DEFAULT = (
    os.getenv(
        "LEVEL_UP_ENABLED",
        "true"
    ).lower() == "true"
)

LEVEL_UP_MENTION_DEFAULT = (
    os.getenv(
        "LEVEL_UP_MENTION",
        "true"
    ).lower() == "true"
)

LEVEL_UP_MESSAGE_DEFAULT = os.getenv(
    "LEVEL_UP_MESSAGE",
    "🎉 مبروك {mention}! وصلت إلى المستوى {level}!"
)


# ============================================================
# DATABASE
# ============================================================

os.makedirs(
    os.path.dirname(DATABASE) or ".",
    exist_ok=True
)

db = sqlite3.connect(
    DATABASE,
    check_same_thread=False
)

db.row_factory = sqlite3.Row

cursor = db.cursor()


# ============================================================
# DATABASE TABLES
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS guilds (
    guild_id INTEGER PRIMARY KEY,

    language TEXT DEFAULT 'ar',

    currency_name TEXT DEFAULT 'Coins',
    currency_symbol TEXT DEFAULT '🪙',

    message_channel INTEGER DEFAULT NULL,
    notification_channel INTEGER DEFAULT NULL,

    daily_enabled INTEGER DEFAULT 1,
    weekly_enabled INTEGER DEFAULT 1,
    monthly_enabled INTEGER DEFAULT 0,

    xp_enabled INTEGER DEFAULT 1,

    reminders_enabled INTEGER DEFAULT 1,

    level_up_enabled INTEGER DEFAULT 1,
    level_up_mention INTEGER DEFAULT 1,

    level_up_message TEXT
        DEFAULT '🎉 مبروك {mention}! وصلت إلى المستوى {level}!',

    created_at TEXT
)
""")


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
    last_xp TEXT,

    PRIMARY KEY (
        guild_id,
        user_id
    )
)
""")


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


cursor.execute("""
CREATE TABLE IF NOT EXISTS task_state (
    guild_id INTEGER,
    user_id INTEGER,

    period TEXT,

    current_index INTEGER DEFAULT 0,

    period_key TEXT,

    updated_at TEXT,

    PRIMARY KEY (
        guild_id,
        user_id,
        period
    )
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS invite_cache (
    guild_id INTEGER,
    invite_code TEXT,

    uses INTEGER DEFAULT 0,

    PRIMARY KEY (
        guild_id,
        invite_code
    )
)
""")


# ============================================================
# DATABASE MIGRATION
# ============================================================

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

        db.commit()


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
    "TEXT DEFAULT '🎉 مبروك {mention}! وصلت إلى المستوى {level}!'"
)

add_column_if_missing(
    "users",
    "last_xp",
    "TEXT DEFAULT NULL"
)


db.commit()


# ============================================================
# BOT
# ============================================================

intents = discord.Intents.default()

intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True
intents.voice_states = True
intents.invites = True


class TaskBot(commands.Bot):

    def __init__(self):

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):

        await self.tree.sync()

        if not voice_tracker.is_running():

            voice_tracker.start()

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
            "Slash commands synchronized."
        )

        print(
            "========================================"
        )


bot = TaskBot()


# ============================================================
# HELPERS
# ============================================================

def now():

    return datetime.now(
        timezone.utc
    )


def current_period_key(
    period
):

    current = now()

    if period == "daily":

        return current.strftime(
            "%Y-%m-%d"
        )

    if period == "weekly":

        return current.strftime(
            "%Y-W%W"
        )

    if period == "monthly":

        return current.strftime(
            "%Y-%m"
        )

    return current.strftime(
        "%Y-%m-%d"
    )


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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            guild_id,
            DEFAULT_LANGUAGE,
            DEFAULT_CURRENCY,
            DEFAULT_CURRENCY_SYMBOL,
            int(
                DAILY_TASKS_ENABLED_DEFAULT
            ),
            int(
                WEEKLY_TASKS_ENABLED_DEFAULT
            ),
            int(
                MONTHLY_TASKS_ENABLED_DEFAULT
            ),
            int(
                XP_ENABLED_DEFAULT
            ),
            int(
                REMINDERS_ENABLED_DEFAULT
            ),
            int(
                LEVEL_UP_ENABLED_DEFAULT
            ),
            int(
                LEVEL_UP_MENTION_DEFAULT
            ),
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
            "Invalid guild setting."
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
        VALUES (?, ?)
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


# ============================================================
# LEVEL SYSTEM
# ============================================================

def calculate_level(
    xp
):

    level = 1
    required = 100

    remaining = xp

    while remaining >= required:

        remaining -= required

        level += 1

        required = int(
            100 * (
                1.35 ** (
                    level - 1
                )
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
            100 * (
                1.35 ** (
                    current - 1
                )
            )
        )

    return total


async def send_level_up_message(
    guild,
    member,
    new_level
):

    settings = get_guild(
        guild.id
    )

    if not settings[
        "level_up_enabled"
    ]:

        return

    channel = None

    if settings[
        "notification_channel"
    ]:

        channel = guild.get_channel(
            settings[
                "notification_channel"
            ]
        )

    if channel is None:

        channel = guild.system_channel

    if channel is None:

        return

    mention = (
        member.mention
        if settings[
            "level_up_mention"
        ]
        else member.display_name
    )

    message = settings[
        "level_up_message"
    ]

    message = message.replace(
        "{mention}",
        mention
    )

    message = message.replace(
        "{user}",
        member.display_name
    )

    message = message.replace(
        "{level}",
        str(new_level)
    )

    try:

        await channel.send(
            message
        )

    except (
        discord.Forbidden,
        discord.HTTPException
    ):

        pass


async def add_xp(
    guild_id,
    user_id,
    amount
):

    user = get_user(
        guild_id,
        user_id
    )

    old_level = user[
        "level"
    ]

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
            level = ?,
            last_xp = ?

        WHERE guild_id = ?
        AND user_id = ?
        """,
        (
            new_xp,
            new_level,
            now().isoformat(),
            guild_id,
            user_id
        )
    )

    db.commit()

    if new_level > old_level:

        guild = bot.get_guild(
            guild_id
        )

        if guild:

            member = guild.get_member(
                user_id
            )

            if member:

                await send_level_up_message(
                    guild,
                    member,
                    new_level
                )

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


def remove_coins(
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

        SET coins = MAX(
            coins - ?,
            0
        )

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
# TRANSLATIONS
# ============================================================

TRANSLATIONS = {

    "ar": {

        "tasks_title": "📋 مهمتك الحالية",

        "tasks_description":
            "أنجز المهمة الحالية لفتح المهمة التالية.",

        "daily": "☀️ المهمة اليومية",

        "weekly": "📅 المهمة الأسبوعية",

        "monthly": "🌙 المهمة الشهرية",

        "reward": "المكافأة",

        "progress": "التقدم",

        "start": "🚀 ابدأ المهمة",

        "details": "📖 التفاصيل",

        "refresh": "🔄 تحديث",

        "completed": "✅ اكتملت",

        "locked":
            "🔒 أكمل المهمة الحالية أولاً لفتح هذه المهمة.",

        "all_completed":
            "🎉 أكملت جميع المهام المتاحة لهذه الفترة!",

        "help_title":
            "❓ مساعدة Forge Tasks BOT",

        "help_description":
            "استخدم الأوامر التالية للتعامل مع نظام المهام والـXP والكوينز.",

        "info_title":
            "ℹ️ معلومات Forge Tasks BOT",

        "setup_title":
            "⚙️ لوحة إعداد Forge Tasks BOT",

        "setup_description":
            "استخدم الأزرار والقوائم بالأسفل لتعديل إعدادات السيرفر.",

        "balance":
            "🪙 الرصيد",

        "profile":
            "👤 الملف الشخصي",

        "top":
            "🏆 الترتيب",

        "language":
            "🌐 اللغة",

        "currency":
            "🪙 العملة",

        "channel":
            "📍 قناة المهام",

        "notifications":
            "🔔 قناة الإشعارات",

        "level_up":
            "🎉 إعدادات Level Up",

        "reminders":
            "⏰ التذكيرات",

        "enabled":
            "مفعّل",

        "disabled":
            "متوقف",

        "yes":
            "نعم",

        "no":
            "لا",

        "back":
            "⬅️ رجوع",

        "close":
            "✖️ إغلاق",

        "saved":
            "✅ تم حفظ الإعدادات.",

        "permission":
            "❌ تحتاج صلاحية **Manage Server** لاستخدام هذا القسم.",

        "message_channel":
            "ابدأ من قناة الرسائل المحددة.",

        "voice_channel":
            "ادخل أي قناة صوتية وابقَ فيها للمدة المطلوبة.",

        "invite":
            "ابدأ بدعوة أعضاء جدد إلى السيرفر.",

        "nickname":
            "ابدأ بتغيير اسمك المستعار في السيرفر.",

        "level":
            "اكسب XP من التفاعل حتى تصل إلى المستوى المطلوب.",

        "image":
            "أرسل الصور في القناة المحددة للمهمة.",

        "next":
            "بعد إكمالها ستفتح المهمة التالية.",

        "no_channel":
            "لم يتم تحديد قناة بعد."
    },

    "en": {

        "tasks_title": "📋 Your Current Task",

        "tasks_description":
            "Complete the current task to unlock the next one.",

        "daily": "☀️ Daily Task",

        "weekly": "📅 Weekly Task",

        "monthly": "🌙 Monthly Task",

        "reward": "Reward",

        "progress": "Progress",

        "start": "🚀 Start Task",

        "details": "📖 Details",

        "refresh": "🔄 Refresh",

        "completed": "✅ Completed",

        "locked":
            "🔒 Complete the current task first to unlock this one.",

        "all_completed":
            "🎉 You completed all available tasks for this period!",

        "help_title":
            "❓ Forge Tasks BOT Help",

        "help_description":
            "Use the following commands to manage tasks, XP and coins.",

        "info_title":
            "ℹ️ Forge Tasks BOT Information",

        "setup_title":
            "⚙️ Forge Tasks BOT Setup",

        "setup_description":
            "Use the buttons and menus below to configure the server.",

        "balance":
            "🪙 Balance",

        "profile":
            "👤 Profile",

        "top":
            "🏆 Leaderboard",

        "language":
            "🌐 Language",

        "currency":
            "🪙 Currency",

        "channel":
            "📍 Task Channel",

        "notifications":
            "🔔 Notification Channel",

        "level_up":
            "🎉 Level Up Settings",

        "reminders":
            "⏰ Reminders",

        "enabled":
            "Enabled",

        "disabled":
            "Disabled",

        "yes":
            "Yes",

        "no":
            "No",

        "back":
            "⬅️ Back",

        "close":
            "✖️ Close",

        "saved":
            "✅ Settings saved.",

        "permission":
            "❌ You need **Manage Server** permission to use this section.",

        "message_channel":
            "Start in the configured message channel.",

        "voice_channel":
            "Join any voice channel and stay there for the required time.",

        "invite":
            "Start by inviting new members to the server.",

        "nickname":
            "Start by changing your server nickname.",

        "level":
            "Earn XP through activity until you reach the required level.",

        "image":
            "Send images in the configured task channel.",

        "next":
            "The next task will unlock after completion.",

        "no_channel":
            "No channel has been configured yet."
    }
}


def get_language(
    guild_id
):

    guild = get_guild(
        guild_id
    )

    language = guild[
        "language"
    ]

    if language not in TRANSLATIONS:

        return "ar"

    return language


def t(
    guild_id,
    key
):

    language = get_language(
        guild_id
    )

    return TRANSLATIONS[
        language
    ].get(
        key,
        key
    )


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

        "target": 50,

        "reward": 10,

        "type": "messages",

        "start": "message_channel"
    },

    {
        "id": "daily_invites",

        "name": "دعوة 3 أشخاص",

        "name_en": "Invite 3 People",

        "description":
            "ادعُ 3 أشخاص إلى السيرفر.",

        "description_en":
            "Invite 3 people to the server.",

        "target": 3,

        "reward": 20,

        "type": "invites",

        "start": "invite"
    },

    {
        "id": "daily_afk",

        "name": "AFK لمدة 30 دقيقة",

        "name_en": "AFK for 30 Minutes",

        "description":
            "ابقَ في أي روم صوتي لمدة 30 دقيقة.",

        "description_en":
            "Stay in any voice channel for 30 minutes.",

        "target": 1800,

        "reward": 30,

        "type": "voice",

        "start": "voice_channel"
    },

    {
        "id": "daily_level5",

        "name": "الوصول إلى Level 5",

        "name_en": "Reach Level 5",

        "description":
            "وصل إلى المستوى الخامس.",

        "description_en":
            "Reach level 5.",

        "target": 5,

        "reward": 50,

        "type": "level",

        "start": "level"
    },

    {
        "id": "daily_images",

        "name": "إرسال 10 صور",

        "name_en": "Send 10 Images",

        "description":
            "أرسل 10 صور.",

        "description_en":
            "Send 10 images.",

        "target": 10,

        "reward": 20,

        "type": "images",

        "start": "image"
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

        "target": 3600,

        "reward": 30,

        "type": "voice",

        "start": "voice_channel"
    },

    {
        "id": "weekly_messages",

        "name": "إرسال 200 رسالة",

        "name_en": "Send 200 Messages",

        "description":
            "أرسل 200 رسالة في الروم المحدد.",

        "description_en":
            "Send 200 messages in the configured channel.",

        "target": 200,

        "reward": 50,

        "type": "messages",

        "start": "message_channel"
    },

    {
        "id": "weekly_invites",

        "name": "دعوة 10 أشخاص",

        "name_en": "Invite 10 People",

        "description":
            "ادعُ 10 أشخاص للسيرفر.",

        "description_en":
            "Invite 10 people to the server.",

        "target": 10,

        "reward": 70,

        "type": "invites",

        "start": "invite"
    },

    {
        "id": "weekly_images",

        "name": "إرسال 30 صورة",

        "name_en": "Send 30 Images",

        "description":
            "أرسل 30 صورة.",

        "description_en":
            "Send 30 images.",

        "target": 30,

        "reward": 50,

        "type": "images",

        "start": "image"
    },

    {
        "id": "weekly_nickname",

        "name": "تغيير الاسم المستعار",

        "name_en": "Change Nickname",

        "description":
            "غيّر اسمك المستعار.",

        "description_en":
            "Change your server nickname.",

        "target": 1,

        "reward": 20,

        "type": "nickname",

        "start": "nickname"
    }

]


MONTHLY_TASKS = []


# ============================================================
# TASK HELPERS
# ============================================================

def get_tasks_for_period(
    period
):

    if period == "daily":

        return DAILY_TASKS

    if period == "weekly":

        return WEEKLY_TASKS

    if period == "monthly":

        return MONTHLY_TASKS

    return []


def get_task(
    task_id
):

    all_tasks = (
        DAILY_TASKS +
        WEEKLY_TASKS +
        MONTHLY_TASKS
    )

    for task in all_tasks:

        if task["id"] == task_id:

            return task

    return None


def get_task_state(
    guild_id,
    user_id,
    period
):

    period_key = current_period_key(
        period
    )

    cursor.execute(
        """
        SELECT *
        FROM task_state

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

    state = cursor.fetchone()

    if state:

        if state["period_key"] != period_key:

            cursor.execute(
                """
                UPDATE task_state

                SET current_index = 0,
                    period_key = ?,
                    updated_at = ?

                WHERE guild_id = ?
                AND user_id = ?
                AND period = ?
                """,
                (
                    period_key,
                    now().isoformat(),
                    guild_id,
                    user_id,
                    period
                )
            )

            db.commit()

            cursor.execute(
                """
                SELECT *
                FROM task_state

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

            state = cursor.fetchone()

        return state

    cursor.execute(
        """
        INSERT INTO task_state (
            guild_id,
            user_id,
            period,
            current_index,
            period_key,
            updated_at
        )
        VALUES (?, ?, ?, 0, ?, ?)
        """,
        (
            guild_id,
            user_id,
            period,
            period_key,
            now().isoformat()
        )
    )

    db.commit()

    cursor.execute(
        """
        SELECT *
        FROM task_state

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

    return cursor.fetchone()


def get_current_task(
    guild_id,
    user_id,
    period
):

    tasks_list = get_tasks_for_period(
        period
    )

    if not tasks_list:

        return None

    state = get_task_state(
        guild_id,
        user_id,
        period
    )

    index = state[
        "current_index"
    ]

    if index >= len(tasks_list):

        return None

    return tasks_list[
        index
    ]


def advance_task(
    guild_id,
    user_id,
    period
):

    state = get_task_state(
        guild_id,
        user_id,
        period
    )

    cursor.execute(
        """
        UPDATE task_state

        SET current_index =
            current_index + 1,

            updated_at = ?

        WHERE guild_id = ?
        AND user_id = ?
        AND period = ?
        """,
        (
            now().isoformat(),
            guild_id,
            user_id,
            period
        )
    )

    db.commit()

    return state[
        "current_index"
    ] + 1


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

    return row[
        "progress"
    ]


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
        VALUES (?, ?, ?, ?, ?, ?)

        ON CONFLICT(
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


async def complete_task(
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

    current_task = get_current_task(
        guild_id,
        user_id,
        period
    )

    if not current_task:

        return False

    if current_task[
        "id"
    ] != task_id:

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
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            guild_id,
            user_id,
            task_id,
            period,
            now().isoformat()
        )
    )

    db.commit()

    add_coins(
        guild_id,
        user_id,
        reward
    )

    advance_task(
        guild_id,
        user_id,
        period
    )

    return True


# ============================================================
# TASK PROGRESS
# ============================================================

def get_user_stat_for_task(
    user,
    task
):

    task_type = task[
        "type"
    ]

    if task_type == "messages":

        return user[
            "messages"
        ]

    if task_type == "images":

        return user[
            "images"
        ]

    if task_type == "invites":

        return user[
            "invites"
        ]

    if task_type == "voice":

        return user[
            "voice_seconds"
        ]

    if task_type == "level":

        return user[
            "level"
        ]

    if task_type == "nickname":

        return get_task_progress(
            user["guild_id"],
            user["user_id"],
            task["id"],
            "weekly"
        )

    return 0


def task_progress_percentage(
    progress,
    target
):

    if target <= 0:

        return 100

    return min(
        100,
        int(
            (
                progress /
                target
            ) * 100
        )
    )


def make_progress_bar(
    progress,
    target,
    size=10
):

    percentage = task_progress_percentage(
        progress,
        target
    )

    filled = int(
        percentage /
        (
            100 / size
        )
    )

    filled = max(
        0,
        min(
            size,
            filled
        )
    )

    return (
        "🟦" * filled +
        "⬜" * (
            size - filled
        )
    )

