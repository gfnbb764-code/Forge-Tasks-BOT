# ============================================================
# TASK BOT — MAIN.PY
# Discord Tasks / Coins / XP / Levels
# Python 3.11+
# discord.py 2.6+
# ============================================================

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


DATABASE = "data/tasks.db"


# ============================================================
# DATABASE
# ============================================================

os.makedirs("data", exist_ok=True)

db = sqlite3.connect(DATABASE)
db.row_factory = sqlite3.Row

cursor = db.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS guilds (
    guild_id INTEGER PRIMARY KEY,

    language TEXT DEFAULT 'ar',

    currency_name TEXT DEFAULT 'Coins',
    currency_symbol TEXT DEFAULT '🪙',

    message_channel INTEGER DEFAULT NULL,

    daily_enabled INTEGER DEFAULT 1,
    weekly_enabled INTEGER DEFAULT 1,
    monthly_enabled INTEGER DEFAULT 1,

    xp_enabled INTEGER DEFAULT 1,

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

    PRIMARY KEY (guild_id, user_id)
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

    UNIQUE(guild_id, name)
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
            intents=intents
        )

    async def setup_hook(self):

        await self.tree.sync()

        voice_tracker.start()

        print("========================================")
        print(" TASK BOT")
        print("========================================")
        print("Bot started successfully.")
        print("Slash commands synchronized.")
        print("========================================")


bot = TaskBot()


# ============================================================
# HELPERS
# ============================================================

def now():

    return datetime.now(timezone.utc)


def get_guild(guild_id):

    cursor.execute(
        "SELECT * FROM guilds WHERE guild_id = ?",
        (guild_id,)
    )

    row = cursor.fetchone()

    if row:
        return row

    cursor.execute("""
        INSERT INTO guilds (
            guild_id,
            created_at
        )
        VALUES (?, ?)
    """, (
        guild_id,
        now().isoformat()
    ))

    db.commit()

    cursor.execute(
        "SELECT * FROM guilds WHERE guild_id = ?",
        (guild_id,)
    )

    return cursor.fetchone()


def get_user(guild_id, user_id):

    cursor.execute("""
        SELECT * FROM users
        WHERE guild_id = ?
        AND user_id = ?
    """, (
        guild_id,
        user_id
    ))

    row = cursor.fetchone()

    if row:
        return row

    cursor.execute("""
        INSERT INTO users (
            guild_id,
            user_id
        )
        VALUES (?, ?)
    """, (
        guild_id,
        user_id
    ))

    db.commit()

    cursor.execute("""
        SELECT * FROM users
        WHERE guild_id = ?
        AND user_id = ?
    """, (
        guild_id,
        user_id
    ))

    return cursor.fetchone()


def calculate_level(xp):

    level = 1
    required = 100

    while xp >= required:

        xp -= required

        level += 1

        required = int(
            100 * (1.35 ** (level - 1))
        )

    return level


def level_required(level):

    if level <= 1:
        return 0

    total = 0

    for current in range(1, level):

        total += int(
            100 * (1.35 ** (current - 1))
        )

    return total


def add_xp(guild_id, user_id, amount):

    user = get_user(
        guild_id,
        user_id
    )

    old_level = user["level"]

    new_xp = user["xp"] + amount

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

    db.commit()

    return old_level, new_level


def add_coins(guild_id, user_id, amount):

    get_user(
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

    db.commit()


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

    return cursor.fetchone() is not None


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
            completed_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        guild_id,
        user_id,
        task_id,
        period,
        now().isoformat()
    ))

    db.commit()

    add_coins(
        guild_id,
        user_id,
        reward
    )

    return True


# ============================================================
# EMBEDS
# ============================================================

def base_embed(
    title,
    description="",
    color=discord.Color.blurple()
):

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=now()
    )

    embed.set_footer(
        text="Task Bot"
    )

    return embed


# ============================================================
# TASKS
# ============================================================

DAILY_TASKS = [

    {
        "id": "daily_messages",
        "name": "إرسال 50 رسالة",
        "description": "أرسل 50 رسالة في الروم المحدد.",
        "target": 50,
        "reward": 10
    },

    {
        "id": "daily_invites",
        "name": "دعوة 3 أشخاص",
        "description": "ادعُ 3 أشخاص إلى السيرفر.",
        "target": 3,
        "reward": 20
    },

    {
        "id": "daily_afk",
        "name": "AFK لمدة 30 دقيقة",
        "description": "ابقَ في أي روم صوتي لمدة 30 دقيقة.",
        "target": 1800,
        "reward": 30
    },

    {
        "id": "daily_level5",
        "name": "الوصول إلى Level 5",
        "description": "وصل إلى المستوى الخامس.",
        "target": 5,
        "reward": 50
    },

    {
        "id": "daily_images",
        "name": "إرسال 10 صور",
        "description": "أرسل 10 صور.",
        "target": 10,
        "reward": 20
    }

]


