import pytest

import app as vibe_chat


@pytest.fixture
def client():
    # Start every test with an empty message list.
    vibe_chat.messages.clear()
    vibe_chat.app.config["TESTING"] = True
    with vibe_chat.app.test_client() as client:
        yield client


def test_empty_name_is_rejected(client):
    response = client.post("/", data={"name": "", "status": "Present", "message": "hello"})
    assert response.status_code == 400
    assert b"User name cannot be empty." in response.data
    assert vibe_chat.messages == []


def test_empty_message_is_rejected(client):
    response = client.post("/", data={"name": "Ada", "status": "Present", "message": ""})
    assert response.status_code == 400
    assert b"Message cannot be empty." in response.data
    assert vibe_chat.messages == []
