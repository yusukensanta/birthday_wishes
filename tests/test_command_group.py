import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, ANY
import discord # Required for spec in mocks

# Imports for the code being tested
from src.command_group import ScheduleCommandGroup
from src.model import ScheduledMessage # Needed for type checking in assertions

# croniter is used by the command group, so it should be available in the test environment
# No need to mock croniter itself unless we want to test specific croniter failures
# beyond what the command group already handles (is_valid_cron).

@pytest.fixture
def mock_interaction():
    interaction = AsyncMock(spec=discord.Interaction)

    # Mock user
    interaction.user = MagicMock(spec=discord.User)
    interaction.user.id = 1234567890

    # Mock guild
    interaction.guild = MagicMock(spec=discord.Guild)
    interaction.guild.id = 9876543210
    interaction.guild_id = interaction.guild.id # Ensure guild_id is explicitly available

    # Mock channel
    # The channel object on an interaction can be various types,
    # but for guild commands, it's typically a TextChannel or similar.
    # Using a generic Messageable as spec might be too broad if specific channel attributes are accessed.
    # For channel_id, a simple MagicMock with an id attribute is often enough.
    interaction.channel = MagicMock(spec=discord.TextChannel)
    interaction.channel.id = 5555555555
    interaction.channel_id = interaction.channel.id # Ensure channel_id is explicitly available

    # Mock response object
    # discord.app_commands.InteractionResponse is not a real class for spec.
    # interaction.response is an instance of InteractionResponse.
    interaction.response = AsyncMock(spec=discord.InteractionResponse)
    interaction.response.send_message = AsyncMock()

    return interaction

@pytest.fixture
def command_group_instance():
    # Patch ScheduledMessageManager within the src.command_group module
    # where it's imported and used by ScheduleCommandGroup.
    with patch('src.command_group.ScheduledMessageManager') as MockManagerClass:
        # This is the mock instance that ScheduleCommandGroup's __init__ will receive
        mock_manager_instance = MockManagerClass.return_value

        # Set up mock methods for the manager instance
        mock_manager_instance.insert = MagicMock()
        mock_manager_instance.list_all = MagicMock()
        mock_manager_instance.delete = MagicMock()
        mock_manager_instance.record_exists = MagicMock()

        # Instantiate the command group. It will now use the mocked manager.
        group = ScheduleCommandGroup()

        # Attach the mock manager to the group instance for easier access in tests
        group.mock_manager = mock_manager_instance
        return group

# --- Test Cases for 'add' command ---
@pytest.mark.asyncio
async def test_add_message_success(command_group_instance: ScheduleCommandGroup, mock_interaction: AsyncMock):
    cron_expr = "*/5 * * * *"
    message_content = "This is a test message"

    # To capture the generated message_id, we can patch uuid.uuid4
    test_uuid = uuid.uuid4()
    with patch('src.command_group.uuid.uuid4', return_value=test_uuid):
        await command_group_instance.add(mock_interaction, cron_expr, message_content)

    # Assert interaction response
    mock_interaction.response.send_message.assert_called_once_with(
        f"Message scheduled successfully! ID: `{str(test_uuid)}`",
        ephemeral=True
    )

    # Assert manager.insert was called
    command_group_instance.mock_manager.insert.assert_called_once()
    # Check the argument passed to insert
    args, _ = command_group_instance.mock_manager.insert.call_args
    inserted_message: ScheduledMessage = args[0]

    assert isinstance(inserted_message, ScheduledMessage)
    assert inserted_message.message_id == str(test_uuid)
    assert inserted_message.server_id == mock_interaction.guild_id
    assert inserted_message.channel_id == mock_interaction.channel_id
    assert inserted_message.user_id == mock_interaction.user.id
    assert inserted_message.message_content == message_content
    assert inserted_message.cron_expression == cron_expr

@pytest.mark.asyncio
async def test_add_message_invalid_cron(command_group_instance: ScheduleCommandGroup, mock_interaction: AsyncMock):
    await command_group_instance.add(mock_interaction, "invalid-cron-string", "Test message")

    mock_interaction.response.send_message.assert_called_once_with(
        "Invalid cron expression format. Please use a valid cron string (e.g., '0 0 * * *').",
        ephemeral=True
    )
    command_group_instance.mock_manager.insert.assert_not_called()

