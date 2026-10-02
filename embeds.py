# ============================================================
# TASK BOT — EMBEDS.PY
# Professional Discord Embeds
# Python 3.11+
# ============================================================

import discord

from datetime import datetime, timezone

from tasks import (
    get_active_task_display,
    get_all_active_tasks,
    get_task_start_info,
    progress_bar,
)


# ============================================================
# COLORS
# ============================================================

COLOR_MAIN = discord.Color.blurple()
COLOR_SUCCESS = discord.Color.green()
COLOR_WARNING = discord.Color.orange()
COLOR_ERROR = discord.Color.red()
COLOR_GOLD = discord.Color.gold()
COLOR_LEVEL = discord.Color.purple()


# ============================================================
# TIME
# ============================================================

def now():

    return datetime.now(
        timezone.utc
    )


# ============================================================
# BASE EMBED
# ============================================================

def create_embed(
    title,
    description="",
    color=COLOR_MAIN
):

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
# TASK EMOJI
# ============================================================

def task_emoji(
    task_type
):

    emojis = {

        "messages": "💬",

        "images": "🖼️",

        "invites": "📨",

        "afk": "🎙️",

        "level": "⭐",

        "nickname": "✏️",

    }

    return emojis.get(
        task_type,
        "📋"
    )


# ============================================================
# PERIOD EMOJI
# ============================================================

def period_emoji(
    period
):

    emojis = {

        "daily": "☀️",

        "weekly": "📅",

        "monthly": "🌙",

    }

    return emojis.get(
        period,
        "📋"
    )


# ============================================================
# PERIOD NAME
# ============================================================

def period_name(
    period
):

    names = {

        "daily": "المهمة اليومية",

        "weekly": "المهمة الأسبوعية",

        "monthly": "المهمة الشهرية",

    }

    return names.get(
        period,
        "المهمة"
    )


# ============================================================
# TASKS EMBED
# ============================================================

def tasks_embed(
    guild_id,
    user_id,
    currency_name,
    currency_symbol,
    language="ar"
):

    english = language == "en"

    embed = create_embed(

        "📋 Your Tasks" if english else "📋 مهامك",

        (
            (
                "Complete the current task to unlock the next one and earn "
                f"**{currency_symbol} {currency_name}**."
                if english else
                "أنجز المهمة الحالية لفتح المهمة التالية "
                f"واحصل على **{currency_symbol} {currency_name}**."
            )
        ),

        COLOR_MAIN

    )


    periods = [

        (
            "daily",
            "☀️ المهام اليومية"
        ),

        (
            "weekly",
            "📅 المهام الأسبوعية"
        ),

        (
            "monthly",
            "🌙 المهام الشهرية"
        ),

    ]


    for period, title in periods:

        task = get_active_task_display(

            guild_id,

            user_id,

            period

        )


        # ----------------------------------------------------
        # الفترة غير مفعلة
        # ----------------------------------------------------

        if (
            not task.get(
                "available"
            )
            and task.get(
                "reason"
            ) == "period_disabled"
        ):

            value = "🔒 هذا النوع من المهام معطل."

        # ----------------------------------------------------
        # جميع المهام مكتملة
        # ----------------------------------------------------

        elif (
            not task.get(
                "available"
            )
            and task.get(
                "reason"
            ) == "all_completed"
        ):

            value = (
                "🎉 **أكملت جميع مهام هذه الفترة!**\n"
                "انتظر بداية الفترة القادمة."
            )

        # ----------------------------------------------------
        # لا توجد مهام
        # ----------------------------------------------------

        elif not task.get(
            "available"
        ):

            value = (
                "لا توجد مهام متاحة حالياً."
            )

        # ----------------------------------------------------
        # المهمة الحالية
        # ----------------------------------------------------

        else:

            emoji = task_emoji(
                task.get(
                    "type",
                    ""
                )
            )


            value = (

                f"🚀 **المهمة "
                f"{task['task_number']}/"
                f"{task['total_tasks']}**\n\n"

                f"{emoji} **{task['name']}**\n"

                f"└ {task['description']}\n\n"

                f"{task['bar']} "
                f"`{task['progress']}/"
                f"{task['target']}` "
                f"**{task['percentage']}%**\n\n"

                f"🎁 المكافأة: "
                f"**{task['reward']} "
                f"{currency_symbol} "
                f"{currency_name}**"

            )


        embed.add_field(

            name=title,

            value=value,

            inline=False

        )


    embed.set_footer(

        text=(
            "Forge Tasks BOT • أكمل المهمة الحالية لفتح التالية"
        )

    )


    return embed


