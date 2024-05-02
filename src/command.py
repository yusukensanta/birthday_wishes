import os

from discord import Interaction, Member, app_commands

from src.database.table import UserTable

DATA_PATH = os.environ.get("DATA_PATH", "data.json")
table = UserTable(DATA_PATH)


class BirthdayCommandGroup(app_commands.Group):
    def __init__(self, description: str):
        name = "bd"
        super().__init__(name, description)
        self.add_command(reg, description="誕生日登録")
        self.add_command(ls, description="誕生日リスト")
        self.add_command(rm, description="誕生日登録削除")


@app_commands.describe(month="月", day="日", user="対象のユーザー")
async def reg(
    interaction: Interaction,
    month: int = 1,
    day: int = 1,
    user: Member = None,
):
    if not 1 <= month <= 12:
        await interaction.response.send_message(
            "月は1から12の間で指定してください", ephemeral=True
        )
        return
    if not 1 <= day <= 31:
        await interaction.response.send_message(
            "日は1から31の間で指定してください", ephemeral=True
        )
        return

    data = {}
    data["month"] = month
    data["day"] = day
    if user:
        data["id"] = user.id
        display_name = user.display_name
    else:
        data["id"] = interaction.user.id
        display_name = interaction.user.display_name
    data["server_id"] = interaction.guild_id
    if table.record_exists(data):
        table.update(data)
        await interaction.response.send_message(
            f"`{display_name}`の誕生日を{month}月{day}日で更新しました",
            ephemeral=True,
        )
    else:
        table.insert(data)
        await interaction.response.send_message(
            f"`{display_name}`の誕生日を{month}月{day}日で登録しました",
            ephemeral=True,
        )


async def ls(interaction: Interaction):
    # TODO: dbから一覧取得
    await interaction.response.send_message(
        "登録されている誕生日リスト\nhoge\nhoge\nhoge", ephemeral=True
    )


@app_commands.describe(user="消す対象の人")
async def rm(interaction: Interaction, user: Member):
    await interaction.response.send_message(
        f"{user.display_name}の誕生日を消しました", ephemeral=True
    )