WEEKLY_TASKS = [

    {
        "id": "weekly_afk",
        "name": "AFK لمدة ساعة",
        "description": "ابقَ في روم صوتي لمدة ساعة.",
        "target": 3600,
        "reward": 30
    },

    {
        "id": "weekly_messages",
        "name": "إرسال 200 رسالة",
        "description": "أرسل 200 رسالة في الروم المحدد.",
        "target": 200,
        "reward": 50
    },

    {
        "id": "weekly_invites",
        "name": "دعوة 10 أشخاص",
        "description": "ادعُ 10 أشخاص للسيرفر.",
        "target": 10,
        "reward": 70
    },

    {
        "id": "weekly_images",
        "name": "إرسال 30 صورة",
        "description": "أرسل 30 صورة.",
        "target": 30,
        "reward": 50
    },

    {
        "id": "weekly_nickname",
        "name": "تغيير الاسم المستعار",
        "description": "غيّر اسمك المستعار.",
        "target": 1,
        "reward": 20
    }

]


MONTHLY_TASKS = []


# ============================================================
# /TASKS
# ============================================================

@bot.tree.command(
    name="tasks",
    description="عرض المهام اليومية والأسبوعية والشهرية"
)
async def tasks_command(
    interaction: discord.Interaction
):

    guild = get_guild(
        interaction.guild.id
    )

    user = get_user(
        interaction.guild.id,
        interaction.user.id
    )

    embed = base_embed(
        "📋 مهامك",
        "أنجز المهام واحصل على الكوينز 🪙"
    )

    # DAILY

    daily_text = ""

    for task in DAILY_TASKS:

        completed = is_task_completed(
            interaction.guild.id,
            interaction.user.id,
            task["id"],
            "daily"
        )

        status = "✅" if completed else "⬜"

        daily_text += (
            f"{status} **{task['name']}**\n"
            f"└ {task['description']}\n"
            f"└ 🪙 {task['reward']} {guild['currency_name']}\n\n"
        )

    embed.add_field(
        name="☀️ المهام اليومية",
        value=daily_text or "لا توجد مهام.",
        inline=False
    )

    # WEEKLY

    weekly_text = ""

    for task in WEEKLY_TASKS:

        completed = is_task_completed(
            interaction.guild.id,
            interaction.user.id,
            task["id"],
            "weekly"
        )

        status = "✅" if completed else "⬜"

        weekly_text += (
            f"{status} **{task['name']}**\n"
            f"└ {task['description']}\n"
            f"└ 🪙 {task['reward']} {guild['currency_name']}\n\n"
        )

    embed.add_field(
        name="📅 المهام الأسبوعية",
        value=weekly_text or "لا توجد مهام.",
        inline=False
    )

    # MONTHLY

    monthly_text = ""

    for task in MONTHLY_TASKS:

        completed = is_task_completed(
            interaction.guild.id,
            interaction.user.id,
            task["id"],
            "monthly"
        )

        status = "✅" if completed else "⬜"

        monthly_text += (
            f"{status} **{task['name']}**\n"
            f"└ {task['description']}\n"
            f"└ 🪙 {task['reward']} {guild['currency_name']}\n\n"
        )

    embed.add_field(
        name="🌙 المهام الشهرية",
        value=monthly_text or "سيتم إضافة المهام الشهرية قريباً.",
        inline=False
    )

    await interaction.response.send_message(
        embed=embed
    )


# ============================================================
# /PROFILE
# ============================================================

