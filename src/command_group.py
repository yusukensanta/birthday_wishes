import logging

from discord import Interaction, Member, TextChannel, app_commands

from src.model import Birthday, BirthdayChannel
from src.table_manager import BirthdayManager, ChannelManager

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
    data = {}
    data["birth_month"] = month
    data["birth_day"] = day
    if member:
        data["member_id"] = member.id
        display_name = member.display_name
    else:
        data["member_id"] = interaction.user.id
        display_name = interaction.user.display_name
    data["server_id"] = interaction.guild_id

    try:
        birthday = Birthday(**data)
    except ValueError as e:
        await interaction.response.send_message(
            f"登録に失敗しました: {repr(e)}", ephemeral=True
        )
        return

    manager = BirthdayManager()
    if manager.record_exists(birthday):
        manager.update(birthday)
        logger.info(f"Updated data `{birthday.dict()}`")
        await interaction.response.send_message(
            f"`{display_name}`の誕生日を{birthday.birth_month}月{birthday.birth_day}日で更新しました"
        )
    else:
        manager.insert(birthday)
        logger.info(f"Inserted data `{birthday.dict()}`")
        await interaction.response.send_message(
            f"`{display_name}`の誕生日を{birthday.birth_month}月{birthday.birth_day}日で登録しました"
        )


@app_commands.command(description="登録されている誕生日のリストを表示します")
async def ls(interaction: Interaction):
    manager = BirthdayManager()
    members = manager.list_all()
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
            # display_name can be changed by user
            # so get latest display name from discord
            members[index]["display_name"] = discord_user.display_name
        else:
            members[index]["display_name"] = "すでに退出したユーザー"

    message = "\n".join(
        [
            f"""{member['display_name']} :
            {member['birth_month']}月{member['birth_day']}日"""
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
        member = interaction.user  # to get display name
        member_id = member.id

    delete_target = {
        "member_id": member_id,
        "server_id": interaction.guild_id,
    }
    birthday = Birthday(**delete_target)
    manager = BirthdayManager()
    if not manager.record_exists(birthday):
        await interaction.response.send_message(
            "誕生日が登録されていません", ephemeral=True
        )
        return

    manager.delete(birthday)

    await interaction.response.send_message(
        f"{member.display_name}の誕生日を消しました", ephemeral=True
    )


@app_commands.command(description="誕生日メッセージの送信先を設定します")
@app_commands.describe(channel="送信先のチャンネル")
async def send_to(interaction: Interaction, channel: TextChannel = None):
    if not channel:
        channel = interaction.channel

    manager = ChannelManager()
    data = {"server_id": interaction.guild_id, "channel_id": channel.id}

    birthday_channel = BirthdayChannel(**data)
    if manager.record_exists(birthday_channel):
        manager.update(birthday_channel)
    else:
        manager.insert(birthday_channel)

    await interaction.response.send_message(
        f"誕生日メッセージの送信先を{channel.mention}に設定しました",
        ephemeral=True,
    )


@app_commands.command(description="誕生日メッセージの送信を停止します")
@app_commands.describe()
async def stop(interaction: Interaction):
    manager = ChannelManager()
    birthday_channel = BirthdayChannel(server_id=interaction.guild_id)
    manager.delete(birthday_channel)
    await interaction.response.send_message(
        "誕生日メッセージの送信を停止しました",
        ephemeral=True,
    )
