from datetime import time
from zoneinfo import ZoneInfo

from discord.ext import commands, tasks

scheduled_time = time(hour=0, minute=0, tzinfo=ZoneInfo("Asia/Tokyo"))


class BirthdayBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @tasks.loop(time=scheduled_time)
    async def birthday_wish(self):
        print("Wishing happy birthday to everyone")

    @birthday_wish.before_loop
    async def before_birthday_wish(self):
        await self.bot.wait_until_ready()
