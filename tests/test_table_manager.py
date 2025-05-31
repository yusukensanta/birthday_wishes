import pytest
import os
import tempfile
from tinydb import TinyDB
from src.table_manager import ScheduledMessageManager
from src.model import ScheduledMessage

@pytest.fixture
def db_manager():
    # Create a temporary file for the TinyDB database
    # tempfile.NamedTemporaryFile can simplify this
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp_db_file:
        db_path = tmp_db_file.name

    # Instantiate the manager
    manager = ScheduledMessageManager()

    # Override the client and table to use the temporary database.
    # BaseManager.__init__ sets up self.table.
    # client = TinyDB("/tmp/birthday_wishes.json")
    # self.table = client.table(type(self).__name__.lower())
    # For ScheduledMessageManager, table name will be 'scheduledmessagemanager'.

    temp_client = TinyDB(db_path)
    # The table name should be consistent with BaseManager's derivation.
    table_name = manager.__class__.__name__.lower()
    manager.table = temp_client.table(table_name)

    yield manager # Provide the configured manager to the test

    # Teardown: close the DB and remove the temporary file
    if hasattr(manager.table._db, '_storage'): # Check if DB is still open / has storage
      manager.table._db.close() # Close the TinyDB instance associated with the table

    # temp_client used for creating table, ensure it's closed if not closed by manager.table._db.close()
    # In TinyDB, closing the client that created the table instance is usually enough.
    # If manager.table._db is the same as temp_client, this is redundant but safe.
    # If they are different, this ensures the client used for table creation is also closed.
    # However, manager.table._db *is* temp_client in this setup.
    # temp_client.close() # Already handled by manager.table._db.close() if they are same.

    os.unlink(db_path)

# Helper function to create a sample message model instance
def create_sample_message_model(msg_id: str, server_id: int, content: str = "Test Content", cron: str = "* * * * *") -> ScheduledMessage:
    return ScheduledMessage(
        message_id=msg_id,
        server_id=server_id,
        channel_id=12345, # Default test channel_id
        user_id=67890,     # Default test user_id
        message_content=content,
        cron_expression=cron
    )

# --- Test Cases ---

def test_insert_and_get_message(db_manager: ScheduledMessageManager):
    msg1_model = create_sample_message_model("msg1", 100)
    db_manager.insert(msg1_model)

    # ScheduledMessageManager._filter_keys is ['message_id']
    # So, we need to pass a ScheduledMessage model with message_id for search/record_exists
    search_criteria_model = ScheduledMessage(message_id="msg1", server_id=100, channel_id=0, user_id=0, message_content="", cron_expression="")

    assert db_manager.record_exists(search_criteria_model)

    retrieved_messages = db_manager.search(search_criteria_model)
    assert len(retrieved_messages) == 1
    retrieved_msg_data = retrieved_messages[0]

    # Convert dict back to model for easier comparison if needed, or compare dict fields
    retrieved_model = ScheduledMessage(**retrieved_msg_data)
    assert retrieved_model.message_id == msg1_model.message_id
    assert retrieved_model.server_id == msg1_model.server_id
    assert retrieved_model.message_content == msg1_model.message_content
    assert retrieved_model.cron_expression == msg1_model.cron_expression

def test_list_all_messages_for_server(db_manager: ScheduledMessageManager):
    msg1_s1 = create_sample_message_model("msg1_s1", 100)
    msg2_s1 = create_sample_message_model("msg2_s1", 100, content="Another message for S1")
    msg1_s2 = create_sample_message_model("msg1_s2", 200)

    db_manager.insert(msg1_s1)
    db_manager.insert(msg2_s1)
    db_manager.insert(msg1_s2)

    server1_messages = db_manager.list_all(server_id=100)
    assert len(server1_messages) == 2
    # Check if message IDs are present (order might vary)
    retrieved_ids_s1 = {msg['message_id'] for msg in server1_messages}
    assert "msg1_s1" in retrieved_ids_s1
    assert "msg2_s1" in retrieved_ids_s1

    server2_messages = db_manager.list_all(server_id=200)
    assert len(server2_messages) == 1
    assert server2_messages[0]['message_id'] == "msg1_s2"

