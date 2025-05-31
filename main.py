import logging
import logging.handlers
import os
import sys

from discord import Intents
from discord.ext import commands

from src.cog import BirthdayCog, SchedulerCog # Added SchedulerCog
from src.command_group import BirthdayCommandGroup, ScheduleCommandGroup # Added ScheduleCommandGroup

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)

TOKEN = os.environ.get("DISCORD_TOKEN")


def run():
    intents = Intents.none()
    intents.guilds = True
    intents.message_content = True
    intents.members = True
    bot = commands.Bot(
        command_prefix="/", case_insensitive=True, intents=intents
    )
    bot.tree.add_command(BirthdayCommandGroup("誕生日関連のコマンド"))
    bot.tree.add_command(ScheduleCommandGroup(description="Manage scheduled messages")) # Added ScheduleCommandGroup
    bot.run(TOKEN, log_handler=None)

    @bot.event
    async def on_ready(self): # Note: self here is actually the bot instance due to @bot.event decorator
        logger.info("BOT is ready")
        try:
            # It's common to add cogs before syncing commands,
            # as cogs can also contain commands.
            # However, the original code added BirthdayCog after initial sync.
            # For consistency with original structure, adding SchedulerCog here.
            # A setup_hook in a Bot subclass would be a more modern place.
            await self.add_cog(BirthdayCog(self)) # 'self' is bot here
            await self.add_cog(SchedulerCog(self)) # Added SchedulerCog, 'self' is bot here

            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} commands")
        except Exception as e:
            logger.error(e)


if __name__ == "__main__":
    logging.getLogger("discord.http").setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    dt_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(
        "[{asctime}] [{levelname:<6}] {name}: {message}", dt_fmt, style="{"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    run()
