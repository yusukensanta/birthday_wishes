import os

from discord import Intents
from discord.ext import commands

from src.command import BirthdayCommandGroup

TOKEN = os.environ.get("DISCORD_TOKEN")


def run():
    intents = Intents.none()
    intents.message_content = True
    bot = commands.Bot(
        command_prefix="/", case_insensitive=True, intents=intents
    )
    bot.tree.add_command(BirthdayCommandGroup("誕生日関連のコマンド"))

    @bot.event
    async def on_ready():
        print("BOT is ready")
        try:
            synced = await bot.tree.sync()
            print(f"Synced {len(synced)} commands")
        except Exception as e:
            print(e)

    bot.run(TOKEN)


if __name__ == "__main__":
    run()