def test_list_all_no_messages(db_manager: ScheduledMessageManager):
    messages = db_manager.list_all(server_id=999) # Server with no messages
    assert len(messages) == 0

def test_delete_message(db_manager: ScheduledMessageManager):
    msg_to_delete_model = create_sample_message_model("msg_del", 300)
    db_manager.insert(msg_to_delete_model)

    # For record_exists and delete, we need a model with the filter key(s)
    criteria_model = ScheduledMessage(message_id="msg_del", server_id=300, channel_id=0, user_id=0, message_content="", cron_expression="")
    assert db_manager.record_exists(criteria_model)

    db_manager.delete(criteria_model)
    assert not db_manager.record_exists(criteria_model)
    assert len(db_manager.search(criteria_model)) == 0

def test_delete_nonexistent_message(db_manager: ScheduledMessageManager):
    # Create a model for a message that doesn't exist
    non_existent_criteria = ScheduledMessage(message_id="non_existent_msg", server_id=400, channel_id=0, user_id=0, message_content="", cron_expression="")

    # Ensure it doesn't exist
    assert not db_manager.record_exists(non_existent_criteria)

    # Attempt to delete it - should not raise an error
    try:
        db_manager.delete(non_existent_criteria)
    except Exception as e:
        pytest.fail(f"Deleting non-existent message raised an exception: {e}")

    # Verify it still doesn't exist and no new records were created
    assert not db_manager.record_exists(non_existent_criteria)

def test_update_message(db_manager: ScheduledMessageManager):
    original_msg_model = create_sample_message_model("msg_upd", 500, content="Original Content")
    db_manager.insert(original_msg_model)

    updated_msg_model = create_sample_message_model("msg_upd", 500, content="Updated Content")
    # Ensure other fields are the same as original if not intended to be updated by this model,
    # or ensure the update logic correctly handles partial updates if that's the design.
    # BaseManager.update replaces the whole dict.

    db_manager.update(updated_msg_model)

    search_criteria_model = ScheduledMessage(message_id="msg_upd", server_id=500, channel_id=0, user_id=0, message_content="", cron_expression="")
    retrieved_messages = db_manager.search(search_criteria_model)
    assert len(retrieved_messages) == 1
    retrieved_msg_data = retrieved_messages[0]

    assert retrieved_msg_data['message_id'] == "msg_upd"
    assert retrieved_msg_data['server_id'] == 500
    assert retrieved_msg_data['message_content'] == "Updated Content" # Key assertion
    assert retrieved_msg_data['cron_expression'] == original_msg_model.cron_expression # Assuming cron wasn't changed

def test_record_exists_false(db_manager: ScheduledMessageManager):
    criteria_model = ScheduledMessage(message_id="does_not_exist", server_id=600, channel_id=0, user_id=0, message_content="", cron_expression="")
    assert not db_manager.record_exists(criteria_model)

def test_update_nonexistent_message(db_manager: ScheduledMessageManager):
    # Attempt to update a message that doesn't exist.
    # BaseManager.update will insert if it doesn't find a record by filter_conditions.
    # This behavior might be desired or not, depending on requirements.
    # Current TinyDB behavior for table.update(doc, query) is that if query matches nothing, nothing happens.

    msg_to_update_model = create_sample_message_model("msg_upd_new", 700, content="Content for new update")

    # Ensure it doesn't exist
    search_criteria_model = ScheduledMessage(message_id="msg_upd_new", server_id=700, channel_id=0, user_id=0, message_content="", cron_expression="")
    assert not db_manager.record_exists(search_criteria_model)

    db_manager.update(msg_to_update_model) # This should not create a new record if it doesn't exist

    # Verify it was NOT created by update
    assert not db_manager.record_exists(search_criteria_model)
    retrieved = db_manager.search(search_criteria_model)
    assert len(retrieved) == 0
