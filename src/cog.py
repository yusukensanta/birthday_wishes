import logging
from datetime import datetime, time, timezone # Added timezone
from zoneinfo import ZoneInfo # Kept for BirthdayCog

import discord # Added for error types like discord.Forbidden
from discord.ext import commands, tasks

from src.table_manager import ( # Added ScheduledMessageManager
    BirthdayManager,
    ChannelManager,
    ScheduledMessageManager,
)
from src.scheduler import MessageScheduler # Added MessageScheduler

scheduled_time = time(
    hour=0, minute=0, second=0, tzinfo=ZoneInfo("Asia/Tokyo")
)

logger = logging.getLogger(__name__) # Reused logger


class BirthdayCog(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot
        self.birthday_wish.start()

    def cog_unload(self):
        self.birthday_wish.cancel()

    @tasks.loop(time=scheduled_time)
    async def birthday_wish(self):
        today = datetime.now(ZoneInfo("Asia/Tokyo"))
        logger.info(
            f"Checking birthday for {today.strftime('%Y-%m-%d %H:%M:%S%z')}"
        )
        async for guild in self.fetch_guilds():
            server_id = guild.id
            birthday_manager = BirthdayManager()
            birthdays = birthday_manager.list_all(server_id=server_id)

            if not birthdays:
                continue
            else:
                for birthday in birthdays:
                    if (
                        birthday["birth_month"] == today.month
                        and birthday["birth_day"] == today.day
                    ):
                        channel_manager = ChannelManager(server_id=server_id)
                        channel = channel_manager.list_all(
                            server_id=server_id
                        )[0]
                        if not channel:
                            continue
                        await self.get_channel(channel["channel_id"]).send(
                            "Happy Birthday!"
                        )


class SchedulerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = MessageScheduler()
        self.message_manager = ScheduledMessageManager()
        self.check_scheduled_messages.start()

    def cog_unload(self):
        self.check_scheduled_messages.cancel()

    @tasks.loop(minutes=1)
    async def check_scheduled_messages(self):
        logger.info("SchedulerCog: Checking for scheduled messages...")
        # Use UTC for consistency with MessageScheduler's default
        now = datetime.now(timezone.utc)

        # Iterate over all guilds the bot is in
        # Using self.bot.guilds directly is often preferred if cache is populated
        # fetch_guilds() is more robust if guilds list might be incomplete.
        # However, fetch_guilds() is an async iterator and might be slow if many guilds.
        # For a background task, self.bot.guilds should be fine after bot is ready.
        for guild in self.bot.guilds:
            server_id = guild.id
            logger.debug(f"SchedulerCog: Checking guild {server_id}")
            try:
                scheduled_messages = self.message_manager.list_all(server_id=server_id)
                if not scheduled_messages:
                    continue

                logger.debug(f"SchedulerCog: Found {len(scheduled_messages)} messages for guild {server_id}")

                for message_data in scheduled_messages:
                    try:
                        if self.scheduler.is_due(message_data['cron_expression'], now):
                            logger.info(
                                f"SchedulerCog: Message ID {message_data['message_id']} is due for guild {server_id}."
                            )
                            channel = self.bot.get_channel(message_data['channel_id'])
                            if channel:
                                try:
                                    await channel.send(message_data['message_content'])
                                    logger.info(
                                        f"SchedulerCog: Sent message ID {message_data['message_id']} to channel {message_data['channel_id']} in guild {server_id}"
                                    )
                                except discord.Forbidden:
                                    logger.error(
                                        f"SchedulerCog: Missing permissions to send message ID {message_data['message_id']} to channel {message_data['channel_id']} in guild {server_id}"
                                    )
                                except discord.HTTPException as e:
                                    logger.error(
                                        f"SchedulerCog: HTTP error sending message ID {message_data['message_id']} to channel {message_data['channel_id']} in guild {server_id}: {e}"
                                    )
                            else:
                                logger.warning(
                                    f"SchedulerCog: Channel ID {message_data['channel_id']} not found for message ID {message_data['message_id']} in guild {server_id}. Consider removing this message."
                                )
                    except Exception as e:
                        logger.error(f"SchedulerCog: Error processing message {message_data.get('message_id', 'Unknown ID')} in guild {server_id}: {e}")

            except Exception as e:
                logger.error(f"SchedulerCog: Failed to retrieve or process messages for guild {server_id}: {e}")
        logger.info("SchedulerCog: Finished checking scheduled messages.")

    @check_scheduled_messages.before_loop
    async def before_check_scheduled_messages(self):
        await self.bot.wait_until_ready()
        logger.info("SchedulerCog: Bot is ready, starting message check loop.")
