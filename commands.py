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
    update_guild_setting,
    required_xp,
)

from tasks import get_all_tasks

from embeds import (
    tasks_embed,
    profile_embed,
    balance_embed,
    top_embed,
    exchange_embed,
    setup_embed,
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
                "تم تغيير اللغة",
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
            guild.get(
                "xp_enabled",
                True
            )
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
            guild.get(
                "reminders_enabled",
                True
            )
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
            guild.get(
                "level_up_enabled",
                True
            )
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
            guild.get(
                "level_up_mention",
                True
            )
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
                "تم تغيير اللغة",
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

        embed = tasks_embed(
            guild_id,
            user_id,
            user
        )

        await interaction.response.send_message(
            embed=embed
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

        embed = profile_embed(
            interaction.user,
            user,
            current_level,
            current_xp,
            next_xp
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

        embed = balance_embed(
            interaction.user,
            user
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

        embed = top_embed(
            interaction.guild,
            users
        )

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

        result = exchange_coins(
            guild_id,
            user_id,
            currency_id,
            amount
        )

        if not result:

            await interaction.response.send_message(
                embed=error_embed(
                    "فشل التحويل",
                    "ليس لديك رصيد كافٍ لإتمام عملية التحويل."
                ),
                ephemeral=True
            )

            return

        embed = exchange_embed(
            interaction.user,
            currency,
            amount,
            result
        )

        await interaction.response.send_message(
            embed=embed
        )


    # ========================================================
    # /help
    # ========================================================

    async def help(
        self,
        interaction: discord.Interaction
    ):

        embed = discord.Embed(
            title="🤖 Forge Tasks BOT",
            description=(
                "نظام المهام والمستويات والمكافآت "
                "والاقتصاد للسيرفر."
            ),
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="📋 المهام",
            value=(
                "`/tasks` — عرض المهمة الحالية\n"
                "المهام تُفتح بالتسلسل، وبعد إكمال المهمة "
                "تُفتح التالية."
            ),
            inline=False
        )

        embed.add_field(
            name="👤 الحساب",
            value=(
                "`/profile` — ملفك الشخصي\n"
                "`/balance` — رصيدك\n"
                "`/top` — أفضل 10 أعضاء"
            ),
            inline=False
        )

        embed.add_field(
            name="💱 الاقتصاد",
            value=(
                "`/exchange` — تحويل العملات"
            ),
            inline=False
        )

        embed.add_field(
            name="⚙️ الإدارة",
            value=(
                "`/setup panel` — لوحة الإعدادات\n"
                "`/setup language` — اللغة\n"
                "`/setup channel` — الرومات\n"
                "`/setup xp` — XP\n"
                "`/setup reminders` — التذكيرات\n"
                "`/setup levelup` — Level Up\n"
                "`/setup currency` — العملة\n"
                "`/setup periods` — فترات المهام\n"
                "`/setup status` — حالة الإعدادات"
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
