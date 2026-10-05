import logging
import uuid
import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from database import (
    create_guild,
    get_guild,
    create_user,
    get_user,
    get_top_users,
    get_currency,
    exchange_coins,
    transfer_coins,
    update_guild_setting,
    required_xp,
    create_custom_task,
    update_custom_task,
    get_custom_task_by_name,
    get_custom_tasks,
    delete_custom_task,
    upsert_custom_task,
)

from tasks import get_all_tasks, register_custom_task, unregister_custom_task, TASK_GROUPS, get_active_task_display, advance_task_index

from embeds import (
    tasks_embed,
    profile_embed,
    balance_embed,
    top_embed,
    exchange_embed,
    setup_embed,
    active_task_embed,
    success_embed,
    error_embed,
)


# ============================================================
# HELPERS
# ============================================================

def setting_bool(
    value
):
    return str(value).lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def get_task_channel(
    guild,
    settings
):

    channel_id = settings.get(
        "task_channel"
    )

    if not channel_id:
        return None

    try:
        channel_id = int(
            channel_id
        )
    except (
        TypeError,
        ValueError
    ):
        return None

    channel = guild.get_channel(
        channel_id
    )

    if isinstance(
        channel,
        discord.TextChannel
    ):
        return channel

    return None


def get_log_channel(
    guild,
    settings
):

    channel_id = settings.get(
        "log_channel"
    )

    if not channel_id:
        return None

    try:
        channel_id = int(
            channel_id
        )
    except (
        TypeError,
        ValueError
    ):
        return None

    channel = guild.get_channel(
        channel_id
    )

    if isinstance(
        channel,
        discord.TextChannel
    ):
        return channel

    return None


class TasksDashboardView(discord.ui.View):

    def __init__(self, guild_id, user_id):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.user_id = user_id

    @discord.ui.button(label="تحديث التقدم", emoji="🔄", style=discord.ButtonStyle.primary)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("هذه اللوحة ليست لك.", ephemeral=True)
            return
        guild = get_guild(self.guild_id)
        embed = tasks_embed(
            self.guild_id,
            self.user_id,
            guild["currency_name"],
            guild["currency_symbol"],
            language=guild["language"],
        )

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="شرح النظام", emoji="📖", style=discord.ButtonStyle.secondary)
    async def explain(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "كل فترة تعمل بالتسلسل: أكمل المهمة الحالية لفتح التالية، وستصلك مكافأة وإشعار خاص عند الإكمال.",
            ephemeral=True,
        )


class TaskAvailabilityView(discord.ui.View):
    def __init__(self, guild_id, user_id, period):
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.user_id = user_id
        self.period = period

    @discord.ui.button(label="بدء المهمة", emoji="🚀", style=discord.ButtonStyle.success)
    async def start_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("هذه المهمة ليست لك.", ephemeral=True)
            return
        guild = get_guild(self.guild_id)
        embed = active_task_embed(self.guild_id, self.user_id, self.period,
                                  guild["currency_name"], guild["currency_symbol"])
        await interaction.response.edit_message(content=None, embed=embed, view=self)

    @discord.ui.button(label="تخطي", emoji="⏭️", style=discord.ButtonStyle.secondary)
    async def skip_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("هذه المهمة ليست لك.", ephemeral=True)
            return
        advance_task_index(self.guild_id, self.user_id, self.period)
        guild = get_guild(self.guild_id)
        display = get_active_task_display(self.guild_id, self.user_id, self.period)
        if not display.get("available"):
            await interaction.response.edit_message(content="لا توجد مهمة أخرى متاحة في هذه الفترة.", embed=None, view=None)
            return
        embed = active_task_embed(self.guild_id, self.user_id, self.period,
                                  guild["currency_name"], guild["currency_symbol"])
        await interaction.response.edit_message(content="تم تخطي المهمة وفتح المهمة التالية.", embed=embed, view=self)


async def custom_task_autocomplete(interaction: discord.Interaction, current: str):
    if not interaction.guild:
        return []
    current = current.casefold()
    rows = get_custom_tasks(interaction.guild.id)
    choices = [
        app_commands.Choice(
            name=f"{row['name']} ({row['period']})"[:100],
            value=row["name"],
        )
        for row in rows
        if row["task_type"] != "disabled" and (not current or current in row["name"].casefold())
    ]
    for period, tasks in TASK_GROUPS.items():
        for key, task in tasks.items():
            if key.startswith("custom_") or task["name"] in {choice.value for choice in choices}:
                continue
            if not current or current in task["name"].casefold():
                choices.append(app_commands.Choice(name=f"{task['name']} ({period})"[:100], value=task["name"]))
    return choices[:25]


async def administrator_only(interaction: discord.Interaction) -> bool:
    return bool(
        interaction.guild
        and interaction.user
        and interaction.user.guild_permissions.administrator
    )


def builtin_task_by_name(name):
    for period, tasks in TASK_GROUPS.items():
        for key, task in tasks.items():
            if not key.startswith("custom_") and task["name"] == name:
                return key, period, task
    return None


# ============================================================
# SETUP PANEL
# ============================================================

