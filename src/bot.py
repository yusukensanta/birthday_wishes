from datetime import datetime, time
from zoneinfo import ZoneInfo

from discord.ext import commands, tasks

from src.table_manager import BirthdayManager, ChannelManager

scheduled_time = time(
    hour=0, minute=0, second=0, tzinfo=ZoneInfo("Asia/Tokyo")
)


class BirthdayBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @tasks.loop(time=scheduled_time)
    async def birthday_wish(self):
        today = datetime.now(ZoneInfo("Asia/Tokyo"))
        for guild in self.guilds():
            server_id = guild.id
            birthday_manager = BirthdayManager(server_id=server_id)
            birthdays = birthday_manager.list_all()
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

    @birthday_wish.before_loop
    async def before_birthday_wish(self):
        await self.bot.wait_until_ready()