@bot.tree.command(
    name="profile",
    description="عرض مستواك والكوينز والتقدم"
)
async def profile_command(
    interaction: discord.Interaction
):

    user = get_user(
        interaction.guild.id,
        interaction.user.id
    )

    guild = get_guild(
        interaction.guild.id
    )

    current_level_xp = level_required(
        user["level"]
    )

    next_level_xp = level_required(
        user["level"] + 1
    )

    progress = user["xp"] - current_level_xp

    required = (
        next_level_xp -
        current_level_xp
    )

    percentage = min(
        100,
        int((progress / required) * 100)
    )

    filled = int(
        percentage / 10
    )

    progress_bar = (
        "🟦" * filled +
        "⬜" * (10 - filled)
    )

    embed = base_embed(
        f"👤 {interaction.user.display_name}",
        "إحصائيات حسابك"
    )

    embed.set_thumbnail(
        url=interaction.user.display_avatar.url
    )

    embed.add_field(
        name="🪙 الرصيد",
        value=(
            f"**{user['coins']}** "
            f"{guild['currency_symbol']}"
        ),
        inline=True
    )

    embed.add_field(
        name="⭐ المستوى",
        value=f"**Level {user['level']}**",
        inline=True
    )

    embed.add_field(
        name="✨ XP",
        value=(
            f"**{progress} / {required}**"
        ),
        inline=True
    )

    embed.add_field(
        name="📊 التقدم",
        value=(
            f"{progress_bar}\n"
            f"**{percentage}%**"
        ),
        inline=False
    )

    embed.add_field(
        name="💬 الرسائل",
        value=str(user["messages"]),
        inline=True
    )

    embed.add_field(
        name="🖼️ الصور",
        value=str(user["images"]),
        inline=True
    )

    embed.add_field(
        name="📨 الدعوات",
        value=str(user["invites"]),
        inline=True
    )

    await interaction.response.send_message(
        embed=embed
    )


# ============================================================
# /BALANCE
# ============================================================

@bot.tree.command(
    name="balance",
    description="عرض رصيدك"
)
async def balance_command(
    interaction: discord.Interaction
):

    user = get_user(
        interaction.guild.id,
        interaction.user.id
    )

    guild = get_guild(
        interaction.guild.id
    )

    embed = base_embed(
        "🪙 رصيدك",
        (
            f"لديك **{user['coins']} "
            f"{guild['currency_symbol']}**"
        ),
        discord.Color.gold()
    )

    await interaction.response.send_message(
        embed=embed
    )


# ============================================================
# /TOP
# ============================================================

@bot.tree.command(
    name="top",
    description="عرض أفضل 10 أعضاء"
)
async def top_command(
    interaction: discord.Interaction
):

    cursor.execute("""
        SELECT *
        FROM users
        WHERE guild_id = ?
        ORDER BY coins DESC
        LIMIT 10
    """, (
        interaction.guild.id,
    ))

    users = cursor.fetchall()

    guild = get_guild(
        interaction.guild.id
    )

    description = ""

    medals = [
        "🥇",
        "🥈",
        "🥉"
    ]

    for index, user in enumerate(users):

        member = interaction.guild.get_member(
            user["user_id"]
        )

        if not member:
            name = f"<@{user['user_id']}>"
        else:
            name = member.display_name

        if index < 3:
            rank = medals[index]
        else:
            rank = f"**#{index + 1}**"

        description += (
            f"{rank} {name} — "
            f"**{user['coins']} "
            f"{guild['currency_symbol']}**\n"
        )

    if not description:

        description = "لا يوجد أعضاء في التوب حالياً."

    embed = base_embed(
        "🏆 Top 10",
        description,
        discord.Color.gold()
    )

    await interaction.response.send_message(
        embed=embed
    )


# ============================================================
# MESSAGE XP + TASK TRACKING
# ============================================================

@bot.event
async def on_message(
    message: discord.Message
):

    if message.author.bot:
        return

    if not message.guild:
        return

    guild_id = message.guild.id
    user_id = message.author.id

    user = get_user(
        guild_id,
        user_id
    )

    # ----------------------------------------
    # MESSAGE COUNT
    # ----------------------------------------

    cursor.execute("""
        UPDATE users

        SET messages = messages + 1,
            last_message = ?

        WHERE guild_id = ?
        AND user_id = ?
    """, (
        now().isoformat(),
        guild_id,
        user_id
    ))

    db.commit()

    # ----------------------------------------
    # XP
    # ----------------------------------------

    guild_settings = get_guild(
        guild_id
    )

    if guild_settings["xp_enabled"]:

        add_xp(
            guild_id,
            user_id,
            10
        )

    # ----------------------------------------
    # IMAGE
    # ----------------------------------------

    has_image = False

    for attachment in message.attachments:

        content_type = (
            attachment.content_type or ""
        )

        if content_type.startswith(
            "image/"
        ):

            has_image = True
            break

    if has_image:

        cursor.execute("""
            UPDATE users

            SET images = images + 1

            WHERE guild_id = ?
            AND user_id = ?
        """, (
            guild_id,
            user_id
        ))

        db.commit()

    # ----------------------------------------
    # DAILY MESSAGE TASK
    # ----------------------------------------

    user = get_user(
        guild_id,
        user_id
    )

    if user["messages"] >= 50:

        complete_task(
            guild_id,
            user_id,
            "daily_messages",
            "daily",
            10
        )

    # ----------------------------------------
    # DAILY IMAGE TASK
    # ----------------------------------------

    if user["images"] >= 10:

        complete_task(
            guild_id,
            user_id,
            "daily_images",
            "daily",
            20
        )

    # ----------------------------------------
    # WEEKLY MESSAGE TASK
    # ----------------------------------------

    if user["messages"] >= 200:

        complete_task(
            guild_id,
            user_id,
            "weekly_messages",
            "weekly",
            50
        )

    # ----------------------------------------
    # WEEKLY IMAGE TASK
    # ----------------------------------------

    if user["images"] >= 30:

        complete_task(
            guild_id,
            user_id,
            "weekly_images",
            "weekly",
            50
        )

    await bot.process_commands(
        message
    )