class SetupPanelView(
    discord.ui.View
):

    def __init__(
        self,
        manager,
        guild_id
    ):

        super().__init__(
            timeout=300
        )

        self.manager = manager
        self.guild_id = guild_id


    # ========================================================
    # LANGUAGE
    # ========================================================

    @discord.ui.select(
        placeholder="🌐 اختر لغة البوت",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label="العربية",
                value="ar",
                emoji="🇸🇦"
            ),
            discord.SelectOption(
                label="English",
                value="en",
                emoji="🇺🇸"
            ),
        ]
    )
    async def language_select(
        self,
        interaction: discord.Interaction,
        select: discord.ui.Select
    ):

        value = select.values[0]

        create_guild(
            self.guild_id
        )

        update_guild_setting(
            self.guild_id,
            "language",
            value
        )

        name = (
            "العربية"
            if value == "ar"
            else
            "English"
        )

        await interaction.response.send_message(
            embed=success_embed(
                "Language updated" if value == "en" else "تم تغيير اللغة",
                f"Bot language is now **{name}**."
                if value == "en" else
                f"لغة البوت الآن: **{name}**."
            ),
            ephemeral=True
        )


    # ========================================================
    # XP
    # ========================================================

    @discord.ui.button(
        label="XP: تشغيل/إيقاف",
        style=discord.ButtonStyle.primary,
        emoji="⭐",
        row=1
    )
    async def xp_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild = get_guild(
            self.guild_id
        )

        if not guild:
            create_guild(
                self.guild_id
            )
            guild = get_guild(
                self.guild_id
            )

        current = setting_bool(
            guild["xp_enabled"]
        )

        new_value = not current

        update_guild_setting(
            self.guild_id,
            "xp_enabled",
            "true"
            if new_value
            else
            "false"
        )

        state = (
            "تشغيل"
            if new_value
            else
            "إيقاف"
        )

        await interaction.response.send_message(
            embed=success_embed(
                "تم تحديث XP",
                f"نظام XP: **{state}**."
            ),
            ephemeral=True
        )


    # ========================================================
    # REMINDERS
    # ========================================================

    @discord.ui.button(
        label="التذكيرات",
        style=discord.ButtonStyle.secondary,
        emoji="🔔",
        row=1
    )
    async def reminders_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild = get_guild(
            self.guild_id
        )

        if not guild:
            create_guild(
                self.guild_id
            )
            guild = get_guild(
                self.guild_id
            )

        current = setting_bool(
            guild["reminders_enabled"]
        )

        new_value = not current

        update_guild_setting(
            self.guild_id,
            "reminders_enabled",
            "true"
            if new_value
            else
            "false"
        )

        state = (
            "تشغيل"
            if new_value
            else
            "إيقاف"
        )

        await interaction.response.send_message(
            embed=success_embed(
                "تم تحديث التذكيرات",
                f"تذكيرات المهام: **{state}**."
            ),
            ephemeral=True
        )


    # ========================================================
    # LEVEL UP
    # ========================================================

    @discord.ui.button(
        label="Level Up",
        style=discord.ButtonStyle.success,
        emoji="🎉",
        row=2
    )
    async def level_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild = get_guild(
            self.guild_id
        )

        if not guild:
            create_guild(
                self.guild_id
            )
            guild = get_guild(
                self.guild_id
            )

        current = setting_bool(
            guild["level_up_enabled"]
        )

        new_value = not current

        update_guild_setting(
            self.guild_id,
            "level_up_enabled",
            "true"
            if new_value
            else
            "false"
        )

        state = (
            "تشغيل"
            if new_value
            else
            "إيقاف"
        )

        await interaction.response.send_message(
            embed=success_embed(
                "تم تحديث Level Up",
                f"إشعارات Level Up: **{state}**."
            ),
            ephemeral=True
        )


    # ========================================================
    # LEVEL UP MENTION
    # ========================================================

    @discord.ui.button(
        label="Mention",
        style=discord.ButtonStyle.secondary,
        emoji="📢",
        row=2
    )
    async def mention_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild = get_guild(
            self.guild_id
        )

        if not guild:
            create_guild(
                self.guild_id
            )
            guild = get_guild(
                self.guild_id
            )

        current = setting_bool(
            guild["level_up_mention"]
        )

        new_value = not current

        update_guild_setting(
            self.guild_id,
            "level_up_mention",
            "true"
            if new_value
            else
            "false"
        )

        state = (
            "تشغيل"
            if new_value
            else
            "إيقاف"
        )

        await interaction.response.send_message(
            embed=success_embed(
                "تم تحديث Mention",
                f"منشن العضو عند Level Up: **{state}**."
            ),
            ephemeral=True
        )


    # ========================================================
    # REFRESH
    # ========================================================

    @discord.ui.button(
        label="تحديث",
        style=discord.ButtonStyle.secondary,
        emoji="🔄",
        row=3
    )
    async def refresh_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild = get_guild(
            self.guild_id
        )

        if not guild:
            await interaction.response.send_message(
                embed=error_embed(
                    "خطأ",
                    "تعذر تحميل إعدادات السيرفر."
                ),
                ephemeral=True
            )
            return

        embed = setup_embed(
            guild
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )


# ============================================================
# SETUP GROUP
# ============================================================

