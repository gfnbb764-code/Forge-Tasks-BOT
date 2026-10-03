# ============================================================
# TASK BOT — EVENTS.PY
# Discord Events / XP / Tasks / Voice / Invites
# Python 3.11+
# ============================================================

import asyncio
import time

import discord

from database import (
    get_user,
    get_guild,
    add_message,
    add_image,
    add_invite,
    add_voice_time,
    add_afk_time,
    add_xp,
)

from tasks import (
    process_message_tasks,
    process_image_tasks,
    process_invite_tasks,
    process_voice_tasks,
    process_level_tasks,
    process_nickname_task,
    get_active_task_display,
)

from embeds import (
    task_completed_embed,
    active_task_embed,
    level_up_embed,
)


# ============================================================
# TRACKING
# ============================================================

voice_sessions = {}
invite_cache = {}
last_message_xp = {}


# ============================================================
# XP SETTINGS
# ============================================================

MESSAGE_XP = 10
VOICE_XP = 5

MESSAGE_XP_COOLDOWN = 30


# ============================================================
# EVENT MANAGER
# ============================================================

class EventManager:

    def __init__(
        self,
        bot
    ):

        self.bot = bot


    # ========================================================
    # START
    # ========================================================

    async def start(
        self
    ):

        await self.load_invites()

        print(
            "[Events] Event manager started."
        )


    # ========================================================
    # LOAD INVITES
    # ========================================================

    async def load_invites(
        self
    ):

        for guild in self.bot.guilds:

            try:

                invites = await guild.invites()

                invite_cache[
                    guild.id
                ] = {

                    invite.code:
                    invite.uses or 0

                    for invite in invites

                }

            except discord.Forbidden:

                invite_cache[
                    guild.id
                ] = {}


    # ========================================================
    # MESSAGE
    # ========================================================

    async def on_message(
        self,
        message
    ):

        if message.author.bot:
            return

        if not message.guild:
            return

        guild_id = message.guild.id
        user_id = message.author.id

        # ----------------------------------------------------
        # CREATE USER
        # ----------------------------------------------------

        user = get_user(
            guild_id,
            user_id
        )

        guild = get_guild(guild_id)

        if user and int(user["messages"] or 0) == 0 and guild:
            await self.send_daily_task_dm(message.author, guild)

        # ----------------------------------------------------
        # MESSAGE COUNT
        # ----------------------------------------------------

        add_message(
            guild_id,
            user_id
        )

        # ----------------------------------------------------
        # XP
        # ----------------------------------------------------

        await self.process_message_xp(
            message
        )

        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

        if self.has_image(message):

            add_image(
                guild_id,
                user_id
            )

            results = process_image_tasks(
                guild_id,
                user_id
            )

            await self.send_completed_tasks(
                message.channel,
                message.author,
                results
            )

        # ----------------------------------------------------
        # MESSAGE TASK
        # ----------------------------------------------------

        results = process_message_tasks(
            guild_id,
            user_id,
            message.channel.id
        )

        await self.send_completed_tasks(
            message.channel,
            message.author,
            results
        )

        # ----------------------------------------------------
        # LEVEL TASK
        # ----------------------------------------------------

        result = process_level_tasks(
            guild_id,
            user_id
        )

        await self.send_completed_tasks(
            message.channel,
            message.author,
            [result]
        )


    # ========================================================
    # MESSAGE XP
    # ========================================================

    async def process_message_xp(
        self,
        message
    ):

        guild_id = message.guild.id
        user_id = message.author.id

        guild = get_guild(
            guild_id
        )

        if not guild:
            return

        if not guild["xp_enabled"]:
            return

        current_time = time.time()

        key = (
            guild_id,
            user_id
        )

        last_time = last_message_xp.get(
            key,
            0
        )

        if (
            current_time - last_time
            <
            MESSAGE_XP_COOLDOWN
        ):

            return

        last_message_xp[
            key
        ] = current_time

        old_level, new_level = add_xp(
            guild_id,
            user_id,
            MESSAGE_XP
        )

        if new_level > old_level:

            await self.send_level_up(
                message.channel,
                message.author,
                old_level,
                new_level
            )


    # ========================================================
    # IMAGE DETECTION
    # ========================================================

    @staticmethod
    def has_image(
        message
    ):

        for attachment in message.attachments:

            content_type = (
                attachment.content_type
                or ""
            )

            if content_type.startswith(
                "image/"
            ):

                return True

            filename = (
                attachment.filename.lower()
            )

            image_extensions = (
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp",
                ".bmp",
            )

            if filename.endswith(
                image_extensions
            ):

                return True

        return False


    # ========================================================
    # VOICE UPDATE
    # ========================================================

    async def on_voice_state_update(
        self,
        member,
        before,
        after
    ):

        if member.bot:
            return

        # ----------------------------------------------------
        # JOIN
        # ----------------------------------------------------

        if after.channel and not before.channel:

            await self.voice_joined(
                member,
                after
            )

            return

        # ----------------------------------------------------
        # MOVE
        # ----------------------------------------------------

        if after.channel and before.channel:

            key = (
                member.guild.id,
                member.id
            )

            if key not in voice_sessions:

                await self.voice_joined(
                    member,
                    after
                )

            else:

                voice_sessions[
                    key
                ]["channel_id"] = (
                    after.channel.id
                )

            return

        # ----------------------------------------------------
        # LEAVE
        # ----------------------------------------------------

        if before.channel and not after.channel:

            await self.voice_left(
                member
            )


    # ========================================================
    # VOICE JOINED
    # ========================================================

    async def voice_joined(
        self,
        member,
        state
    ):

        guild_id = member.guild.id
        user_id = member.id

        voice_sessions[
            (
                guild_id,
                user_id
            )
        ] = {

            "started": time.time(),

            "last_update": time.time(),

            "channel_id":
                state.channel.id,

            "afk": bool(
                state.afk
            ),

        }


    # ========================================================
    # VOICE LEFT
    # ========================================================

    async def voice_left(
        self,
        member
    ):

        guild_id = member.guild.id
        user_id = member.id

        key = (
            guild_id,
            user_id
        )

        session = voice_sessions.pop(
            key,
            None
        )

        if not session:
            return

        elapsed = int(
            time.time()
            -
            session["started"]
        )

        if elapsed <= 0:
            return

        # ----------------------------------------------------
        # VOICE TIME
        # ----------------------------------------------------

        add_voice_time(
            guild_id,
            user_id,
            elapsed
        )

        # ----------------------------------------------------
        # ACTUAL DISCORD AFK TIME
        #
        # This is kept for statistics.
        # It does NOT grant XP.
        # ----------------------------------------------------

        if session["afk"]:

            add_afk_time(
                guild_id,
                user_id,
                elapsed
            )

        # ----------------------------------------------------
        # VOICE XP
        # ----------------------------------------------------

        guild = get_guild(
            guild_id
        )

        if guild and guild["xp_enabled"]:

            minutes = elapsed // 60

            xp_amount = (
                minutes *
                VOICE_XP
            )

            if xp_amount > 0:

                old_level, new_level = add_xp(
                    guild_id,
                    user_id,
                    xp_amount
                )

                if new_level > old_level:

                    await self.send_level_up(
                        member.guild.system_channel,
                        member,
                        old_level,
                        new_level
                    )

        # ----------------------------------------------------
        # VOICE TASK
        # ----------------------------------------------------

        results = process_voice_tasks(
            guild_id,
            user_id
        )

        await self.send_completed_tasks(
            member.guild.system_channel,
            member,
            results
        )


    # ========================================================
    # VOICE TRACKING LOOP
    # ========================================================

    async def voice_loop(
        self
    ):

        await self.bot.wait_until_ready()

        while not self.bot.is_closed():

            current_time = time.time()

            for key, session in list(
                voice_sessions.items()
            ):

                guild_id, user_id = key

                guild = self.bot.get_guild(
                    guild_id
                )

                if not guild:
                    continue

                member = guild.get_member(
                    user_id
                )

                if not member:
                    continue

                if not member.voice:
                    continue

                if not member.voice.channel:
                    continue

                # ------------------------------------------------
                # UPDATE EVERY 60 SECONDS
                # ------------------------------------------------

                last_update = session.get(
                    "last_update",
                    session["started"]
                )

                elapsed = int(
                    current_time -
                    last_update
                )

                if elapsed < 60:
                    continue

                session["last_update"] = current_time

                # ------------------------------------------------
                # VOICE TIME
                # ------------------------------------------------

                add_voice_time(
                    guild_id,
                    user_id,
                    60
                )

                # ------------------------------------------------
                # DISCORD AFK STATISTICS
                #
                # Kept for tracking only.
                # No XP is awarded because of AFK state.
                # ------------------------------------------------

                if member.voice.afk:

                    session["afk"] = True

                    add_afk_time(
                        guild_id,
                        user_id,
                        60
                    )

                # ------------------------------------------------
                # VOICE XP
                # ------------------------------------------------

                guild_settings = get_guild(
                    guild_id
                )

                if (
                    guild_settings
                    and
                    guild_settings["xp_enabled"]
                ):

                    old_level, new_level = add_xp(
                        guild_id,
                        user_id,
                        VOICE_XP
                    )

                    if new_level > old_level:

                        channel = (
                            guild.system_channel
                        )

                        if channel:

                            await self.send_level_up(
                                channel,
                                member,
                                old_level,
                                new_level
                            )

                # ------------------------------------------------
                # VOICE TASK
                # ------------------------------------------------

                results = process_voice_tasks(
                    guild_id,
                    user_id
                )

                channel = (
                    guild.system_channel
                )

                await self.send_completed_tasks(
                    channel,
                    member,
                    results
                )

            await asyncio.sleep(
                10
            )


    # ========================================================
    # INVITES
    # ========================================================

    async def on_invite_create(
        self,
        invite
    ):

        guild_id = invite.guild.id

        if guild_id not in invite_cache:

            invite_cache[
                guild_id
            ] = {}

        invite_cache[
            guild_id
        ][invite.code] = (
            invite.uses or 0
        )


    # ========================================================
    # MEMBER JOIN
    # ========================================================

    async def on_member_join(
        self,
        member
    ):

        if member.bot:
            return

        guild = member.guild

        try:

            current_invites = (
                await guild.invites()
            )

        except discord.Forbidden:

            return

        previous = invite_cache.get(
            guild.id,
            {}
        )

        used_invite = None

        for invite in current_invites:

            old_uses = previous.get(
                invite.code,
                0
            )

            new_uses = (
                invite.uses or 0
            )

            if new_uses > old_uses:

                used_invite = invite
                break

        invite_cache[
            guild.id
        ] = {

            invite.code:
            invite.uses or 0

            for invite in current_invites

        }

        if not used_invite:
            return

        inviter = used_invite.inviter

        if not inviter:
            return

        if inviter.bot:
            return

        add_invite(
            guild.id,
            inviter.id,
            1
        )

        results = process_invite_tasks(
            guild.id,
            inviter.id
        )

        await self.send_completed_tasks(
            guild.system_channel,
            inviter,
            results
        )


    # ========================================================
    # NICKNAME
    # ========================================================

    async def on_member_update(
        self,
        before,
        after
    ):

        if before.nick == after.nick:
            return

        if after.bot:
            return

        guild_id = after.guild.id
        user_id = after.id

        result = process_nickname_task(
            guild_id,
            user_id
        )

        await self.send_completed_tasks(
            after.guild.system_channel,
            after,
            [result]
        )


    # ========================================================
    # SEND COMPLETED TASK
    # ========================================================

    async def send_completed_tasks(
        self,
        channel,
        member,
        results
    ):

        if not results:
            return

        guild = get_guild(
            member.guild.id
        )

        if not guild:
            return

        for result in results:

            if not result:
                continue

            if not result.get(
                "completed",
                False
            ):

                continue

            task = result.get(
                "task"
            )

            if not task:
                continue

            next_task = result.get(
                "next_task"
            )

            next_task_number = result.get(
                "next_task_number"
            )

            total_tasks = result.get(
                "total_tasks"
            )

            embed = task_completed_embed(

                task,

                guild["currency_name"],

                guild["currency_symbol"],

                next_task=next_task,

                next_task_number=next_task_number,

                total_tasks=total_tasks,

                language=guild["language"]

            )

            try:

                await member.send(embed=embed)

            except (discord.HTTPException, discord.Forbidden):

                if channel:
                    try:
                        await channel.send(content=member.mention, embed=embed)
                    except discord.HTTPException:
                        pass


    async def send_daily_task_dm(
        self,
        member,
        guild
    ):

        """Send the first daily task privately once when a member starts."""

        display = get_active_task_display(
            guild["guild_id"],
            member.id,
            "daily"
        )

        if not display.get("available"):
            return

        embed = active_task_embed(
            guild["guild_id"],
            member.id,
            "daily",
            guild["currency_name"],
            guild["currency_symbol"]
        )

        embed.title = "🚀 مهمتك اليومية الأولى"
        embed.description = (
            "أهلًا بك في Forge Tasks!\n\n"
            "هذه أول مهمة يومية لك. نفّذها ليتم فتح المهمة التالية تلقائيًا.\n"
            "سأرسل لك إشعارًا خاصًا عند الإكمال مع تفاصيل المهمة القادمة."
        )

        try:
            await member.send(embed=embed)
        except (discord.HTTPException, discord.Forbidden):
            pass


    # ========================================================
    # LEVEL UP MESSAGE
    # ========================================================

    async def send_level_up(
        self,
        channel,
        member,
        old_level,
        new_level
    ):

        guild = get_guild(
            member.guild.id
        )

        if not guild:
            return

        if not guild["level_up_enabled"]:

            return

        embed = level_up_embed(

            member,

            old_level,

            new_level,

            mention=guild["level_up_mention"],

            message=guild["level_up_message"]

        )

        try:

            content = None

            if guild["level_up_mention"]:

                content = member.mention

            await channel.send(

                content=content,

                embed=embed

            )

        except discord.HTTPException:

            pass


# ============================================================
# REGISTER EVENTS
# ============================================================

def register_events(
    bot
):

    manager = EventManager(
        bot
    )

    @bot.event
    async def on_message(
        message
    ):

        await manager.on_message(
            message
        )

        # ----------------------------------------------------
        # Keep normal commands working.
        # ----------------------------------------------------

        await bot.process_commands(
            message
        )


    @bot.event
    async def on_voice_state_update(
        member,
        before,
        after
    ):

        await manager.on_voice_state_update(

            member,

            before,

            after

        )


    @bot.event
    async def on_invite_create(
        invite
    ):

        await manager.on_invite_create(
            invite
        )


    @bot.event
    async def on_member_join(
        member
    ):

        await manager.on_member_join(
            member
        )


    @bot.event
    async def on_member_update(
        before,
        after
    ):

        await manager.on_member_update(

            before,

            after

        )


    return manager