# ============================================================
# SINGLE ACTIVE TASK EMBED
# ============================================================

def active_task_embed(
    guild_id,
    user_id,
    period,
    currency_name,
    currency_symbol
):

    task = get_active_task_display(

        guild_id,

        user_id,

        period

    )


    title = (
        f"{period_emoji(period)} "
        f"{period_name(period)}"
    )


    # --------------------------------------------------------
    # PERIOD DISABLED
    # --------------------------------------------------------

    if (
        not task.get(
            "available"
        )
        and task.get(
            "reason"
        ) == "period_disabled"
    ):

        return create_embed(

            title,

            "🔒 هذا النوع من المهام معطل حالياً.",

            COLOR_WARNING

        )


    # --------------------------------------------------------
    # ALL COMPLETED
    # --------------------------------------------------------

    if (
        not task.get(
            "available"
        )
        and task.get(
            "reason"
        ) == "all_completed"
    ):

        return create_embed(

            title,

            (
                "🎉 **أكملت جميع مهام هذه الفترة!**\n\n"
                "ترقب بداية الفترة القادمة للحصول على مهام جديدة."
            ),

            COLOR_SUCCESS

        )


    # --------------------------------------------------------
    # NO TASK
    # --------------------------------------------------------

    if not task.get(
        "available"
    ):

        return create_embed(

            title,

            "لا توجد مهمة متاحة حالياً.",

            COLOR_WARNING

        )


    emoji = task_emoji(
        task["type"]
    )


    embed = create_embed(

        f"{emoji} {task['name']}",

        task["description"],

        COLOR_MAIN

    )


    embed.add_field(

        name="📊 التقدم",

        value=(

            f"{task['bar']}\n"

            f"**{task['progress']} / "
            f"{task['target']}** "

            f"({task['percentage']}%)"

        ),

        inline=False

    )


    embed.add_field(

        name="🎁 المكافأة",

        value=(

            f"**{task['reward']} "
            f"{currency_symbol} "
            f"{currency_name}**"

        ),

        inline=True

    )


    embed.add_field(

        name="📋 ترتيب المهمة",

        value=(

            f"**{task['task_number']} / "
            f"{task['total_tasks']}**"

        ),

        inline=True

    )


    embed.add_field(

        name="🚀 كيف تبدأ؟",

        value=get_task_start_text(
            task["type"]
        ),

        inline=False

    )


    embed.set_footer(

        text=(
            "أكمل هذه المهمة لفتح المهمة التالية."
        )

    )


    return embed


# ============================================================
# TASK START TEXT
# ============================================================

def get_task_start_text(
    task_type
):

    instructions = {

        "messages": (
            "💬 أرسل الرسائل في الروم المحدد."
        ),

        "images": (
            "🖼️ أرسل الصور حتى تصل للعدد المطلوب."
        ),

        "invites": (
            "📨 ادعُ أعضاء جدد إلى السيرفر."
        ),

        "afk": (
            "🎙️ ادخل أي روم صوتي وابقَ فيه حتى يكتمل الوقت المطلوب."
        ),

        "level": (
            "⭐ استمر في اكتساب XP حتى تصل إلى المستوى المطلوب."
        ),

        "nickname": (
            "✏️ غيّر اسمك المستعار في السيرفر مرة واحدة."
        ),

    }


    return instructions.get(

        task_type,

        "📋 ابدأ بتنفيذ المهمة."

    )


# ============================================================
# PROFILE EMBED
# ============================================================