# ============================================================
# VOICE / AFK TRACKER
# ============================================================

@tasks.loop(seconds=60)
async def voice_tracker():

    for guild in bot.guilds:

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

            cursor.execute("""
                UPDATE users

                SET voice_seconds =
                    voice_seconds + 60

                WHERE guild_id = ?
                AND user_id = ?
            """, (
                guild.id,
                member.id
            ))

            db.commit()

            # -----------------------------
            # DAILY AFK
            # -----------------------------

            if user["voice_seconds"] + 60 >= 1800:

                complete_task(
                    guild.id,
                    member.id,
                    "daily_afk",
                    "daily",
                    30
                )

            # -----------------------------
            # WEEKLY AFK
            # -----------------------------

            if user["voice_seconds"] + 60 >= 3600:

                complete_task(
                    guild.id,
                    member.id,
                    "weekly_afk",
                    "weekly",
                    30
                )

            # -----------------------------
            # VOICE XP
            # -----------------------------

            guild_settings = get_guild(
                guild.id
            )

            if guild_settings["xp_enabled"]:

                add_xp(
                    guild.id,
                    member.id,
                    5
                )


# ============================================================
# /SETUP
# ============================================================

@bot.tree.command(
    name="setup",
    description="إعداد نظام المهام والبوت"
)
@app_commands.describe(
    language="لغة البوت",
    currency="اسم العملة",
    symbol="رمز العملة"
)
@app_commands.choices(
    language=[
        app_commands.Choice(
            name="العربية",
            value="ar"
        ),
        app_commands.Choice(
            name="English",
            value="en"
        )
    ]
)
async def setup_command(
    interaction: discord.Interaction,
    language: app_commands.Choice[str] | None = None,
    currency: str | None = None,
    symbol: str | None = None
):

    if not interaction.user.guild_permissions.manage_guild:

        await interaction.response.send_message(
            "❌ تحتاج صلاحية **Manage Server** لاستخدام هذا الأمر.",
            ephemeral=True
        )

        return

    get_guild(
        interaction.guild.id
    )

    if language:

        cursor.execute("""
            UPDATE guilds

            SET language = ?

            WHERE guild_id = ?
        """, (
            language.value,
            interaction.guild.id
        ))

    if currency:

        cursor.execute("""
            UPDATE guilds

            SET currency_name = ?

            WHERE guild_id = ?
        """, (
            currency,
            interaction.guild.id
        ))

    if symbol:

        cursor.execute("""
            UPDATE guilds

            SET currency_symbol = ?

            WHERE guild_id = ?
        """, (
            symbol,
            interaction.guild.id
        ))

    db.commit()

    guild = get_guild(
        interaction.guild.id
    )

    embed = base_embed(
        "⚙️ إعدادات البوت",
        "تم تحديث إعدادات السيرفر بنجاح.",
        discord.Color.green()
    )

    embed.add_field(
        name="🌐 اللغة",
        value=guild["language"],
        inline=True
    )

    embed.add_field(
        name="🪙 العملة",
        value=(
            f"{guild['currency_symbol']} "
            f"{guild['currency_name']}"
        ),
        inline=True
    )

    embed.add_field(
        name="📋 المهام",
        value=(
            "☀️ يومية\n"
            "📅 أسبوعية\n"
            "🌙 شهرية"
        ),
        inline=True
    )

    await interaction.response.send_message(
        embed=embed
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

bot.run(TOKEN)
