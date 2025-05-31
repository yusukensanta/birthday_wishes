import pytest
from pydantic import ValidationError
from src.model import ScheduledMessage

def test_scheduled_message_creation_success():
    msg = ScheduledMessage(
        message_id="test_id_123",
        server_id=12345,
        channel_id=67890,
        user_id=11223,
        message_content="Hello world",
        cron_expression="* * * * *"
    )
    assert msg.message_id == "test_id_123"
    assert msg.server_id == 12345
    assert msg.channel_id == 67890
    assert msg.user_id == 11223
    assert msg.message_content == "Hello world"
    assert msg.cron_expression == "* * * * *"

def test_scheduled_message_invalid_cron_empty():
    with pytest.raises(ValidationError) as excinfo:
        ScheduledMessage(
            message_id="test_id_empty_cron",
            server_id=12345,
            channel_id=67890,
            user_id=11223,
            message_content="Hello world",
            cron_expression="" # Empty cron expression
        )
    # Check that the error message is related to the cron_expression field
    # and its specific validator message if possible.
    # Pydantic v2 gives a list of errors.
    assert len(excinfo.value.errors()) == 1
    assert excinfo.value.errors()[0]['loc'] == ('cron_expression',)
    assert "cron_expression cannot be empty" in excinfo.value.errors()[0]['msg']

def test_scheduled_message_field_types():
    # Test with incorrect types to ensure Pydantic validation catches them
    with pytest.raises(ValidationError):
        ScheduledMessage(
            message_id=123, # incorrect type
            server_id="abc", # incorrect type
            channel_id="def", # incorrect type
            user_id="ghi", # incorrect type
            message_content=True, # incorrect type
            cron_expression="* * * * *"
        )

    # Example of checking a specific field's error
    with pytest.raises(ValidationError) as excinfo:
        ScheduledMessage(
            message_id="correct_id",
            server_id="not_an_int", # incorrect type
            channel_id=67890,
            user_id=11223,
            message_content="Hello world",
            cron_expression="* * * * *"
        )
    assert len(excinfo.value.errors()) == 1
    assert excinfo.value.errors()[0]['type'] == 'int_parsing'
    assert excinfo.value.errors()[0]['loc'] == ('server_id',)