def profile_embed(
    member,
    user,
    currency_name,
    currency_symbol,
    current_xp,
    required_xp,
    percentage,
    language="ar"
):

    english = language == "en"

    embed = create_embed(

        f"👤 {member.display_name}",

        "Your account statistics and progress" if english else "إحصائيات حسابك وتقدمك",

        COLOR_MAIN

    )


    embed.set_thumbnail(

        url=member.display_avatar.url

    )


    filled = int(
        percentage / 10
    )


    filled = max(

        0,

        min(
            filled,
            10
        )

    )


    bar = (

        "🟦" * filled +

        "⬜" * (
            10 - filled
        )

    )


    embed.add_field(

        name="🪙 Balance" if english else "🪙 الرصيد",

        value=(

            f"**{user['coins']}** "
            f"{currency_symbol}"

        ),

        inline=True

    )


    embed.add_field(

        name="⭐ Level" if english else "⭐ المستوى",

        value=(

            f"**Level "
            f"{user['level']}**"

        ),

        inline=True

    )


    embed.add_field(

        name="✨ XP",

        value=(

            f"**{current_xp} / "
            f"{required_xp}**"

        ),

        inline=True

    )


    embed.add_field(

        name="📊 Progress" if english else "📊 التقدم",

        value=(

            f"{bar}\n"
            f"**{percentage}%**"

        ),

        inline=False

    )


    embed.add_field(

        name="💬 Messages" if english else "💬 الرسائل",

        value=str(
            user["messages"]
        ),

        inline=True

    )


    embed.add_field(

        name="🖼️ Images" if english else "🖼️ الصور",

        value=str(
            user["images"]
        ),

        inline=True

    )


    embed.add_field(

        name="📨 Invites" if english else "📨 الدعوات",

        value=str(
            user["invites"]
        ),

        inline=True

    )


    embed.add_field(

        name="🎙️ Voice time" if english else "🎙️ وقت الصوت",

        value=format_seconds(
            user["voice_seconds"]
        ),

        inline=True

    )


    embed.add_field(

        name="💤 AFK time" if english else "💤 وقت AFK",

        value=format_seconds(
            user["afk_seconds"]
        ),

        inline=True

    )


    embed.add_field(

        name="🏅 Currency" if english else "🏅 العملة",

        value=(

            f"{currency_symbol} "
            f"{currency_name}"

        ),

        inline=True

    )


    return embed


# ============================================================
# BALANCE EMBED
# ============================================================

def balance_embed(
    user,
    currency_name,
    currency_symbol,
    language="ar"
):

    english = language == "en"

    embed = create_embed(

        "🪙 Your Balance" if english else "🪙 رصيدك",

        (
            f"You have **{user['coins']}** {currency_symbol}\n\n"
            f"Currency: **{currency_name}**"
            if english else
            f"لديك **{user['coins']}** {currency_symbol}\n\n"
            f"العملة: **{currency_name}**"
        ),

        COLOR_GOLD

    )


    return embed


# ============================================================
# TOP EMBED
# ============================================================

def top_embed(
    users,
    guild,
    members,
    language="ar"
):

    english = language == "en"

    embed = create_embed(

        "🏆 Top 10",

        (
            "Top members by current balance."
            if english else "أعلى الأعضاء حسب الرصيد الحالي."
        ),

        COLOR_GOLD

    )


    medals = [

        "🥇",

        "🥈",

        "🥉",

    ]


    lines = []


    for index, user in enumerate(
        users
    ):

        member = members.get(
            user["user_id"]
        )


        if member:

            name = member.display_name

        else:

            name = (
                f"<@{user['user_id']}>"
            )


        if index < 3:

            rank = medals[index]

        else:

            rank = (
                f"**#{index + 1}**"
            )


        lines.append(

            f"{rank} "
            f"**{name}** — "
            f"{user['coins']} "
            f"{guild['currency_symbol']}"

        )


    if not lines:

        lines.append(
            "No members on the leaderboard yet." if english else "لا يوجد أعضاء في التوب حالياً."
        )


    embed.description = (
        "\n".join(lines)
    )


    embed.add_field(

        name="📊 Ranking" if english else "📊 الترتيب",

        value=(

            "Ranked by **coins**." if english else "يتم الترتيب حسب **الكوينز**."

        ),

        inline=False

    )


    return embed


