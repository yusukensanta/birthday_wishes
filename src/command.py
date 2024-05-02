import logging

from discord import Interaction, Member, app_commands

from src.database.table import UserTable

logger = logging.getLogger(__name__)


class BirthdayCommandGroup(app_commands.Group):
    def __init__(self, description: str):
        name = "bd"
        super().__init__(name=name, description=description)
        self.add_command(reg)
        self.add_command(ls)
        self.add_command(rm)


@app_commands.command(
    description="誕生日を登録します(userが指定されていない場合は自分の誕生日を登録します)"
)
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
    print(user, type(user))
    if user:
        data["id"] = user.id
        display_name = user.display_name
    else:
        data["id"] = interaction.user.id
        display_name = interaction.user.display_name
    data["server_id"] = interaction.guild_id
    table = UserTable(data["server_id"])
    if table.record_exists(data):
        table.update(data)
        logger.info(f"Updated data `{data}`")
        await interaction.response.send_message(
            f"`{display_name}`の誕生日を{month}月{day}日で更新しました"
        )
    else:
        table.insert(data)
        logger.info(f"Inserted data `{data}`")
        await interaction.response.send_message(
            f"`{display_name}`の誕生日を{month}月{day}日で登録しました"
        )


@app_commands.command(description="登録されている誕生日のリストを表示します")
async def ls(interaction: Interaction):
    table = UserTable(interaction.guild_id)
    users = table.list_all()
    if not users:
        await interaction.response.send_message(
            "誕生日が登録されていません", ephemeral=True
        )
        return
    for index, user in enumerate(users):
        discord_users: Member = interaction.guild.get_member(user["id"])
        if discord_users:
            users[index]["display_name"] = discord_users.display_name
        else:
            users[index]["display_name"] = "すでに退出したユーザー"

    message = "\n".join(
        [
            f"{user['display_name']} : {user['month']}月{user['day']}日"
            for user in users
        ]
    )

    await interaction.response.send_message(
        f"登録されている誕生日一覧\n{message}", ephemeral=True
    )


@app_commands.command(
    description="誕生日を消します(userが指定されていない場合は自分の誕生日を消します)"
)
@app_commands.describe(user="消す対象の人")
async def rm(interaction: Interaction, user: Member):
    await interaction.response.send_message(
        f"{user.display_name}の誕生日を消しました", ephemeral=True
    )
