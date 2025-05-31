import logging
import uuid # Added for message_id generation

from croniter import croniter # Added for cron validation
from discord import Embed, Interaction, Member, TextChannel, app_commands

from src.model import Birthday, BirthdayChannel, ScheduledMessage # Added ScheduledMessage
from src.table_manager import ( # Added ScheduledMessageManager
    BirthdayManager,
    ChannelManager,
    ScheduledMessageManager,
)

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
        self.add_command(help)


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
            f"`{display_name}`の誕生日を{birthday.birth_month}月{birthday.birth_day}日で更新しました",
            ephemeral=True,
        )
    else:
        manager.insert(birthday)
        logger.info(f"Inserted data `{birthday.dict()}`")
        await interaction.response.send_message(
            f"`{display_name}`の誕生日を{birthday.birth_month}月{birthday.birth_day}日で登録しました",
            ephemeral=True,
        )


@app_commands.command(description="登録されている誕生日のリストを表示します")
async def ls(interaction: Interaction):
    manager = BirthdayManager()
    members = manager.list_all(interaction.guild_id)
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
            f"""{member['display_name']} : \
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
async def stop(interaction: Interaction):
    manager = ChannelManager()
    birthday_channel = BirthdayChannel(server_id=interaction.guild_id)
    manager.delete(birthday_channel)
    await interaction.response.send_message(
        """
        誕生日メッセージの送信を停止しました
        再開する場合は`/bd send_to`を実行してください"
        """,
        ephemeral=True,
    )


@app_commands.command(description="ヘルプを表示します")
async def help(interaction: Interaction):
    embed = Embed(
        title="Birthday Bot(ja)",
        description="""
            誕生日を管理するBotです。以下のコマンドが利用できます。\n
            - `/bd reg`: 誕生日の登録\n
            - `/bd ls`: 登録されている誕生日のリスト表示\n
            - `/bd rm`: 誕生日の登録削除\n
            - `/bd send_to`: 誕生日メッセージの送信先設定\n
            - `/bd stop`: 誕生日メッセージの送信停止\n
            - `/bd help`: ヘルプの表示\n
            `/`を入力してこのBotのアイコンをクリックするとコマンドが表示されます。
            """,
        color=0x00FF00,
    )
    await interaction.response.send_message(
        embed=embed,
        ephemeral=True,
    )


class ScheduleCommandGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="schedule", description="Manage scheduled messages")
        self.manager = ScheduledMessageManager()

    @app_commands.command(name="add", description="Schedule a new message.")
    @app_commands.describe(
        cron_expression="Cron expression (e.g., '0 0 * * *')",
        message_content="The message to schedule",
    )
    async def add(
        self,
        interaction: Interaction,
        cron_expression: str,
        message_content: str,
    ):
        if not croniter.is_valid_cron(cron_expression):
            await interaction.response.send_message(
                "Invalid cron expression format. Please use a valid cron string (e.g., '0 0 * * *').",
                ephemeral=True,
            )
            return

        message_id = str(uuid.uuid4())
        server_id = interaction.guild_id
        channel_id = interaction.channel_id # Use the channel where command was invoked
        user_id = interaction.user.id

        if server_id is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        if channel_id is None: # Should not happen if guild_id is present
            await interaction.response.send_message(
                "Could not determine the channel ID.", ephemeral=True
            )
            return


        scheduled_message = ScheduledMessage(
            message_id=message_id,
            server_id=server_id,
            channel_id=channel_id,
            user_id=user_id,
            message_content=message_content,
            cron_expression=cron_expression,
        )

        try:
            self.manager.insert(scheduled_message)
            logger.info(f"Inserted scheduled message: {scheduled_message.dict()}")
            await interaction.response.send_message(
                f"Message scheduled successfully! ID: `{message_id}`",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Failed to schedule message: {e}")
            await interaction.response.send_message(
                "Failed to schedule message. Please check logs.", ephemeral=True
            )

    @app_commands.command(name="list", description="List scheduled messages for this server.")
    async def list_messages(self, interaction: Interaction):
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        messages = self.manager.list_all(server_id=interaction.guild_id)

        if not messages:
            await interaction.response.send_message(
                "No messages scheduled for this server.", ephemeral=True
            )
            return

        response_lines = ["Scheduled messages:"]
        for msg_data in messages:
            # Ensure all keys are present, providing defaults if not
            msg_id = msg_data.get('message_id', 'N/A')
            cron = msg_data.get('cron_expression', 'N/A')
            content = msg_data.get('message_content', 'N/A')
            response_lines.append(
                f"- ID: `{msg_id}` | Cron: `{cron}` | Message: \"{content[:50]}{'...' if len(content) > 50 else ''}\""
            )

        # Discord has a 2000 character limit for messages
        full_response = "\n".join(response_lines)
        if len(full_response) > 2000:
            full_response = full_response[:1997] + "..."

        await interaction.response.send_message(full_response, ephemeral=True)

    @app_commands.command(name="remove", description="Remove a scheduled message by its ID.")
    @app_commands.describe(message_id="The ID of the message to remove")
    async def remove(self, interaction: Interaction, message_id: str):
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        # server_id is not strictly needed for the filter if message_id is global UUID
        # but good for context and if _filter_keys changes.
        # The model needs all non-optional fields if we were to create it fully.
        # For deletion, we only need what _filter_keys requires.
        # ScheduledMessageManager._filter_keys is ['message_id']
        delete_data_model = ScheduledMessage(
            message_id=message_id,
            server_id=interaction.guild_id, # Required by model, though not by filter_keys
            channel_id=0, # Dummy value, required by model
            user_id=0, # Dummy value, required by model
            message_content="", # Dummy value, required by model
            cron_expression="* * * * *", # Dummy value, required by model
        )

        if not self.manager.record_exists(delete_data_model):
            await interaction.response.send_message(
                f"No scheduled message found with ID: `{message_id}`",
                ephemeral=True,
            )
            return

        try:
            self.manager.delete(delete_data_model)
            logger.info(f"Removed scheduled message ID: {message_id} for server {interaction.guild_id}")
            await interaction.response.send_message(
                f"Successfully removed scheduled message ID: `{message_id}`",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Failed to remove scheduled message ID {message_id}: {e}")
            await interaction.response.send_message(
                "Failed to remove message. Please check logs.", ephemeral=True
            )