# ============================================================
# TASK COMPLETED EMBED
# ============================================================

def task_completed_embed(
    task,
    currency_name,
    currency_symbol,
    next_task=None,
    next_task_number=None,
    total_tasks=None
):

    embed = create_embed(

        "🎉 تم إنجاز المهمة!",

        (

            f"أحسنت! أكملت مهمة:\n\n"

            f"**{task['name']}**\n\n"

            f"🎁 المكافأة: "
            f"**{task['reward']} "
            f"{currency_name} "
            f"{currency_symbol}**"

        ),

        COLOR_SUCCESS

    )


    # --------------------------------------------------------
    # NEXT TASK
    # --------------------------------------------------------

    if next_task:

        emoji = task_emoji(
            next_task.get(
                "type",
                ""
            )
        )


        if (
            next_task_number is not None
            and total_tasks is not None
        ):

            position = (
                f"{next_task_number}/{total_tasks}"
            )

        else:

            position = ""


        embed.add_field(

            name="🔓 المهمة التالية",

            value=(

                f"{emoji} **{next_task['name']}** "
                f"`{position}`\n"

                f"{next_task['description']}\n\n"

                f"🎁 المكافأة: "
                f"**{next_task['reward']} "
                f"{currency_name} "
                f"{currency_symbol}**"

            ),

            inline=False

        )


        embed.add_field(

            name="🚀 ابدأ الآن",

            value=(
                "استخدم `/tasks` لعرض تقدم المهمة الجديدة."
            ),

            inline=False

        )

    else:

        embed.add_field(

            name="🏆 اكتملت الفترة",

            value=(

                "🎊 **أكملت جميع مهام هذه الفترة!**\n"
                "انتظر بداية الفترة القادمة لمهام جديدة."

            ),

            inline=False

        )


    return embed


# ============================================================
# LEVEL UP EMBED
# ============================================================

def level_up_embed(
    member,
    old_level,
    new_level,
    mention=True,
    message=None
):

    mention_text = (

        member.mention

        if mention

        else member.display_name

    )


    default_message = (

        f"مبروك {mention_text}! 🔥\n\n"

        f"ارتفع مستواك من "
        f"**Level {old_level}** "
        f"إلى "
        f"**Level {new_level}** ⭐"

    )


    description = (

        message

        if message

        else default_message

    )


    # --------------------------------------------------------
    # استبدال المتغيرات في الرسالة المخصصة
    # --------------------------------------------------------

    description = description.replace(

        "{mention}",

        mention_text

    )


    description = description.replace(

        "{user}",

        member.display_name

    )


    description = description.replace(

        "{level}",

        str(
            new_level
        )

    )


    description = description.replace(

        "{old_level}",

        str(
            old_level
        )

    )


    embed = create_embed(

        "🎊 Level Up!",

        description,

        COLOR_LEVEL

    )


    embed.set_thumbnail(

        url=member.display_avatar.url

    )


    embed.add_field(

        name="⭐ المستوى الجديد",

        value=(

            f"**Level {new_level}**"

        ),

        inline=False

    )


    return embed


# ============================================================
# COINS ADDED EMBED
# ============================================================

def coins_added_embed(
    amount,
    reason,
    currency_name,
    currency_symbol
):

    embed = create_embed(

        "🪙 تمت إضافة المكافأة",

        (

            f"تمت إضافة:\n\n"

            f"**+{amount} "
            f"{currency_symbol}**\n\n"

            f"السبب: **{reason}**"

        ),

        COLOR_SUCCESS

    )


    embed.add_field(

        name="💰 العملة",

        value=currency_name,

        inline=False

    )


    return embed


# ============================================================
# COINS REMOVED EMBED
# ============================================================

def coins_removed_embed(
    amount,
    reason,
    currency_name,
    currency_symbol
):

    embed = create_embed(

        "🪙 تم خصم الكوينز",

        (

            f"تم خصم:\n\n"

            f"**-{amount} "
            f"{currency_symbol}**\n\n"

            f"السبب: **{reason}**"

        ),

        COLOR_WARNING

    )


    embed.add_field(

        name="💰 العملة",

        value=currency_name,

        inline=False

    )


    return embed


