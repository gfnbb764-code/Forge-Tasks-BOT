# ============================================================
# TASK BOT — TASKS.PY
# Task System / Progress / Rewards
# Python 3.11+
# ============================================================

from database import (
    get_user,
    get_guild,
    get_task_progress,
    set_task_progress,
    is_task_completed,
    complete_task,
    add_xp,
)


# ============================================================
# TASK DEFINITIONS
# ============================================================

DAILY_TASKS = {

    "daily_messages": {
        "name": "إرسال 50 رسالة",
        "description": "أرسل 50 رسالة في الروم المحدد.",
        "type": "messages",
        "target": 50,
        "reward": 10,
    },

    "daily_invites": {
        "name": "دعوة 3 أشخاص",
        "description": "ادعُ 3 أشخاص إلى السيرفر.",
        "type": "invites",
        "target": 3,
        "reward": 20,
    },

    "daily_afk": {
        "name": "AFK لمدة 30 دقيقة",
        "description": "ابقَ في روم صوتي لمدة 30 دقيقة.",
        "type": "afk",
        "target": 1800,
        "reward": 30,
    },

    "daily_level5": {
        "name": "الوصول إلى Level 5",
        "description": "وصل إلى المستوى الخامس.",
        "type": "level",
        "target": 5,
        "reward": 50,
    },

    "daily_images": {
        "name": "إرسال 10 صور",
        "description": "أرسل 10 صور.",
        "type": "images",
        "target": 10,
        "reward": 20,
    },

}


WEEKLY_TASKS = {

    "weekly_afk": {
        "name": "AFK لمدة ساعة",
        "description": "ابقَ في روم صوتي لمدة ساعة.",
        "type": "afk",
        "target": 3600,
        "reward": 30,
    },

    "weekly_messages": {
        "name": "إرسال 200 رسالة",
        "description": "أرسل 200 رسالة في الروم المحدد.",
        "type": "messages",
        "target": 200,
        "reward": 50,
    },

    "weekly_invites": {
        "name": "دعوة 10 أشخاص",
        "description": "ادعُ 10 أشخاص للسيرفر.",
        "type": "invites",
        "target": 10,
        "reward": 70,
    },

    "weekly_images": {
        "name": "إرسال 30 صورة",
        "description": "أرسل 30 صورة.",
        "type": "images",
        "target": 30,
        "reward": 50,
    },

    "weekly_nickname": {
        "name": "تغيير الاسم المستعار",
        "description": "غيّر اسمك المستعار.",
        "type": "nickname",
        "target": 1,
        "reward": 20,
    },

}


# ============================================================
# MONTHLY TASKS
# ============================================================

# لا توجد مهام شهرية حالياً.
# نضيفها لاحقاً بدون تغيير النظام.

MONTHLY_TASKS = {}


# ============================================================
# ALL TASKS
# ============================================================

TASK_GROUPS = {

    "daily": DAILY_TASKS,

    "weekly": WEEKLY_TASKS,

    "monthly": MONTHLY_TASKS,

}


# ============================================================
# GET TASK
# ============================================================

def get_task(
    task_id,
    period=None
):

    if period:

        return TASK_GROUPS.get(
            period,
            {}
        ).get(task_id)


    for tasks in TASK_GROUPS.values():

        if task_id in tasks:

            return tasks[task_id]

    return None


# ============================================================
# GET ALL TASKS
# ============================================================

def get_all_tasks(
    period
):

    return TASK_GROUPS.get(
        period,
        {}
    )


# ============================================================
# TASK ENABLED
# ============================================================

def is_period_enabled(
    guild_id,
    period
):

    guild = get_guild(
        guild_id
    )

    if not guild:

        return False


    settings = {

        "daily": "daily_enabled",

        "weekly": "weekly_enabled",

        "monthly": "monthly_enabled",

    }


    setting = settings.get(
        period
    )

    if not setting:

        return False


    return bool(
        guild[setting]
    )


# ============================================================
# TASK STATUS
# ============================================================

def get_task_status(
    guild_id,
    user_id,
    task_id,
    period
):

    task = get_task(
        task_id,
        period
    )

    if not task:

        return None


    completed = is_task_completed(
        guild_id,
        user_id,
        task_id,
        period
    )


    progress = get_task_progress(
        guild_id,
        user_id,
        task_id,
        period
    )


    target = task["target"]


    percentage = 0

    if target > 0:

        percentage = int(
            min(
                progress / target,
                1
            ) * 100
        )


    return {

        "id": task_id,

        "name": task["name"],

        "description": task["description"],

        "type": task["type"],

        "progress": progress,

        "target": target,

        "reward": task["reward"],

        "percentage": percentage,

        "completed": completed,

    }


# ============================================================
# PROGRESS BAR
# ============================================================

def progress_bar(
    progress,
    target,
    size=10
):

    if target <= 0:

        return "🟦" * size


    percentage = min(
        progress / target,
        1
    )


    filled = int(
        percentage * size
    )


    empty = (
        size -
        filled
    )


    return (
        "🟦" * filled +
        "⬜" * empty
    )


# ============================================================
# UPDATE TASK
# ============================================================

