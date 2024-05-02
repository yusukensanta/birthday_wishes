import logging
import logging.handlers
import os
import sys

from discord import Intents
from discord.ext import commands

from src.command import BirthdayCommandGroup

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

    @bot.event
    async def on_ready():
        logger.info("BOT is ready")
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} commands")
        except Exception as e:
            logger.error(e)

    bot.run(TOKEN, log_handler=None)


if __name__ == "__main__":
    logging.getLogger("discord.http").setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    dt_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(
        "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    run()
