import os

import discord
from discord import app_commands
from discord.ext import commands

TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.none()
intents.message_content = True
bot = commands.Bot(command_prefix="/", case_insensitive=True, intents=intents)
group = app_commands.Group(name="bd", description="birthday commands")
bot.tree.add_command(group)


@group.command(description="誕生日を登録する")
@app_commands.describe(month="月", day="日", user="対象のユーザー")
async def reg(
    interaction: discord.Interaction,
    month: int = 1,
    day: int = 1,
    user: discord.Member = None,
):
    # TODO: dbへ登録
    await interaction.response.send_message(f"{month}/{day}", ephemeral=True)


@group.command(description="現在登録されている誕生日リストを見る")
async def ls(interaction: discord.Interaction):
    # TODO: dbから一覧取得
    await interaction.response.send_message(
        "登録されている誕生日リスト\nhoge\nhoge\nhoge", ephemeral=True
    )


@group.command(description="誕生日登録を消す")
@app_commands.describe(user="消す対象の人")
async def rm(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.send_message(
        f"{user.display_name}の誕生日を消しました", ephemeral=True
    )


@bot.event
async def on_ready():
    print("BOT is ready")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)


bot.run(TOKEN)