class SetupGroup(
    app_commands.Group
):

    def __init__(self):

        super().__init__(
            name="setup",
            description="إعدادات البوت وإدارة السيرفر"
        )


    # ========================================================
    # /setup panel
    # ========================================================

    @app_commands.command(
        name="panel",
        description="فتح لوحة إعدادات البوت التفاعلية"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def panel(
        self,
        interaction: discord.Interaction
    ):

        guild_id = interaction.guild.id

        create_guild(
            guild_id
        )

        guild = get_guild(
            guild_id
        )

        embed = setup_embed(
            guild
        )

        view = SetupPanelView(
            None,
            guild_id
        )

        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )


    # ========================================================
    # /setup language
    # ========================================================

    @app_commands.command(
        name="language",
        description="تغيير لغة البوت"
    )
    @app_commands.describe(
        language="لغة البوت"
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
            ),
        ]
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def language(
        self,
        interaction: discord.Interaction,
        language: app_commands.Choice[str]
    ):

        guild_id = interaction.guild.id

        create_guild(
            guild_id
        )

        update_guild_setting(
            guild_id,
            "language",
            language.value
        )

        await interaction.response.send_message(
            embed=success_embed(
                "Language updated" if language.value == "en" else "تم تغيير اللغة",
                f"Bot language changed to **{language.name}**."
                if language.value == "en" else
                f"تم تغيير لغة البوت إلى **{language.name}**."
            ),
            ephemeral=True
        )


    # ========================================================
    # /setup channel
    # ========================================================

    @app_commands.command(
        name="channel",
        description="تحديد روم المهام أو الإشعارات"
    )
    @app_commands.describe(
        channel_type="نوع الروم",
        channel="الروم المطلوب"
    )
    @app_commands.choices(
        channel_type=[
            app_commands.Choice(
                name="روم المهام",
                value="task_channel"
            ),
            app_commands.Choice(
                name="روم الإشعارات",
                value="log_channel"
            ),
            app_commands.Choice(
                name="روم الرسائل المطلوبة",
                value="message_channel"
            ),
        ]
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def channel(
        self,
        interaction: discord.Interaction,
        channel_type: app_commands.Choice[str],
        channel: discord.TextChannel
    ):

        guild_id = interaction.guild.id

        create_guild(
            guild_id
        )

        update_guild_setting(
            guild_id,
            channel_type.value,
            str(channel.id)
        )

        names = {
            "task_channel": "روم المهام",
            "log_channel": "روم الإشعارات",
            "message_channel": "روم الرسائل المطلوبة",
        }

        await interaction.response.send_message(
            embed=success_embed(
                "تم حفظ الإعداد",
                f"{names[channel_type.value]} أصبح {channel.mention}."
            ),
            ephemeral=True
        )


    # ========================================================
    # /setup xp
    # ========================================================

    @app_commands.command(
        name="xp",
        description="تفعيل أو تعطيل نظام الخبرة"
    )
    @app_commands.describe(
        enabled="تشغيل أو إيقاف XP"
    )
    @app_commands.choices(
        enabled=[
            app_commands.Choice(
                name="تشغيل",
                value="true"
            ),
            app_commands.Choice(
                name="إيقاف",
                value="false"
            ),
        ]
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def xp(
        self,
        interaction: discord.Interaction,
        enabled: app_commands.Choice[str]
    ):

        guild_id = interaction.guild.id

        create_guild(
            guild_id
        )

        update_guild_setting(
            guild_id,
            "xp_enabled",
            enabled.value
        )

        state = (
            "تشغيل"
            if enabled.value == "true"
            else
            "إيقاف"
        )

        await interaction.response.send_message(
            embed=success_embed(
                "تم تحديث XP",
                f"تم ضبط نظام الخبرة على **{state}**."
            ),
            ephemeral=True
        )


    # ========================================================
    # /setup reminders
    # ========================================================

    @app_commands.command(
        name="reminders",
        description="تفعيل أو تعطيل تذكيرات المهام"
    )
    @app_commands.describe(
        enabled="تشغيل أو إيقاف التذكيرات"
    )
    @app_commands.choices(
        enabled=[
            app_commands.Choice(
                name="تشغيل",
                value="true"
            ),
            app_commands.Choice(
                name="إيقاف",
                value="false"
            ),
        ]
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def reminders(
        self,
        interaction: discord.Interaction,
        enabled: app_commands.Choice[str]
    ):

        guild_id = interaction.guild.id

        create_guild(
            guild_id
        )

        update_guild_setting(
            guild_id,
            "reminders_enabled",
            enabled.value
        )

        state = (
            "تشغيل"
            if enabled.value == "true"
            else
            "إيقاف"
        )

        await interaction.response.send_message(
            embed=success_embed(
                "تم تحديث التذكيرات",
                f"تذكيرات المهام: **{state}**."
            ),
            ephemeral=True
        )


    # ========================================================
    # /setup levelup
    # ========================================================

    @app_commands.command(
        name="levelup",
        description="إعداد إشعارات رفع المستوى"
    )
    @app_commands.describe(
        enabled="تفعيل إشعار Level Up",
        mention="منشن العضو",
        message="رسالة Level Up المخصصة"
    )
    @app_commands.choices(
        enabled=[
            app_commands.Choice(
                name="تشغيل",
                value="true"
            ),
            app_commands.Choice(
                name="إيقاف",
                value="false"
            ),
        ],
        mention=[
            app_commands.Choice(
                name="تشغيل",
                value="true"
            ),
            app_commands.Choice(
                name="إيقاف",
                value="false"
            ),
        ]
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def levelup(
        self,
        interaction: discord.Interaction,
        enabled: app_commands.Choice[str],
        mention: app_commands.Choice[str],
        message: str | None = None
    ):

        guild_id = interaction.guild.id

        create_guild(
            guild_id
        )

        update_guild_setting(
            guild_id,
            "level_up_enabled",
            enabled.value
        )

        update_guild_setting(
            guild_id,
            "level_up_mention",
            mention.value
        )

        if message is not None:

            update_guild_setting(
                guild_id,
                "level_up_message",
                message
            )

        await interaction.response.send_message(
            embed=success_embed(
                "تم تحديث Level Up",
                (
                    f"الإشعارات: **{'تشغيل' if enabled.value == 'true' else 'إيقاف'}**\n"
                    f"المنشن: **{'تشغيل' if mention.value == 'true' else 'إيقاف'}**"
                )
            ),
            ephemeral=True
        )


    # ========================================================
    # /setup currency
    # ========================================================

    @app_commands.command(
        name="currency",
        description="تغيير اسم ورمز عملة السيرفر"
    )
    @app_commands.describe(
        name="اسم العملة",
        symbol="رمز أو إيموجي العملة"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def currency(
        self,
        interaction: discord.Interaction,
        name: str,
        symbol: str
    ):

        guild_id = interaction.guild.id

        create_guild(
            guild_id
        )

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

        await interaction.response.send_message(
            embed=success_embed(
                "تم تحديث العملة",
                (
                    f"اسم العملة: **{name}**\n"
                    f"الرمز: **{symbol}**"
                )
            ),
            ephemeral=True
        )


    # ========================================================
    # /setup periods
    # ========================================================

    @app_commands.command(
        name="periods",
        description="تفعيل أو تعطيل فترات المهام"
    )
    @app_commands.describe(
        daily="المهام اليومية",
        weekly="المهام الأسبوعية",
        monthly="المهام الشهرية"
    )
    @app_commands.choices(
        daily=[
            app_commands.Choice(
                name="تشغيل",
                value="true"
            ),
            app_commands.Choice(
                name="إيقاف",
                value="false"
            ),
        ],
        weekly=[
            app_commands.Choice(
                name="تشغيل",
                value="true"
            ),
            app_commands.Choice(
                name="إيقاف",
                value="false"
            ),
        ],
        monthly=[
            app_commands.Choice(
                name="تشغيل",
                value="true"
            ),
            app_commands.Choice(
                name="إيقاف",
                value="false"
            ),
        ]
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def periods(
        self,
        interaction: discord.Interaction,
        daily: app_commands.Choice[str],
        weekly: app_commands.Choice[str],
        monthly: app_commands.Choice[str]
    ):

        guild_id = interaction.guild.id

        create_guild(
            guild_id
        )

        update_guild_setting(
            guild_id,
            "daily_enabled",
            daily.value
        )

        update_guild_setting(
            guild_id,
            "weekly_enabled",
            weekly.value
        )

        update_guild_setting(
            guild_id,
            "monthly_enabled",
            monthly.value
        )

        await interaction.response.send_message(
            embed=success_embed(
                "تم تحديث الفترات",
                (
                    f"يومي: **{'تشغيل' if daily.value == 'true' else 'إيقاف'}**\n"
                    f"أسبوعي: **{'تشغيل' if weekly.value == 'true' else 'إيقاف'}**\n"
                    f"شهري: **{'تشغيل' if monthly.value == 'true' else 'إيقاف'}**"
                )
            ),
            ephemeral=True
        )


    @app_commands.command(name="create-task", description="إنشاء مهمة مخصصة كاملة للأدمن")
    @app_commands.describe(
        period="الفترة: daily أو weekly أو monthly",
        name="اسم المهمة",
        description="شرح المهمة",
        task_type="نوع التحقق",
        target="الهدف المطلوب (للفويس: عدد الثواني)",
        reward="المكافأة بالعملات",
        role_id="رقم الرتبة المطلوبة عند الحاجة",
        channel="الروم المطلوب عند الحاجة",
        url="الرابط المطلوب عند الحاجة",
    )
    @app_commands.choices(
        period=[app_commands.Choice(name="Daily", value="daily"), app_commands.Choice(name="Weekly", value="weekly"), app_commands.Choice(name="Monthly", value="monthly")],
        task_type=[
            app_commands.Choice(name="رسائل", value="messages"),
            app_commands.Choice(name="صوت / AFK", value="afk"),
            app_commands.Choice(name="صوت / مدة فعلية", value="voice"),
            app_commands.Choice(name="دعوات", value="invites"),
            app_commands.Choice(name="أوامر", value="commands"),
            app_commands.Choice(name="تفاعل / منشن / Reply", value="interactions"),
            app_commands.Choice(name="رتبة", value="role"),
            app_commands.Choice(name="Level", value="level"),
            app_commands.Choice(name="YouTube / رابط", value="youtube"),
            app_commands.Choice(name="Top 1", value="top"),
        ]
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def create_task(self, interaction, period: app_commands.Choice[str], name: str,
                          description: str, task_type: app_commands.Choice[str], target: int,
                          reward: int, role_id: str | None = None,
                          channel: discord.TextChannel | None = None, url: str | None = None):
        if target <= 0 or reward < 0:
            await interaction.response.send_message("الهدف والبيانات غير صالحة.", ephemeral=True)
            return
        key = f"custom_{uuid.uuid4().hex[:12]}"
        try:
            row = create_custom_task(interaction.guild.id, key, period.value, name, description,
                                     task_type.value, target, reward,
                                     int(role_id) if role_id else None,
                                     channel.id if channel else None, url)
            register_custom_task(row)
        except Exception:
            await interaction.response.send_message("تعذر إنشاء المهمة. تحقق من البيانات وحاول مرة أخرى.", ephemeral=True)
            return
        await interaction.response.send_message(
            embed=success_embed("تم إنشاء المهمة", f"**{name}**\nالنوع: `{task_type.value}`\nالهدف: `{target}`\nالمكافأة: **{reward}**"),
            ephemeral=True,
        )


    @app_commands.command(name="edit-task", description="تعديل مهمة مخصصة موجودة")
    @app_commands.describe(
        task_name="اسم المهمة الحالية",
        new_name="اسم جديد (اختياري)",
        description="وصف جديد",
        target="هدف جديد (للفويس: عدد الثواني)",
        reward="مكافأة جديدة",
        role_id="رقم الرتبة",
        channel="الروم",
        url="الرابط",
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.autocomplete(task_name=custom_task_autocomplete)
    async def edit_task(self, interaction, task_name: str, new_name: str | None = None,
                        description: str | None = None, target: int | None = None,
                        reward: int | None = None, role_id: str | None = None,
                        channel: discord.TextChannel | None = None, url: str | None = None):
        current = get_custom_task_by_name(interaction.guild.id, task_name)
        builtin = None if current else builtin_task_by_name(task_name)
        if not current and not builtin:
            await interaction.response.send_message("لم أجد مهمة بهذا الاسم.", ephemeral=True)
            return
        if current:
            row = update_custom_task(interaction.guild.id, current["task_key"], name=new_name, description=description,
                                     target=target, reward=reward,
                                     role_id=int(role_id) if role_id else None,
                                     channel_id=channel.id if channel else None, url=url)
        else:
            key, period, task = builtin
            row = upsert_custom_task(interaction.guild.id, key, period, new_name or task["name"],
                                     description or task["description"], task["type"],
                                     target if target is not None else task["target"],
                                     reward if reward is not None else task["reward"],
                                     int(role_id) if role_id else task.get("role_id"),
                                     channel.id if channel else task.get("channel_id"), url or task.get("url"))
        if not row:
            await interaction.response.send_message("تعذر تعديل المهمة.", ephemeral=True)
            return
        register_custom_task(row)
        await interaction.response.send_message(embed=success_embed("تم تعديل المهمة", f"تم تحديث **{task_name}**."), ephemeral=True)


    @app_commands.command(name="delete-task", description="حذف مهمة مخصصة من السيرفر")
    @app_commands.describe(task_name="اختر المهمة التي تريد حذفها من القائمة")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.autocomplete(task_name=custom_task_autocomplete)
    async def delete_task(self, interaction, task_name: str):
        current = get_custom_task_by_name(interaction.guild.id, task_name)
        builtin = None if current else builtin_task_by_name(task_name)
        if not current and not builtin:
            await interaction.response.send_message("لم أجد مهمة بهذا الاسم.", ephemeral=True)
            return
        if current:
            deleted = delete_custom_task(interaction.guild.id, current["task_key"])
            if deleted:
                unregister_custom_task(current["task_key"], current["period"])
        else:
            key, period, task = builtin
            upsert_custom_task(interaction.guild.id, key, period, task["name"], task["description"],
                               "disabled", task["target"], task["reward"], enabled=1)
            unregister_custom_task(key, period)
        await interaction.response.send_message(
            embed=success_embed("تم حذف المهمة", f"تم حذف **{task_name}** نهائيًا من قائمة المهام."),
            ephemeral=True,
        )


    @app_commands.command(name="list-tasks", description="عرض كل المهام الافتراضية والمخصصة")
    @app_commands.checks.has_permissions(administrator=True)
    async def list_tasks(self, interaction):
        custom_rows = {row["task_key"]: row for row in get_custom_tasks(interaction.guild.id)}
        embed = discord.Embed(
            title="📚 قائمة مهام السيرفر",
            description="تظهر هنا المهام الأساسية الجاهزة والمهام التي أنشأتها أنت.",
            color=discord.Color.blurple(),
        )
        for period, title in (("daily", "☀️ اليومية"), ("weekly", "📅 الأسبوعية"), ("monthly", "🌙 الشهرية")):
            lines = []
            for key, task in TASK_GROUPS.get(period, {}).items():
                if key.startswith("custom_"):
                    continue
                lines.append(f"• **{task['name']}** — `{task['target']}` — 💰 {task['reward']}")
            for key, row in custom_rows.items():
                if row["period"] == period and row["task_type"] != "disabled":
                    lines.append(f"• 🛠️ **{row['name']}** — `{row['target']}` — 💰 {row['reward']}")
            embed.add_field(name=title, value="\n".join(lines) or "لا توجد مهام.", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


    # ========================================================
    # /setup status
    # ========================================================

    @app_commands.command(
        name="status",
        description="عرض إعدادات البوت الحالية"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def status(
        self,
        interaction: discord.Interaction
    ):

        guild_id = interaction.guild.id

        create_guild(
            guild_id
        )

        guild = get_guild(
            guild_id
        )

        if not guild:

            await interaction.response.send_message(
                embed=error_embed(
                    "خطأ",
                    "تعذر تحميل إعدادات السيرفر."
                ),
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            embed=setup_embed(
                guild
            ),
            ephemeral=True
        )


# ============================================================
# COMMAND MANAGER
# ============================================================

class CommandManager:

    def __init__(
        self,
        bot: commands.Bot
    ):

        self.bot = bot


    # ========================================================
    # /tasks
    # ========================================================

    async def tasks(
        self,
        interaction: discord.Interaction
    ):

        guild_id = interaction.guild.id
        user_id = interaction.user.id

        create_guild(
            guild_id
        )

        create_user(
            guild_id,
            user_id
        )

        user = get_user(
            guild_id,
            user_id
        )

        guild = get_guild(guild_id)
        embed = tasks_embed(
            guild_id,
            user_id,
            guild["currency_name"],
            guild["currency_symbol"],
            language=guild["language"],
        )

        await interaction.response.send_message(
            embed=embed,
            view=TasksDashboardView(guild_id, user_id)
        )


    # ========================================================
    # /profile
    # ========================================================

    async def profile(
        self,
        interaction: discord.Interaction
    ):

        guild_id = interaction.guild.id
        user_id = interaction.user.id

        create_guild(
            guild_id
        )

        create_user(
            guild_id,
            user_id
        )

        user = get_user(
            guild_id,
            user_id
        )

        if not user:

            await interaction.response.send_message(
                embed=error_embed(
                    "خطأ",
                    "تعذر العثور على بيانات حسابك."
                ),
                ephemeral=True
            )

            return

        current_level = user["level"]
        current_xp = user["xp"]

        next_xp = required_xp(
            current_level
        )

        guild = get_guild(guild_id)
        percentage = round((current_xp / next_xp) * 100) if next_xp else 0
        embed = profile_embed(
            interaction.user,
            user,
            guild["currency_name"],
            guild["currency_symbol"],
            current_xp,
            next_xp,
            percentage,
            language=guild["language"],
        )

        await interaction.response.send_message(
            embed=embed
        )


    # ========================================================
    # /balance
    # ========================================================

    async def balance(
        self,
        interaction: discord.Interaction
    ):

        guild_id = interaction.guild.id
        user_id = interaction.user.id

        create_guild(
            guild_id
        )

        create_user(
            guild_id,
            user_id
        )

        user = get_user(
            guild_id,
            user_id
        )

        guild = get_guild(guild_id)
        embed = balance_embed(
            user,
            guild["currency_name"],
            guild["currency_symbol"],
            language=guild["language"],
        )

        await interaction.response.send_message(
            embed=embed
        )


    # ========================================================
    # /top
    # ========================================================

    async def top(
        self,
        interaction: discord.Interaction
    ):

        guild_id = interaction.guild.id

        create_guild(
            guild_id
        )

        users = get_top_users(
            guild_id,
            limit=10
        )

        guild = get_guild(guild_id)
        members = {member.id: member for member in interaction.guild.members}
        embed = top_embed(users, guild, members, language=guild["language"])

        await interaction.response.send_message(
            embed=embed
        )


    # ========================================================
    # /exchange
    # ========================================================

    async def exchange(
        self,
        interaction: discord.Interaction,
        currency_id: int,
        amount: int
    ):

        guild_id = interaction.guild.id
        user_id = interaction.user.id

        create_guild(
            guild_id
        )

        create_user(
            guild_id,
            user_id
        )

        if amount <= 0:

            await interaction.response.send_message(
                embed=error_embed(
                    "قيمة غير صحيحة",
                    "يجب أن تكون الكمية أكبر من صفر."
                ),
                ephemeral=True
            )

            return

        currency = get_currency(
            guild_id,
            currency_id
        )

        if not currency:

            await interaction.response.send_message(
                embed=error_embed(
                    "العملة غير موجودة",
                    "تحقق من رقم العملة باستخدام `/exchange`."
                ),
                ephemeral=True
            )

            return

        amount = min(amount, 100)
        user = get_user(guild_id, user_id)
        if not user or user["coins"] < currency["coins_required"] * amount:
            await interaction.response.send_message(
                embed=error_embed(
                    "Insufficient balance" if get_guild(guild_id)["language"] == "en" else "فشل التحويل",
                    "You do not have enough coins for this amount."
                    if get_guild(guild_id)["language"] == "en" else
                    "ليس لديك رصيد كافٍ لإتمام الكمية المطلوبة."
                ),
                ephemeral=True,
            )
            return
        results = [exchange_coins(guild_id, user_id, currency_id) for _ in range(amount)]
        result = results[-1]

        if not result[0]:

            await interaction.response.send_message(
                embed=error_embed(
                    "فشل التحويل",
                    "ليس لديك رصيد كافٍ لإتمام عملية التحويل."
                ),
                ephemeral=True
            )

            return

        coins_spent = currency["coins_required"] * amount
        external_amount = result[1] * amount
        embed = exchange_embed(currency, coins_spent, external_amount)

        await interaction.response.send_message(
            embed=embed
        )


    @app_commands.describe(
        member="اختر العضو أو ابحث عن اسمه",
        amount="عدد الكوينز المراد تحويلها",
    )
    async def transfer(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if member.bot or member.id == interaction.user.id or amount <= 0:
            await interaction.response.send_message("اختر عضوًا صالحًا ومبلغًا أكبر من صفر.", ephemeral=True)
            return
        ok, reason = transfer_coins(interaction.guild.id, interaction.user.id, member.id, amount)
        if not ok:
            message = "رصيدك لا يكفي لإتمام التحويل." if reason == "insufficient" else "تعذر تنفيذ التحويل."
            await interaction.response.send_message(embed=error_embed("فشل التحويل", message), ephemeral=True)
            return
        await interaction.response.send_message(
            embed=success_embed("تم تحويل الكوينز", f"تم تحويل **{amount}** كوينز إلى {member.mention} ✅")
        )


    # ========================================================
    # /help
    # ========================================================

    async def help(
        self,
        interaction: discord.Interaction
    ):

        language = get_guild(interaction.guild.id)["language"]
        english = language == "en"
        embed = discord.Embed(
            title="🤖 Forge Tasks BOT",
            description=(
                "Tasks, levels, rewards and server economy."
                if english else
                "نظام المهام والمستويات والمكافآت والاقتصاد للسيرفر."
            ),
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="📋 Tasks" if english else "📋 المهام",
            value=(
                "`/tasks` — عرض المهمة الحالية\n"
                "المهام تُفتح بالتسلسل، وبعد إكمال المهمة "
                "تُفتح التالية."
            ),
            inline=False
        )

        embed.add_field(
            name="👤 Account" if english else "👤 الحساب",
            value=(
                "`/profile` — ملفك الشخصي\n"
                "`/balance` — رصيدك\n"
                "`/top` — أفضل 10 أعضاء"
            ),
            inline=False
        )

        embed.add_field(
            name="💱 Economy" if english else "💱 الاقتصاد",
            value=(
                "`/exchange` — تحويل العملات\n`/transfer` — تحويل كوينز لعضو"
            ),
            inline=False
        )

        embed.add_field(
            name="⚙️ Administration" if english else "⚙️ الإدارة",
            value=(
                "`/setup panel` — لوحة الإعدادات\n"
                "`/setup language` — اللغة\n"
                "`/setup channel` — الرومات\n"
                "`/setup xp` — XP\n"
                "`/setup reminders` — التذكيرات\n"
                "`/setup levelup` — Level Up\n"
                "`/setup currency` — العملة\n"
                "`/setup periods` — فترات المهام\n"
                "`/setup list-tasks` — كل المهام الافتراضية والمخصصة\n"
                "`/setup status` — حالة الإعدادات\n"
                "`/sendnof` — إرسال تذكير خاص بالمهام للأعضاء\n"
                "`/prank` — مقلب واضح وموسوم من البوت"
            ),
            inline=False
        )

        embed.set_footer(
            text="Forge Tasks BOT • Task System"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


    @app_commands.describe(
        message="رسالة مخصصة اختيارية، ويمكن استخدام {user} و {guild}",
        include_embed="تشغيل أو إيقاف Embed التذكير الافتراضي",
        include_message="تشغيل أو إيقاف الرسالة النصية الافتراضية",
    )
    async def sendnof(
        self,
        interaction: discord.Interaction,
        message: str | None = None,
        include_embed: bool = True,
        include_message: bool = True,
    ):
        """Send a localized task-expiry reminder to every human member."""
        if not include_embed and not include_message and not message:
            await interaction.response.send_message(
                "فعّل الـ Embed أو الرسالة النصية، أو اكتب رسالة مخصصة.",
                ephemeral=True,
            )
            return
        await interaction.response.defer(ephemeral=True)
        guild = get_guild(interaction.guild.id)
        english = guild["language"] == "en"
        sent = 0
        failed = 0

        for member in interaction.guild.members:
            if member.bot:
                continue
            embed = None
            if include_embed:
                embed = tasks_embed(
                    interaction.guild.id,
                    member.id,
                    guild["currency_name"],
                    guild["currency_symbol"],
                    language=guild["language"],
                )
                embed.title = "⏰ Task reminder" if english else "⏰ تذكير بالمهام"
                embed.description = (
                    "You have active tasks. Complete them before this period ends, or they will be reset."
                    if english else
                    "لديك مهام نشطة. أكملها قبل انتهاء الفترة، وإلا ستنتهي وتُعاد تهيئتها من البداية."
                )
            content = None
            if message:
                content = message.replace("{user}", member.display_name).replace("{guild}", interaction.guild.name)
            elif include_message:
                content = (
                    "You have active tasks. Complete them before this period ends, or they will be reset."
                    if english else
                    "لديك مهام. أكملها قبل انتهاء الفترة، وإلا ستنتهي وتُعاد تهيئتها."
                )
            try:
                await member.send(content=content, embed=embed)
                sent += 1
            except (discord.Forbidden, discord.HTTPException):
                failed += 1
            await asyncio.sleep(0.15)

        await interaction.followup.send(
            f"Reminder sent: **{sent}**, unavailable DMs: **{failed}**."
            if english else
            f"تم إرسال التذكير إلى **{sent}** عضو، وتعذر الإرسال إلى **{failed}** عضو.",
            ephemeral=True,
        )


    @app_commands.describe(
        member="العضو المستهدف",
        message="نص المقلب",
        mention="إضافة منشن للعضو عند الإرسال في روم عام",
        channel="روم عام اختياري؛ إذا لم تحدده تصل الرسالة في الخاص",
    )
    async def prank(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        message: str,
        mention: bool = False,
        channel: discord.TextChannel | None = None,
    ):
        embed = discord.Embed(
            title="🎭 Prank من Forge Tasks BOT",
            description=(
                f"{message}\n\n"
                "هذه رسالة مقلب مرحة أرسلها البوت، وليست رسالة من العضو نفسه."
            ),
            color=discord.Color.orange(),
        )
        embed.set_footer(text="Prank • رسالة واضحة من البوت")
        try:
            if channel:
                await channel.send(content=member.mention if mention else None, embed=embed)
                destination = channel.mention
            else:
                await member.send(embed=embed)
                destination = "الخاص"
        except (discord.Forbidden, discord.HTTPException):
            await interaction.response.send_message(
                "تعذر إرسال المقلب؛ تحقق من صلاحيات الروم أو إعدادات الخاص.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"تم إرسال المقلب إلى {member.mention} عبر {destination} ✅",
            ephemeral=True,
        )


# ============================================================
# REGISTER COMMANDS
# ============================================================

def register_commands(
    bot: commands.Bot
):

    manager = CommandManager(
        bot
    )

    # --------------------------------------------------------
    # Main commands
    # --------------------------------------------------------

    bot.tree.add_command(
        app_commands.Command(
            name="tasks",
            description="عرض مهامك الحالية",
            callback=manager.tasks
        )
    )

    bot.tree.add_command(
        app_commands.Command(
            name="profile",
            description="عرض ملفك الشخصي",
            callback=manager.profile
        )
    )

    bot.tree.add_command(
        app_commands.Command(
            name="balance",
            description="عرض رصيدك",
            callback=manager.balance
        )
    )

    bot.tree.add_command(
        app_commands.Command(
            name="top",
            description="عرض أفضل 10 أعضاء",
            callback=manager.top
        )
    )

    bot.tree.add_command(
        app_commands.Command(
            name="help",
            description="عرض أوامر البوت",
            callback=manager.help
        )
    )

    sendnof_command = app_commands.Command(
        name="sendnof",
        description="إرسال تذكير خاص بالمهام لجميع الأعضاء",
        callback=manager.sendnof,
    )
    sendnof_command.add_check(administrator_only)
    bot.tree.add_command(sendnof_command)

    prank_command = app_commands.Command(
        name="prank",
        description="إرسال مقلب واضح وموسوم من البوت",
        callback=manager.prank,
    )
    prank_command.add_check(administrator_only)
    bot.tree.add_command(prank_command)

    # --------------------------------------------------------
    # Exchange
    # --------------------------------------------------------

    exchange_command = app_commands.Command(
        name="exchange",
        description="تحويل العملات",
        callback=manager.exchange
    )

    bot.tree.add_command(
        exchange_command
    )

    transfer_command = app_commands.Command(
        name="transfer",
        description="تحويل كوينز لعضو باختياره من القائمة",
        callback=manager.transfer,
    )
    bot.tree.add_command(transfer_command)

    # --------------------------------------------------------
    # Setup
    # --------------------------------------------------------

    bot.tree.add_command(
        SetupGroup()
    )


# ============================================================
# ERROR HANDLER
# ============================================================

async def setup_error_handler(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    logging.getLogger("forge_tasks").exception(
        "Unhandled application command error",
        exc_info=(type(error), error, error.__traceback__),
    )

    original = getattr(error, "original", error)

    if isinstance(
        error,
        app_commands.errors.MissingPermissions
    ):

        message = (
            "ليس لديك صلاحية Administrator "
            "لاستخدام هذا الأمر."
        )

    elif isinstance(
        error,
        app_commands.errors.CommandOnCooldown
    ):

        message = (
            "الأمر مستخدم بسرعة كبيرة. "
            "حاول مرة أخرى بعد قليل."
        )

    elif isinstance(
        error,
        app_commands.errors.MissingRole
    ):

        message = (
            "لا تملك الرتبة المطلوبة."
        )

    elif isinstance(original, (ValueError, TypeError)):

        message = (
            "تعذر تنفيذ الطلب بسبب بيانات غير صالحة. "
            "تحقق من الخيارات وحاول مرة أخرى."
        )

    else:

        message = (
            "حدث خطأ أثناء تنفيذ الأمر."
        )

    try:

        if interaction.response.is_done():

            await interaction.followup.send(
                embed=error_embed(
                    "حدث خطأ",
                    message
                ),
                ephemeral=True
            )

        else:

            await interaction.response.send_message(
                embed=error_embed(
                    "حدث خطأ",
                    message
                ),
                ephemeral=True
            )

    except discord.HTTPException:

        pass