def update_task(
    guild_id,
    user_id,
    task_id,
    period,
    progress
):

    task = get_task(
        task_id,
        period
    )

    if not task:

        return {

            "success": False,

            "reason": "task_not_found",

        }


    if not is_period_enabled(
        guild_id,
        period
    ):

        return {

            "success": False,

            "reason": "period_disabled",

        }


    if is_task_completed(
        guild_id,
        user_id,
        task_id,
        period
    ):

        return {

            "success": False,

            "reason": "already_completed",

        }


    target = task["target"]


    progress = max(
        0,
        progress
    )


    progress = min(
        progress,
        target
    )


    set_task_progress(
        guild_id,
        user_id,
        task_id,
        period,
        progress
    )


    completed = False


    if progress >= target:

        completed = complete_task(
            guild_id,
            user_id,
            task_id,
            period,
            task["reward"]
        )


    return {

        "success": True,

        "completed": completed,

        "task": task,

        "progress": progress,

        "target": target,

        "reward": task["reward"],

        "percentage": int(
            (progress / target) * 100
        ) if target else 100,

    }


# ============================================================
# INCREMENT TASK
# ============================================================

def increment_task(
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


    return update_task(
        guild_id,
        user_id,
        task_id,
        period,
        current + amount
    )


# ============================================================
# MESSAGE TASKS
# ============================================================

def process_message_tasks(
    guild_id,
    user_id,
    message_channel_id=None
):

    results = []


    # ----------------------------------------
    # DAILY
    # ----------------------------------------

    daily = get_task(
        "daily_messages",
        "daily"
    )


    if daily:

        guild = get_guild(
            guild_id
        )


        allowed_channel = guild[
            "message_channel"
        ]


        if (
            allowed_channel is None
            or message_channel_id == allowed_channel
        ):

            user = get_user(
                guild_id,
                user_id
            )


            result = update_task(
                guild_id,
                user_id,
                "daily_messages",
                "daily",
                user["messages"]
            )


            results.append(
                result
            )


    # ----------------------------------------
    # WEEKLY
    # ----------------------------------------

    weekly = get_task(
        "weekly_messages",
        "weekly"
    )


    if weekly:

        guild = get_guild(
            guild_id
        )


        allowed_channel = guild[
            "message_channel"
        ]


        if (
            allowed_channel is None
            or message_channel_id == allowed_channel
        ):

            user = get_user(
                guild_id,
                user_id
            )


            result = update_task(
                guild_id,
                user_id,
                "weekly_messages",
                "weekly",
                user["messages"]
            )


            results.append(
                result
            )


    return results


# ============================================================
# IMAGE TASKS
# ============================================================

def process_image_tasks(
    guild_id,
    user_id
):

    user = get_user(
        guild_id,
        user_id
    )


    results = []


    result = update_task(
        guild_id,
        user_id,
        "daily_images",
        "daily",
        user["images"]
    )


    results.append(
        result
    )


    result = update_task(
        guild_id,
        user_id,
        "weekly_images",
        "weekly",
        user["images"]
    )


    results.append(
        result
    )


    return results


# ============================================================
# INVITE TASKS
# ============================================================

def process_invite_tasks(
    guild_id,
    user_id
):

    user = get_user(
        guild_id,
        user_id
    )


    results = []


    result = update_task(
        guild_id,
        user_id,
        "daily_invites",
        "daily",
        user["invites"]
    )


    results.append(
        result
    )


    result = update_task(
        guild_id,
        user_id,
        "weekly_invites",
        "weekly",
        user["invites"]
    )


    results.append(
        result
    )


    return results


# ============================================================
# VOICE / AFK TASKS
# ============================================================

def process_voice_tasks(
    guild_id,
    user_id
):

    user = get_user(
        guild_id,
        user_id
    )


    results = []


    # ----------------------------------------
    # DAILY AFK
    # ----------------------------------------

    result = update_task(
        guild_id,
        user_id,
        "daily_afk",
        "daily",
        user["afk_seconds"]
    )


    results.append(
        result
    )


    # ----------------------------------------
    # WEEKLY AFK
    # ----------------------------------------

    result = update_task(
        guild_id,
        user_id,
        "weekly_afk",
        "weekly",
        user["afk_seconds"]
    )


    results.append(
        result
    )


    return results


# ============================================================
# LEVEL TASK
# ============================================================

def process_level_tasks(
    guild_id,
    user_id
):

    user = get_user(
        guild_id,
        user_id
    )


    result = update_task(
        guild_id,
        user_id,
        "daily_level5",
        "daily",
        user["level"]
    )


    return result


# ============================================================
# NICKNAME TASK
# ============================================================

def process_nickname_task(
    guild_id,
    user_id
):

    result = update_task(
        guild_id,
        user_id,
        "weekly_nickname",
        "weekly",
        1
    )


    return result


# ============================================================
# PROCESS ALL TASKS
# ============================================================

def process_all_tasks(
    guild_id,
    user_id
):

    results = []


    results.extend(
        process_message_tasks(
            guild_id,
            user_id
        )
    )


    results.extend(
        process_image_tasks(
            guild_id,
            user_id
        )
    )


    results.extend(
        process_invite_tasks(
            guild_id,
            user_id
        )
    )


    results.extend(
        process_voice_tasks(
            guild_id,
            user_id
        )
    )


    results.append(
        process_level_tasks(
            guild_id,
            user_id
        )
    )


    return results


# ============================================================
# TASK DISPLAY DATA
# ============================================================

def get_task_display(
    guild_id,
    user_id,
    period
):

    tasks = get_all_tasks(
        period
    )


    output = []


    for task_id, task in tasks.items():

        status = get_task_status(
            guild_id,
            user_id,
            task_id,
            period
        )


        if not status:

            continue


        bar = progress_bar(
            status["progress"],
            status["target"]
        )


        output.append({

            "id": task_id,

            "name": task["name"],

            "description": task["description"],

            "progress": status["progress"],

            "target": status["target"],

            "reward": status["reward"],

            "percentage": status["percentage"],

            "bar": bar,

            "completed": status["completed"],

        })


    return output
