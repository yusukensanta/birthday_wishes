import logging
import logging.handlers
import os
import sys

from discord import Intents
from discord.ext import commands

from src.cog import BirthdayCog
from src.command_group import BirthdayCommandGroup

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
    bot.run(TOKEN, log_handler=None)

    @bot.event
    async def on_ready(self):
        logger.info("BOT is ready")
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} commands")
            await bot.add_cog(BirthdayCog(bot))
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
