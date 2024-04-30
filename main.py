import os

import discord
from discord import app_commands
from discord.ext import commands

TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.none()
intents.message_content = True
bot = commands.Bot(command_prefix="/", case_insensitive=True, intents=intents)


@bot.event
async def on_ready():
    print("BOT is ready")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)


@bot.tree.command(name="reg")
@app_commands.describe(month="月", day="日")
async def reg(interaction: discord.Interaction, month: int = 1, day: int = 1):
    # TODO: dbへ登録
    await interaction.response.send_message(f"{month}/{day}", ephemeral=True)


@bot.tree.command(name="ls")
async def ls(interaction: discord.Interaction):
    # TODO: dbから一覧取得
    await interaction.response.send_message(
        "登録されている誕生日リスト\nhoge\nhoge\nhoge", ephemeral=True
    )


@bot.tree.command(name="rm")
@app_commands.describe(user="消す対象の人")
async def rm(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.send_message(
        f"{user.name}の誕生日を消しました", ephemeral=True
    )


bot.run(TOKEN)
