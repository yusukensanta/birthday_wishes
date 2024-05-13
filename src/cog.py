import logging
from datetime import datetime, time
from zoneinfo import ZoneInfo

from discord.ext import commands, tasks

from src.table_manager import BirthdayManager, ChannelManager

scheduled_time = time(
    hour=0, minute=0, second=0, tzinfo=ZoneInfo("Asia/Tokyo")
)

logger = logging.getLogger(__name__)


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
