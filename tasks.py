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

    get_period_stats,

    is_task_completed,
    complete_task,

    get_task_state,
    set_task_index,
    advance_task_index,
    get_user_rank,
    get_custom_tasks,
)


# ============================================================
# TASK DEFINITIONS
# ============================================================

DAILY_TASKS = {

    "daily_messages": {
        "name": "إرسال 25 رسالة",
        "description": "أرسل 25 رسالة في روم المهام المحدد.",
        "type": "messages",
        "target": 25,
        "reward": 10,
    },

    "daily_afk": {
        "name": "البقاء في الصوت 10 دقائق",
        "description": "ادخل أي روم صوتي وابقَ فيه 10 دقائق.",
        "type": "afk",
        "target": 600,
        "reward": 20,
    },

    "daily_invites": {
        "name": "دعوة شخصين للسيرفر",
        "description": "ادعُ شخصين فعليًا عبر روابط دعوة صالحة.",
        "type": "invites",
        "target": 2,
        "reward": 20,
    },

    "daily_commands": {
        "name": "استعمال 5 أوامر",
        "description": "استخدم خمسة أوامر من أوامر البوت.",
        "type": "commands",
        "target": 5,
        "reward": 15,
    },

}


WEEKLY_TASKS = {

    "weekly_interactions": {
        "name": "التفاعل مع عضوين لمدة 5 دقائق",
        "description": "اذكر عضوين أو قم بالرد عليهما داخل السيرفر.",
        "type": "interactions",
        "target": 2,
        "reward": 30,
    },

    "weekly_invites": {
        "name": "دعوة 5 أشخاص بروابط مختلفة",
        "description": "اجعل خمسة أعضاء يدخلون عبر روابط دعوة مختلفة.",
        "type": "invites",
        "target": 5,
        "reward": 40,
    },

    "weekly_nickname": {
        "name": "تغيير الاسم المستعار 3 مرات",
        "description": "غيّر اسمك المستعار ثلاث مرات.",
        "type": "nickname",
        "target": 3,
        "reward": 20,
    },

    "weekly_voice": {
        "name": "التحدث في الصوت 8 دقائق",
        "description": "تكلم أو ابقَ متصلًا في أي روم صوتي 8 دقائق.",
        "type": "afk",
        "target": 480,
        "reward": 50,
    },

    "weekly_role": {
        "name": "امتلاك رتبة مخصصة",
        "description": "امتلك الرتبة التي يحددها الأدمن من إعدادات المهمة.",
        "type": "role",
        "target": 1,
        "reward": 30,
    },

}


# ============================================================
# MONTHLY TASKS
# ============================================================

# لا توجد مهام شهرية حاليًا.
# يمكن إضافة المهام لاحقًا بدون تغيير نظام المهام.

MONTHLY_TASKS = {
    "monthly_voice": {
        "name": "البقاء في الصوت 30 دقيقة",
        "description": "ادخل أي روم صوتي لمدة 30 دقيقة.",
        "type": "afk", "target": 1800, "reward": 60,
    },
    "monthly_invites": {
        "name": "دعوة 10 أشخاص مع رتبة",
        "description": "ادعُ عشرة أعضاء مع امتلاك الرتبة المخصصة.",
        "type": "invites_role", "target": 10, "reward": 50,
    },
    "monthly_interactions": {
        "name": "التفاعل مع 4 أشخاص 10 دقائق",
        "description": "اذكر أو رد على أربعة أعضاء في روم المهام.",
        "type": "interactions", "target": 4, "reward": 70,
    },
    "monthly_level15": {
        "name": "الوصول إلى Level 15",
        "description": "واصل اكتساب XP حتى تصل إلى المستوى 15.",
        "type": "level", "target": 15, "reward": 80,
    },
    "monthly_youtube": {
        "name": "مشاهدة مقطع لمدة 10 دقائق",
        "description": "شاهد الرابط الذي يحدده الأدمن لمدة 10 دقائق.",
        "type": "youtube", "target": 600, "reward": 100,
    },
    "monthly_top": {
        "name": "امتلاك المركز الأول",
        "description": "كن صاحب المركز الأول في ترتيب السيرفر.",
        "type": "top", "target": 1, "reward": 100,
    },
}