# ============================================================
# EXCHANGE EMBED
# ============================================================

def exchange_embed(
    currency,
    coins_spent,
    external_amount
):

    embed = create_embed(

        "💱 عملية تحويل",

        (

            "تم تنفيذ عملية التحويل بنجاح! 🎉"

        ),

        COLOR_SUCCESS

    )


    embed.add_field(

        name="🪙 الكوينز المستخدمة",

        value=(

            f"**{coins_spent}**"

        ),

        inline=True

    )


    embed.add_field(

        name="💰 العملة",

        value=(

            f"**{external_amount} "
            f"{currency['symbol']} "
            f"{currency['name']}**"

        ),

        inline=True

    )


    embed.add_field(

        name="📊 سعر التحويل",

        value=(

            f"{currency['coins_required']} "
            f"Coins = "

            f"{currency['external_amount']} "
            f"{currency['symbol']}"

        ),

        inline=False

    )


    return embed


# ============================================================
# ERROR EMBED
# ============================================================

def error_embed(
    title,
    description
):

    return create_embed(

        f"❌ {title}",

        description,

        COLOR_ERROR

    )


# ============================================================
# WARNING EMBED
# ============================================================

def warning_embed(
    title,
    description
):

    return create_embed(

        f"⚠️ {title}",

        description,

        COLOR_WARNING

    )


# ============================================================
# SUCCESS EMBED
# ============================================================

def success_embed(
    title,
    description
):

    return create_embed(

        f"✅ {title}",

        description,

        COLOR_SUCCESS

    )


# ============================================================
# SETUP EMBED
# ============================================================

def setup_embed(
    guild
):

    embed = create_embed(

        "⚙️ إعدادات Forge Tasks BOT",

        (

            "لوحة إعدادات السيرفر.\n\n"

            "استخدم أزرار وقوائم الإعدادات للتحكم "
            "في المهام والـXP والعملات والتنبيهات."

        ),

        COLOR_MAIN

    )


    embed.add_field(

        name="🌐 اللغة",

        value=(

            guild["language"]

            if guild["language"]

            else "ar"

        ),

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

        name="💬 روم الرسائل",

        value=(

            f"<#{guild['message_channel']}>"

            if guild["message_channel"]

            else "غير محدد"

        ),

        inline=True

    )


    embed.add_field(

        name="📋 روم المهام",

        value=(

            f"<#{guild['task_channel']}>"

            if guild["task_channel"]

            else "غير محدد"

        ),

        inline=True

    )


    embed.add_field(

        name="📝 روم السجلات",

        value=(

            f"<#{guild['log_channel']}>"

            if guild["log_channel"]

            else "غير محدد"

        ),

        inline=True

    )


    embed.add_field(

        name="📋 المهام",

        value=(

            f"☀️ يومية: "
            f"{'مفعلة' if guild['daily_enabled'] else 'معطلة'}\n"

            f"📅 أسبوعية: "
            f"{'مفعلة' if guild['weekly_enabled'] else 'معطلة'}\n"

            f"🌙 شهرية: "
            f"{'مفعلة' if guild['monthly_enabled'] else 'معطلة'}"

        ),

        inline=False

    )


    embed.add_field(

        name="✨ نظام XP",

        value=(

            "مفعل"

            if guild["xp_enabled"]

            else "معطل"

        ),

        inline=True

    )


    embed.add_field(

        name="🔔 التذكيرات",

        value=(

            "مفعلة"

            if guild["reminders_enabled"]

            else "معطلة"

        ),

        inline=True

    )


    embed.add_field(

        name="🎊 رسائل Level Up",

        value=(

            "مفعلة"

            if guild["level_up_enabled"]

            else "معطلة"

        ),

        inline=True

    )


    embed.add_field(

        name="📣 Mention عند Level Up",

        value=(

            "مفعل"

            if guild["level_up_mention"]

            else "معطل"

        ),

        inline=True

    )


    return embed