@pytest.mark.asyncio
async def test_add_message_no_guild_id(command_group_instance: ScheduleCommandGroup, mock_interaction: AsyncMock):
    mock_interaction.guild_id = None # Simulate command used in DM or context where guild_id is not available
    await command_group_instance.add(mock_interaction, "* * * * *", "Test message")
    mock_interaction.response.send_message.assert_called_once_with(
        "This command can only be used in a server.", ephemeral=True
    )
    command_group_instance.mock_manager.insert.assert_not_called()


# --- Test Cases for 'list' command ---
@pytest.mark.asyncio
async def test_list_messages_success(command_group_instance: ScheduleCommandGroup, mock_interaction: AsyncMock):
    sample_messages_data = [
        {"message_id": "id1", "cron_expression": "0 0 * * *", "message_content": "Message 1"},
        {"message_id": "id2", "cron_expression": "0 12 * * *", "message_content": "Message 2 very long to test truncation feature of the list command which should be implemented."},
    ]
    command_group_instance.mock_manager.list_all.return_value = sample_messages_data

    await command_group_instance.list_messages(mock_interaction) # list_messages is the method name

    command_group_instance.mock_manager.list_all.assert_called_once_with(server_id=mock_interaction.guild_id)

    expected_response_part1 = "ID: `id1` | Cron: `0 0 * * *` | Message: \"Message 1\""
    # Message 2 content is 66 chars long, so it will be truncated at 50 + "..."
    expected_response_part2 = "ID: `id2` | Cron: `0 12 * * *` | Message: \"Message 2 very long to test truncation feature of...\""

    # Check that send_message was called, and its content contains the formatted messages
    args, _ = mock_interaction.response.send_message.call_args
    actual_response_message = args[0]

    assert "Scheduled messages:" in actual_response_message
    assert expected_response_part1 in actual_response_message
    assert expected_response_part2 in actual_response_message
    mock_interaction.response.send_message.assert_called_once_with(ANY, ephemeral=True)


@pytest.mark.asyncio
async def test_list_messages_empty(command_group_instance: ScheduleCommandGroup, mock_interaction: AsyncMock):
    command_group_instance.mock_manager.list_all.return_value = []
    await command_group_instance.list_messages(mock_interaction) # list_messages is the method name

    command_group_instance.mock_manager.list_all.assert_called_once_with(server_id=mock_interaction.guild_id)
    mock_interaction.response.send_message.assert_called_once_with(
        "No messages scheduled for this server.", ephemeral=True
    )

# --- Test Cases for 'remove' command ---
@pytest.mark.asyncio
async def test_remove_message_success(command_group_instance: ScheduleCommandGroup, mock_interaction: AsyncMock):
    message_id_to_remove = "existing_id_123"
    command_group_instance.mock_manager.record_exists.return_value = True

    await command_group_instance.remove(mock_interaction, message_id_to_remove)

    # Check record_exists was called correctly
    command_group_instance.mock_manager.record_exists.assert_called_once()
    args_re, _ = command_group_instance.mock_manager.record_exists.call_args
    model_re: ScheduledMessage = args_re[0]
    assert model_re.message_id == message_id_to_remove
    assert model_re.server_id == mock_interaction.guild_id # Important for context

    # Check delete was called correctly
    command_group_instance.mock_manager.delete.assert_called_once()
    args_del, _ = command_group_instance.mock_manager.delete.call_args
    model_del: ScheduledMessage = args_del[0]
    assert model_del.message_id == message_id_to_remove
    assert model_del.server_id == mock_interaction.guild_id

    # Check response
    mock_interaction.response.send_message.assert_called_once_with(
        f"Successfully removed scheduled message ID: `{message_id_to_remove}`",
        ephemeral=True
    )

@pytest.mark.asyncio
async def test_remove_message_not_found(command_group_instance: ScheduleCommandGroup, mock_interaction: AsyncMock):
    message_id_to_remove = "non_existent_id_456"
    command_group_instance.mock_manager.record_exists.return_value = False

    await command_group_instance.remove(mock_interaction, message_id_to_remove)

    command_group_instance.mock_manager.record_exists.assert_called_once()
    command_group_instance.mock_manager.delete.assert_not_called()
    mock_interaction.response.send_message.assert_called_once_with(
        f"No scheduled message found with ID: `{message_id_to_remove}`",
        ephemeral=True
    )
