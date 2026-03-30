from src.domain.models.message import Message


def test_message_creation(db_session):
    msg = Message(
        channel_id="C123",
        thread_ts="1234567890.000100",
        user="U456",
        text="Hello",
        timestamp="1234567890.000100",
    )
    db_session.add(msg)
    db_session.commit()
    db_session.refresh(msg)
    assert msg.id is not None
    assert msg.channel_id == "C123"
    assert msg.user == "U456"
    assert msg.text == "Hello"
    assert msg.created_at is not None


def test_message_thread_ts_optional(db_session):
    msg = Message(
        channel_id="C123",
        thread_ts=None,
        user="U456",
        text="Hello",
        timestamp="1234567890.000100",
    )
    db_session.add(msg)
    db_session.commit()
    assert msg.thread_ts is None