# ============================================================
# REMINDER EMBED
# ============================================================

def reminder_embed(
    tasks,
    currency_name,
    currency_symbol
):

    embed = create_embed(

        "🔔 تذكير بالمهمة",

        (

            "عندك مهمة لم تكتمل بعد! 👀\n"
            "أكملها للحصول على المكافأة."

        ),

        COLOR_WARNING

    )


    lines = []


    for task in tasks:

        if task.get(
            "completed"
        ):

            continue


        emoji = task_emoji(
            task.get(
                "type",
                ""
            )
        )


        lines.append(

            f"{emoji} **{task['name']}**\n"

            f"└ {task['description']}\n"

            f"└ {task['bar']} "
            f"`{task['progress']}/"
            f"{task['target']}`\n"

            f"└ 🎁 {task['reward']} "
            f"{currency_symbol}"

        )


    if not lines:

        embed.description = (
            "🎉 ما عندك مهمة ناقصة!"
        )

    else:

        embed.add_field(

            name="📋 المهمة الحالية",

            value="\n\n".join(
                lines
            ),

            inline=False

        )


    return embed


# ============================================================
# TASK UNLOCKED EMBED
# ============================================================

def task_unlocked_embed(
    task,
    currency_name,
    currency_symbol,
    task_number=None,
    total_tasks=None
):

    emoji = task_emoji(
        task.get(
            "type",
            ""
        )
    )


    if (
        task_number is not None
        and total_tasks is not None
    ):

        position = (
            f"المهمة {task_number}/{total_tasks}"
        )

    else:

        position = (
            "المهمة التالية"
        )


    embed = create_embed(

        "🔓 مهمة جديدة!",

        (

            f"تم فتح {position}!\n\n"

            f"{emoji} **{task['name']}**\n"

            f"{task['description']}"

        ),

        COLOR_MAIN

    )


    embed.add_field(

        name="🎁 المكافأة",

        value=(

            f"**{task['reward']} "
            f"{currency_symbol} "
            f"{currency_name}**"

        ),

        inline=True

    )


    embed.add_field(

        name="🚀 ابدأ الآن",

        value=get_task_start_text(
            task["type"]
        ),

        inline=False

    )


    return embed


# ============================================================
# ALL TASKS COMPLETED EMBED
# ============================================================

def all_tasks_completed_embed(
    period,
    currency_name,
    currency_symbol
):

    embed = create_embed(

        "🏆 اكتملت المهام!",

        (

            f"🎉 أكملت جميع "
            f"{period_name(period)}!\n\n"

            "أنجزت كل المهام المتاحة لهذه الفترة."

        ),

        COLOR_GOLD

    )


    embed.add_field(

        name="🎁 المكافآت",

        value=(

            f"تم جمع مكافآت المهام "
            f"بعملة **{currency_name} "
            f"{currency_symbol}**."

        ),

        inline=False

    )


    embed.add_field(

        name="⏳ ماذا بعد؟",

        value=(

            "انتظر بداية الفترة القادمة "
            "للحصول على مجموعة مهام جديدة."

        ),

        inline=False

    )


    return embed


# ============================================================
# SETUP SAVED EMBED
# ============================================================

def setup_saved_embed(
    setting_name,
    setting_value
):

    return success_embed(

        "تم حفظ الإعداد",

        (

            f"تم تحديث **{setting_name}** بنجاح.\n\n"

            f"القيمة الجديدة: **{setting_value}**"

        )

    )


# ============================================================
# FORMAT SECONDS
# ============================================================

def format_seconds(
    seconds
):

    seconds = max(
        0,
        int(seconds)
    )


    hours = seconds // 3600


    minutes = (
        seconds % 3600
    ) // 60


    remaining = (
        seconds % 60
    )


    if hours:

        return (

            f"{hours} ساعة "
            f"{minutes} دقيقة"

        )


    if minutes:

        return (

            f"{minutes} دقيقة "
            f"{remaining} ثانية"

        )


    return (

        f"{remaining} ثانية"

    )
