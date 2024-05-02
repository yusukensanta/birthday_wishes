import logging

from discord import Interaction, Member, TextChannel, app_commands

from src.database.table import ChannelTable, MemberTable

logger = logging.getLogger(__name__)


class BirthdayCommandGroup(app_commands.Group):
    def __init__(self, description: str):
        name = "bd"
        super().__init__(name=name, description=description)
        self.add_command(reg)
        self.add_command(ls)
        self.add_command(rm)
        self.add_command(send_to)
        self.add_command(stop)


@app_commands.command(
    description="誕生日を登録します(memberが指定されていない場合は自分の誕生日を登録します)"
)
@app_commands.describe(month="月", day="日", member="対象のユーザー")
async def reg(
    interaction: Interaction,
    month: int = 1,
    day: int = 1,
    member: Member = None,
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
    if member:
        data["member_id"] = member.id
        display_name = member.display_name
    else:
        data["member_id"] = interaction.user.id
        display_name = interaction.user.display_name
    data["server_id"] = interaction.guild_id

    table = MemberTable()
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
    table = MemberTable()
    members = table.list_all()
    if not members:
        await interaction.response.send_message(
            "誕生日が登録されていません", ephemeral=True
        )
        return
    for index, member in enumerate(members):
        discord_user: Member = interaction.guild.get_member(
            member.get("member_id")
        )
        if discord_user:
            members[index]["display_name"] = discord_user.display_name
        else:
            members[index]["display_name"] = "すでに退出したユーザー"

    message = "\n".join(
        [
            f"{member['display_name']} : {member['month']}月{member['day']}日"
            for member in members
        ]
    )

    await interaction.response.send_message(
        f"登録されている誕生日一覧\n{message}", ephemeral=True
    )


@app_commands.command(
    description="誕生日を消します(memberが指定されていない場合は自分の誕生日を消します)"
)
@app_commands.describe(member="消す対象の人")
async def rm(interaction: Interaction, member: Member = None):
    if member:
        member_id = member.id
    else:
        member = interaction.user
        member_id = member.id

    delete_target = {
        "member_id": member_id,
        "server_id": interaction.guild_id,
    }
    table = MemberTable()
    if not table.record_exists(delete_target):
        await interaction.response.send_message(
            "誕生日が登録されていません", ephemeral=True
        )
        return

    table.delete(delete_target)

    await interaction.response.send_message(
        f"{member.display_name}の誕生日を消しました", ephemeral=True
    )


@app_commands.command(description="誕生日メッセージの送信先を設定します")
@app_commands.describe(channel="送信先のチャンネル")
async def send_to(interaction: Interaction, channel: TextChannel = None):
    if not channel:
        channel = interaction.channel

    table = ChannelTable()
    data = {"server_id": interaction.guild_id, "channel_id": channel.id}

    if table.record_exists(data):
        table.update(data)
    else:
        table.insert(data)

    await interaction.response.send_message(
        f"誕生日メッセージの送信先を{channel.mention}に設定しました",
        ephemeral=True,
    )


@app_commands.command(description="誕生日メッセージの送信を停止します")
@app_commands.describe()
async def stop(interaction: Interaction):
    table = ChannelTable()
    table.delete({"server_id": interaction.guild_id})

    await interaction.response.send_message(
        "誕生日メッセージの送信を停止しました",
        ephemeral=True,
    )