# ============================================================
# ALL TASK GROUPS
# ============================================================

TASK_GROUPS = {

    "daily": DAILY_TASKS,

    "weekly": WEEKLY_TASKS,

    "monthly": MONTHLY_TASKS,

}


# ============================================================
# TASK ORDER
# ============================================================

# ترتيب المهام مهم جدًا.
#
# العضو لا يستطيع تنفيذ المهمة الثانية
# إلا بعد إكمال المهمة الأولى.
#
# وبعد إكمال المهمة الحالية يتم فتح التالية تلقائيًا.

TASK_ORDER = {

    "daily": list(DAILY_TASKS.keys()),

    "weekly": list(WEEKLY_TASKS.keys()),

    "monthly": list(MONTHLY_TASKS.keys()),

}


def _custom_task_dict(row):
    return {
        "name": row["name"],
        "description": row["description"],
        "type": row["task_type"],
        "target": row["target"],
        "reward": row["reward"],
        "role_id": row["role_id"],
        "channel_id": row["channel_id"],
        "url": row["url"],
        "guild_id": row["guild_id"],
    }


def register_custom_task(row):
    period = row["period"]
    TASK_GROUPS.setdefault(period, {})[row["task_key"]] = _custom_task_dict(row)
    TASK_ORDER.setdefault(period, [])
    if row["task_key"] not in TASK_ORDER[period]:
        TASK_ORDER[period].append(row["task_key"])


for _custom_row in get_custom_tasks():
    register_custom_task(_custom_row)


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
# GET TASK ORDER
# ============================================================

def get_task_order(
    period
):

    return TASK_ORDER.get(
        period,
        []
    )


# ============================================================
# GET CURRENT TASK INDEX
# ============================================================

def get_current_task_index(
    guild_id,
    user_id,
    period
):

    state = get_task_state(
        guild_id,
        user_id,
        period
    )

    if not state:

        return 0

    return int(
        state["current_index"] or 0
    )


# ============================================================
# GET ACTIVE TASK ID
# ============================================================

def get_active_task_id(
    guild_id,
    user_id,
    period
):

    if not is_period_enabled(
        guild_id,
        period
    ):

        return None


    order = get_task_order(
        period
    )

    if not order:

        return None


    current_index = get_current_task_index(
        guild_id,
        user_id,
        period
    )


    if current_index >= len(order):

        return None


    return order[
        current_index
    ]


# ============================================================
# GET ACTIVE TASK
# ============================================================

def get_active_task(
    guild_id,
    user_id,
    period
):

    task_id = get_active_task_id(
        guild_id,
        user_id,
        period
    )

    if not task_id:

        return None


    return get_task(
        task_id,
        period
    )


# ============================================================
# PERIOD ENABLED
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
# PERIOD HAS TASKS
# ============================================================

def period_has_tasks(
    period
):

    return bool(
        get_task_order(
            period
        )
    )


# ============================================================
# ALL TASKS COMPLETED
# ============================================================

