import discord
from discord import app_commands
from discord.ext import commands

from database import (
    create_guild,
    get_guild,
    create_user,
    get_user,
    get_top_users,
    get_currencies,
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
# SETUP GROUP
# ============================================================

class SetupGroup(app_commands.Group):
    def __init__(self):
        super().__init__(
            name="setup",
            description="إعدادات البوت وإدارة السيرفر"
        )

    # --------------------------------------------------------
    # /setup language
    # --------------------------------------------------------

    @app_commands.command(
        name="language",
        description="تغيير لغة البوت"
    )
    @app_commands.describe(
        language="لغة البوت"
    )
    @app_commands.choices(
        language=[
            app_commands.Choice(name="العربية", value="ar"),
            app_commands.Choice(name="English", value="en"),
        ]
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def language(
        self,
        interaction: discord.Interaction,
        language: app_commands.Choice[str]
    ):
        guild_id = interaction.guild.id

        create_guild(guild_id)

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

    # --------------------------------------------------------
    # /setup channel
    # --------------------------------------------------------

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
                value="notification_channel"
            ),
            app_commands.Choice(
                name="روم الرسائل المطلوبة",
                value="message_channel"
            ),
        ]
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def channel(
        self,
        interaction: discord.Interaction,
        channel_type: app_commands.Choice[str],
        channel: discord.TextChannel
    ):
        guild_id = interaction.guild.id

        create_guild(guild_id)

        update_guild_setting(
            guild_id,
            channel_type.value,
            str(channel.id)
        )

        names = {
            "task_channel": "روم المهام",
            "notification_channel": "روم الإشعارات",
            "message_channel": "روم الرسائل المطلوبة",
        }

        await interaction.response.send_message(
            embed=success_embed(
                "تم حفظ الإعداد",
                f"{names[channel_type.value]} أصبح {channel.mention}."
            ),
            ephemeral=True
        )

    # --------------------------------------------------------
    # /setup xp
    # --------------------------------------------------------

    @app_commands.command(
        name="xp",
        description="تفعيل أو تعطيل نظام الخبرة"
    )
    @app_commands.describe(
        enabled="تشغيل أو إيقاف XP"
    )
    @app_commands.choices(
        enabled=[
            app_commands.Choice(name="تشغيل", value="true"),
            app_commands.Choice(name="إيقاف", value="false"),
        ]
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def xp(
        self,
        interaction: discord.Interaction,
        enabled: app_commands.Choice[str]
    ):
        guild_id = interaction.guild.id

        create_guild(guild_id)

        update_guild_setting(
            guild_id,
            "xp_enabled",
            enabled.value
        )

        state = "تشغيل" if enabled.value == "true" else "إيقاف"

        await interaction.response.send_message(
            embed=success_embed(
                "تم تحديث XP",
                f"تم ضبط نظام الخبرة على **{state}**."
            ),
            ephemeral=True
        )

    # --------------------------------------------------------
    # /setup reminders
    # --------------------------------------------------------

    @app_commands.command(
        name="reminders",
        description="تفعيل أو تعطيل تذكيرات المهام"
    )
    @app_commands.describe(
        enabled="تشغيل أو إيقاف التذكيرات"
    )
    @app_commands.choices(
        enabled=[
            app_commands.Choice(name="تشغيل", value="true"),
            app_commands.Choice(name="إيقاف", value="false"),
        ]
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def reminders(
        self,
        interaction: discord.Interaction,
        enabled: app_commands.Choice[str]
    ):
        guild_id = interaction.guild.id

        create_guild(guild_id)

        update_guild_setting(
            guild_id,
            "reminders_enabled",
            enabled.value
        )

        state = "تشغيل" if enabled.value == "true" else "إيقاف"

        await interaction.response.send_message(
            embed=success_embed(
                "تم تحديث التذكيرات",
                f"تذكيرات المهام: **{state}**."
            ),
            ephemeral=True
        )

    # --------------------------------------------------------
    # /setup status
    # --------------------------------------------------------

    @app_commands.command(
        name="status",
        description="عرض إعدادات البوت الحالية"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def status(
        self,
        interaction: discord.Interaction
    ):
        guild_id = interaction.guild.id

        create_guild(guild_id)

        guild = get_guild(guild_id)

        if not guild:
            await interaction.response.send_message(
                embed=error_embed(
                    "خطأ",
                    "تعذر تحميل إعدادات السيرفر."
                ),
                ephemeral=True
            )
            return

        embed = setup_embed(guild)

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# ============================================================
# COMMAND MANAGER
# ============================================================

class CommandManager:

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --------------------------------------------------------
    # /tasks
    # --------------------------------------------------------

    async def tasks(
        self,
        interaction: discord.Interaction
    ):
        guild_id = interaction.guild.id
        user_id = interaction.user.id

        create_guild(guild_id)
        create_user(guild_id, user_id)

        user = get_user(guild_id, user_id)

        embed = tasks_embed(
            guild_id,
            user_id,
            user
        )

        await interaction.response.send_message(
            embed=embed
        )

    # --------------------------------------------------------
    # /profile
    # --------------------------------------------------------

    async def profile(
        self,
        interaction: discord.Interaction
    ):
        guild_id = interaction.guild.id
        user_id = interaction.user.id

        create_guild(guild_id)
        create_user(guild_id, user_id)

        user = get_user(guild_id, user_id)

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

        next_xp = required_xp(current_level)

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

    # --------------------------------------------------------
    # /balance
    # --------------------------------------------------------

    async def balance(
        self,
        interaction: discord.Interaction
    ):
        guild_id = interaction.guild.id
        user_id = interaction.user.id

        create_guild(guild_id)
        create_user(guild_id, user_id)

        user = get_user(guild_id, user_id)

        embed = balance_embed(
            interaction.user,
            user
        )

        await interaction.response.send_message(
            embed=embed
        )

    # --------------------------------------------------------
    # /top
    # --------------------------------------------------------

    async def top(
        self,
        interaction: discord.Interaction
    ):
        guild_id = interaction.guild.id

        create_guild(guild_id)

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

    # --------------------------------------------------------
    # /exchange
    # --------------------------------------------------------

    async def exchange(
        self,
        interaction: discord.Interaction,
        currency_id: int,
        amount: int
    ):
        guild_id = interaction.guild.id
        user_id = interaction.user.id

        create_guild(guild_id)
        create_user(guild_id, user_id)

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

    # --------------------------------------------------------
    # /help
    # --------------------------------------------------------

    async def help(
        self,
        interaction: discord.Interaction
    ):
        embed = discord.Embed(
            title="🤖 Task Bot",
            description="قائمة أوامر البوت",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="📋 المهام",
            value="`/tasks` — عرض المهام اليومية والأسبوعية",
            inline=False
        )

        embed.add_field(
            name="👤 الحساب",
            value=(
                "`/profile` — عرض الملف الشخصي\n"
                "`/balance` — عرض الرصيد\n"
                "`/top` — أفضل 10 أعضاء"
            ),
            inline=False
        )

        embed.add_field(
            name="💱 الاقتصاد",
            value="`/exchange` — تحويل العملات",
            inline=False
        )

        embed.add_field(
            name="⚙️ الإدارة",
            value=(
                "`/setup language`\n"
                "`/setup channel`\n"
                "`/setup xp`\n"
                "`/setup reminders`\n"
                "`/setup status`"
            ),
            inline=False
        )

        embed.set_footer(
            text="Task Bot • نظام المهام والمكافآت"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# ============================================================
# REGISTER COMMANDS
# ============================================================

def register_commands(bot: commands.Bot):

    manager = CommandManager(bot)

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
    # Exchange command
    # --------------------------------------------------------

    exchange_command = app_commands.Command(
        name="exchange",
        description="تحويل العملات"
    )

    exchange_command.add_callback(manager.exchange)

    bot.tree.add_command(exchange_command)

    # --------------------------------------------------------
    # Setup group
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
        message = "ليس لديك صلاحية Administrator لاستخدام هذا الأمر."

    elif isinstance(
        error,
        app_commands.errors.CommandOnCooldown
    ):
        message = "الأمر مستخدم بسرعة كبيرة. حاول مرة أخرى بعد قليل."

    else:
        message = "حدث خطأ أثناء تنفيذ الأمر."

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