def all_tasks_completed(
    guild_id,
    user_id,
    period
):

    order = get_task_order(
        period
    )

    if not order:

        return True


    current_index = get_current_task_index(
        guild_id,
        user_id,
        period
    )


    return (
        current_index >= len(order)
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


    active_task_id = get_active_task_id(
        guild_id,
        user_id,
        period
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

        "active": (
            active_task_id == task_id
        ),

    }


# ============================================================
# ACTIVE TASK STATUS
# ============================================================

def get_active_task_status(
    guild_id,
    user_id,
    period
):

    task_id = get_active_task_id(
        guild_id,
        user_id,
        period
    )


    if not task_id:

        return None


    return get_task_status(
        guild_id,
        user_id,
        task_id,
        period
    )


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
# GET PERIOD STAT VALUE
# ============================================================

def get_period_stat_value(
    guild_id,
    user_id,
    period,
    stat_name
):

    stats = get_period_stats(
        guild_id,
        user_id,
        period
    )


    if not stats:

        return 0


    try:

        return int(
            stats[stat_name] or 0
        )

    except (
        KeyError,
        TypeError,
        ValueError
    ):

        return 0


# ============================================================
# GET TASK PROGRESS FROM CURRENT STATS
# ============================================================

def calculate_task_progress(
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

        return 0


    task_type = task["type"]


    # ----------------------------------------
    # MESSAGES
    # ----------------------------------------

    if task_type == "messages":

        return get_period_stat_value(
            guild_id,
            user_id,
            period,
            "messages"
        )


    # ----------------------------------------
    # IMAGES
    # ----------------------------------------

    if task_type == "images":

        return get_period_stat_value(
            guild_id,
            user_id,
            period,
            "images"
        )


    # ----------------------------------------
    # INVITES
    # ----------------------------------------

    if task_type == "invites":
        stat_name = "unique_invites" if period == "weekly" else "invites"
        return get_period_stat_value(
            guild_id,
            user_id,
            period,
            stat_name
        )

    if task_type == "invites_role":
        return get_period_stat_value(guild_id, user_id, period, "invites")

    if task_type == "commands":
        return get_period_stat_value(guild_id, user_id, period, "commands_used")

    if task_type in ("interactions", "interaction"):
        return get_period_stat_value(guild_id, user_id, period, "interaction_count")

    if task_type == "youtube":
        return get_period_stat_value(guild_id, user_id, period, "youtube_seconds")

    if task_type == "top":
        return 1 if get_user_rank(guild_id, user_id) == 1 else 0

    if task_type == "role":
        return 0


    # ----------------------------------------
    # VOICE / AFK
    # ----------------------------------------

    if task_type == "afk":

        return get_period_stat_value(
            guild_id,
            user_id,
            period,
            "voice_seconds"
        )


    # ----------------------------------------
    # NICKNAME
    # ----------------------------------------

    if task_type == "nickname":

        return get_period_stat_value(
            guild_id,
            user_id,
            period,
            "nickname_changes"
        )


    # ----------------------------------------
    # LEVEL
    # ----------------------------------------

    if task_type == "level":

        user = get_user(
            guild_id,
            user_id
        )


        if not user:

            return 0


        return int(
            user["level"] or 1
        )


    return 0


# ============================================================
# SYNC ACTIVE TASK PROGRESS
# ============================================================

def sync_active_task_progress(
    guild_id,
    user_id,
    period
):

    task_id = get_active_task_id(
        guild_id,
        user_id,
        period
    )


    if not task_id:

        return {

            "success": False,

            "reason": "no_active_task",

            "period": period,

        }


    task = get_task(
        task_id,
        period
    )


    if not task:

        return {

            "success": False,

            "reason": "task_not_found",

            "period": period,

        }


    progress = calculate_task_progress(
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
        progress
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

            "completed": False,

        }


    if not is_period_enabled(
        guild_id,
        period
    ):

        return {

            "success": False,

            "reason": "period_disabled",

            "completed": False,

        }


    active_task_id = get_active_task_id(
        guild_id,
        user_id,
        period
    )


    # --------------------------------------------------------
    # لا نسمح بتقدم مهمة ليست المهمة النشطة.
    # --------------------------------------------------------

    if active_task_id != task_id:

        return {

            "success": False,

            "reason": "task_not_active",

            "completed": False,

            "active_task_id": active_task_id,

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

            "completed": True,

            "task": task,

        }


    target = int(
        task["target"]
    )


    try:

        progress = int(
            progress
        )

    except (
        TypeError,
        ValueError
    ):

        progress = 0


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


    # --------------------------------------------------------
    # COMPLETE TASK
    # --------------------------------------------------------

    if progress >= target:

        completed = complete_task(
            guild_id,
            user_id,
            task_id,
            period,
            task["reward"]
        )


        # ----------------------------------------------------
        # فتح المهمة التالية تلقائيًا.
        # ----------------------------------------------------

        if completed:

            advance_task_index(
                guild_id,
                user_id,
                period
            )


    percentage = 100

    if target > 0:

        percentage = int(
            min(
                progress / target,
                1
            ) * 100
        )


    next_task_id = get_active_task_id(
        guild_id,
        user_id,
        period
    )

    next_task = get_task(next_task_id, period) if next_task_id else None
    next_task_number = None
    if next_task_id:
        next_task_number = get_current_task_index(guild_id, user_id, period) + 1


    return {

        "success": True,

        "completed": completed,

        "task": task,

        "task_id": task_id,

        "period": period,

        "progress": progress,

        "target": target,

        "reward": task["reward"],

        "percentage": percentage,

        "next_task_id": next_task_id,

        "next_task": next_task,

        "next_task_number": next_task_number,

        "total_tasks": len(get_task_order(period)),

        "all_completed": (
            next_task_id is None
        ),

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
# PROCESS ACTIVE MESSAGE TASK
# ============================================================

def process_message_tasks(
    guild_id,
    user_id,
    message_channel_id=None
):

    results = []


    # --------------------------------------------------------
    # DAILY + WEEKLY
    # --------------------------------------------------------

    for period in (
        "daily",
        "weekly",
    ):

        task_id = get_active_task_id(
            guild_id,
            user_id,
            period
        )


        if not task_id:

            continue


        task = get_task(
            task_id,
            period
        )


        if not task:

            continue


        if task["type"] != "messages":

            continue


        guild = get_guild(
            guild_id
        )


        if not guild:

            continue


        allowed_channel = guild[
            "message_channel"
        ]


        # ----------------------------------------------------
        # إذا تم تحديد روم للرسائل،
        # يجب أن تكون الرسالة داخله.
        # ----------------------------------------------------

        if (
            allowed_channel is not None
            and message_channel_id != allowed_channel
        ):

            continue


        result = sync_active_task_progress(
            guild_id,
            user_id,
            period
        )


        results.append(
            result
        )


    return results


# ============================================================
# PROCESS ACTIVE IMAGE TASK
# ============================================================

def process_image_tasks(
    guild_id,
    user_id
):

    results = []


    for period in (
        "daily",
        "weekly",
    ):

        task_id = get_active_task_id(
            guild_id,
            user_id,
            period
        )


        if not task_id:

            continue


        task = get_task(
            task_id,
            period
        )


        if not task:

            continue


        if task["type"] != "images":

            continue


        result = sync_active_task_progress(
            guild_id,
            user_id,
            period
        )


        results.append(
            result
        )


    return results


# ============================================================
# PROCESS ACTIVE INVITE TASK
# ============================================================

def process_invite_tasks(
    guild_id,
    user_id,
    member=None
):

    results = []


    for period in ("daily", "weekly", "monthly"):

        task_id = get_active_task_id(
            guild_id,
            user_id,
            period
        )


        if not task_id:

            continue


        task = get_task(
            task_id,
            period
        )


        if not task:

            continue


        if task["type"] not in ("invites", "invites_role"):

            continue

        if task["type"] == "invites_role":
            role_id = task.get("role_id")
            if role_id and (not member or not any(role.id == int(role_id) for role in member.roles)):
                continue


        result = sync_active_task_progress(
            guild_id,
            user_id,
            period
        )


        results.append(
            result
        )


    return results


# ============================================================
# PROCESS ACTIVE VOICE / AFK TASK
# ============================================================

def process_voice_tasks(
    guild_id,
    user_id
):

    results = []


    for period in ("daily", "weekly", "monthly"):

        task_id = get_active_task_id(
            guild_id,
            user_id,
            period
        )


        if not task_id:

            continue


        task = get_task(
            task_id,
            period
        )


        if not task:

            continue


        if task["type"] != "afk":

            continue


        # ----------------------------------------------------
        # مهم:
        #
        # هذه المهمة تعتمد على وقت البقاء في الروم الصوتي.
        #
        # لم نحذف نظام Voice / AFK Task.
        # ----------------------------------------------------

        result = sync_active_task_progress(
            guild_id,
            user_id,
            period
        )


        results.append(
            result
        )


    return results


# ============================================================
# PROCESS LEVEL TASK
# ============================================================

def process_level_tasks(
    guild_id,
    user_id,
    period=None
):

    periods = (period,) if period else ("daily",)
    output = []
    for current_period in periods:
        result = _process_level_task_for_period(guild_id, user_id, current_period)
        if result.get("success"):
            output.append(result)
    if period:
        return output[0] if output else {"success": False, "completed": False, "reason": "no_active_task"}
    return output


def _process_level_task_for_period(guild_id, user_id, period):


    task_id = get_active_task_id(
        guild_id,
        user_id,
        period
    )


    if not task_id:

        return {

            "success": False,

            "reason": "no_active_task",

            "completed": False,

        }


    task = get_task(
        task_id,
        period
    )


    if not task:

        return {

            "success": False,

            "reason": "task_not_found",

            "completed": False,

        }


    if task["type"] != "level":

        return {

            "success": False,

            "reason": "task_not_level",

            "completed": False,

        }


    return sync_active_task_progress(
        guild_id,
        user_id,
        period
    )


# ============================================================
# PROCESS NICKNAME TASK
# ============================================================

def process_nickname_task(
    guild_id,
    user_id
):

    period = "weekly"


    task_id = get_active_task_id(
        guild_id,
        user_id,
        period
    )


    if not task_id:

        return {

            "success": False,

            "reason": "no_active_task",

            "completed": False,

        }


    task = get_task(
        task_id,
        period
    )


    if not task:

        return {

            "success": False,

            "reason": "task_not_found",

            "completed": False,

        }


    if task["type"] != "nickname":

        return {

            "success": False,

            "reason": "task_not_nickname",

            "completed": False,

        }


    return sync_active_task_progress(
        guild_id,
        user_id,
        period
    )


def process_command_tasks(guild_id, user_id):
    results = []
    task_id = get_active_task_id(guild_id, user_id, "daily")
    task = get_task(task_id, "daily") if task_id else None
    if task and task["type"] == "commands":
        results.append(sync_active_task_progress(guild_id, user_id, "daily"))
    return results


def process_interaction_tasks(guild_id, user_id):
    results = []
    for period in ("weekly", "monthly"):
        task_id = get_active_task_id(guild_id, user_id, period)
        task = get_task(task_id, period) if task_id else None
        if task and task["type"] in ("interactions", "interaction"):
            results.append(sync_active_task_progress(guild_id, user_id, period))
    return results


def process_top_tasks(guild_id, user_id):
    task_id = get_active_task_id(guild_id, user_id, "monthly")
    task = get_task(task_id, "monthly") if task_id else None
    if task and task["type"] == "top":
        return [sync_active_task_progress(guild_id, user_id, "monthly")]
    return []


def process_role_task(guild_id, user_id, member):
    results = []
    for period in ("weekly", "monthly"):
        task_id = get_active_task_id(guild_id, user_id, period)
        task = get_task(task_id, period) if task_id else None
        if not task or task["type"] != "role" or not task.get("role_id"):
            continue
        if any(role.id == int(task["role_id"]) for role in member.roles):
            results.append(update_task(guild_id, user_id, task_id, period, 1))
    return results


# ============================================================
# PROCESS ALL TASKS
# ============================================================

def process_all_tasks(
    guild_id,
    user_id
):

    results = []


    # --------------------------------------------------------
    # MESSAGE TASKS
    # --------------------------------------------------------

    results.extend(
        process_message_tasks(
            guild_id,
            user_id
        )
    )


    # --------------------------------------------------------
    # IMAGE TASKS
    # --------------------------------------------------------

    results.extend(
        process_image_tasks(
            guild_id,
            user_id
        )
    )


    # --------------------------------------------------------
    # INVITE TASKS
    # --------------------------------------------------------

    results.extend(
        process_invite_tasks(
            guild_id,
            user_id
        )
    )


    # --------------------------------------------------------
    # VOICE TASKS
    # --------------------------------------------------------

    results.extend(
        process_voice_tasks(
            guild_id,
            user_id
        )
    )


    # --------------------------------------------------------
    # LEVEL TASK
    # --------------------------------------------------------

    level_result = process_level_tasks(
        guild_id,
        user_id
    )


    if level_result.get(
        "success"
    ):

        results.append(
            level_result
        )


    # --------------------------------------------------------
    # NICKNAME TASK
    # --------------------------------------------------------

    nickname_result = process_nickname_task(
        guild_id,
        user_id
    )


    if nickname_result.get(
        "success"
    ):

        results.append(
            nickname_result
        )


    return results


# ============================================================
# GET ACTIVE TASK DISPLAY
# ============================================================

def get_active_task_display(
    guild_id,
    user_id,
    period
):

    if not is_period_enabled(
        guild_id,
        period
    ):

        return {

            "available": False,

            "reason": "period_disabled",

            "period": period,

        }


    task_id = get_active_task_id(
        guild_id,
        user_id,
        period
    )


    if not task_id:

        return {

            "available": False,

            "reason": "all_completed",

            "period": period,

        }


    status = get_active_task_status(
        guild_id,
        user_id,
        period
    )


    if not status:

        return {

            "available": False,

            "reason": "task_not_found",

            "period": period,

        }


    bar = progress_bar(
        status["progress"],
        status["target"]
    )


    current_index = get_current_task_index(
        guild_id,
        user_id,
        period
    )


    total_tasks = len(
        get_task_order(
            period
        )
    )


    return {

        "available": True,

        "period": period,

        "task_number": current_index + 1,

        "total_tasks": total_tasks,

        "id": status["id"],

        "name": status["name"],

        "description": status["description"],

        "type": status["type"],

        "progress": status["progress"],

        "target": status["target"],

        "reward": status["reward"],

        "percentage": status["percentage"],

        "bar": bar,

        "completed": status["completed"],

        "active": True,

    }


# ============================================================
# GET TASK DISPLAY
# ============================================================

def get_task_display(
    guild_id,
    user_id,
    period
):

    active = get_active_task_display(
        guild_id,
        user_id,
        period
    )


    if not active.get(
        "available"
    ):

        return []


    return [
        active
    ]


# ============================================================
# GET ALL ACTIVE PERIOD TASKS
# ============================================================

def get_all_active_tasks(
    guild_id,
    user_id
):

    output = []


    for period in (
        "daily",
        "weekly",
        "monthly",
    ):

        display = get_active_task_display(
            guild_id,
            user_id,
            period
        )


        if display.get(
            "available"
        ):

            output.append(
                display
            )


    return output


# ============================================================
# GET TASK START INFORMATION
# ============================================================

def get_task_start_info(
    guild_id,
    user_id,
    period
):

    display = get_active_task_display(
        guild_id,
        user_id,
        period
    )


    if not display.get(
        "available"
    ):

        return display


    task_type = display[
        "type"
    ]


    instructions = {

        "messages": (
            "ابدأ بإرسال الرسائل في الروم المحدد."
        ),

        "images": (
            "ابدأ بإرسال الصور حتى تصل للعدد المطلوب."
        ),

        "invites": (
            "ابدأ بدعوة أعضاء جدد إلى السيرفر."
        ),

        "afk": (
            "ادخل أي روم صوتي وابقَ فيه حتى يكتمل الوقت المطلوب."
        ),

        "level": (
            "استمر في اكتساب XP حتى تصل إلى المستوى المطلوب."
        ),

        "nickname": (
            "غيّر اسمك المستعار في السيرفر مرة واحدة."
        ),

    }


    display[
        "start_instruction"
    ] = instructions.get(
        task_type,
        "ابدأ بتنفيذ المهمة."
    )


    return display


# ============================================================
# GET NEXT TASK
# ============================================================

def get_next_task(
    guild_id,
    user_id,
    period
):

    order = get_task_order(
        period
    )


    if not order:

        return None


    current_index = get_current_task_index(
        guild_id,
        user_id,
        period
    )


    next_index = current_index + 1


    if next_index >= len(order):

        return None


    task_id = order[
        next_index
    ]


    return {

        "id": task_id,

        "task": get_task(
            task_id,
            period
        ),

        "index": next_index,

        "number": next_index + 1,

        "total": len(order),

    }


# ============================================================
# TASK COMPLETION SUMMARY
# ============================================================

def get_completion_summary(
    guild_id,
    user_id,
    period,
    completed_task_id
):

    completed_task = get_task(
        completed_task_id,
        period
    )


    if not completed_task:

        return {

            "success": False,

            "reason": "task_not_found",

        }


    next_task = get_active_task(
        guild_id,
        user_id,
        period
    )


    if next_task:

        next_task_id = get_active_task_id(
            guild_id,
            user_id,
            period
        )


        current_index = get_current_task_index(
            guild_id,
            user_id,
            period
        )


        return {

            "success": True,

            "completed": True,

            "completed_task_id": completed_task_id,

            "completed_task": completed_task,

            "reward": completed_task["reward"],

            "all_completed": False,

            "next_task_id": next_task_id,

            "next_task": next_task,

            "next_task_number": current_index + 1,

            "total_tasks": len(
                get_task_order(
                    period
                )
            ),

        }


    return {

        "success": True,

        "completed": True,

        "completed_task_id": completed_task_id,

        "completed_task": completed_task,

        "reward": completed_task["reward"],

        "all_completed": True,

        "next_task_id": None,

        "next_task": None,

        "next_task_number": None,

        "total_tasks": len(
            get_task_order(
                period
            )
        ),

    }


# ============================================================
# RESET TASK PERIOD
# ============================================================

def reset_task_period(
    guild_id,
    user_id,
    period
):

    order = get_task_order(
        period
    )


    # --------------------------------------------------------
    # إعادة مؤشر المهمة إلى أول مهمة.
    # --------------------------------------------------------

    set_task_index(
        guild_id,
        user_id,
        period,
        0
    )


    # --------------------------------------------------------
    # حذف تقدم المهام لهذه الفترة.
    # --------------------------------------------------------

    for task_id in order:

        set_task_progress(
            guild_id,
            user_id,
            task_id,
            period,
            0
        )


    return {

        "success": True,

        "period": period,

        "task_count": len(
            order
        ),

        "active_task_id": (
            order[0]
            if order
            else None
        ),

    }


# ============================================================
# TASK COUNT
# ============================================================

def get_task_count(
    period
):

    return len(
        get_task_order(
            period
        )
    )


# ============================================================
# TASK POSITION
# ============================================================

def get_task_position(
    guild_id,
    user_id,
    period
):

    order = get_task_order(
        period
    )


    current_index = get_current_task_index(
        guild_id,
        user_id,
        period
    )


    if current_index >= len(order):

        return {

            "current": None,

            "number": len(order),

            "total": len(order),

            "completed_all": True,

        }


    return {

        "current": order[
            current_index
        ],

        "number": current_index + 1,

        "total": len(order),

        "completed_all": False,

    }


# ============================================================
# TASK SYSTEM HEALTH
# ============================================================

def get_task_system_status(
    guild_id,
    user_id
):

    periods = {}


    for period in (
        "daily",
        "weekly",
        "monthly",
    ):

        order = get_task_order(
            period
        )


        active_id = get_active_task_id(
            guild_id,
            user_id,
            period
        )


        periods[
            period
        ] = {

            "enabled": is_period_enabled(
                guild_id,
                period
            ),

            "task_count": len(
                order
            ),

            "active_task": active_id,

            "all_completed": (
                active_id is None
                and bool(order)
            ),

        }


    return periods
