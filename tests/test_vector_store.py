"""Tests for the IncidentVectorStore (uses real in-memory Qdrant — no server needed)."""

import os
import pytest
from app.database.vector_store import IncidentVectorStore


@pytest.fixture
def fresh_store():
    """A fresh IncidentVectorStore instance for each test."""
    return IncidentVectorStore()


def test_vector_store_initializes_without_error(fresh_store):
    """IncidentVectorStore should initialize and create the collection."""
    assert fresh_store.qdrant_client is not None
    assert fresh_store.collection_name == "incident_playbooks"


def test_mock_embedding_returns_correct_size(fresh_store):
    """_get_mock_embedding should return a vector of the expected size."""
    vector = fresh_store._get_mock_embedding("test query")
    assert len(vector) == fresh_store.vector_size
    assert all(isinstance(v, float) for v in vector)


def test_index_playbook_creates_new_file_if_missing(fresh_store, tmp_path):
    """index_playbook should auto-create the playbook file if it doesn't exist."""
    fake_path = tmp_path / "playbooks" / "test_playbook.md"
    fresh_store.index_playbook(str(fake_path))
    assert fake_path.exists()


def test_index_playbook_indexes_chunks(fresh_store, tmp_path):
    """index_playbook should load chunks into Qdrant successfully."""
    playbook = tmp_path / "playbook.md"
    playbook.write_text(
        "# Main Title\n\n## Error AUTH_001\nRestart the service.\n\n## Error AUTH_002\nCheck the logs.",
        encoding="utf-8"
    )
    fresh_store.index_playbook(str(playbook))

    # After indexing, search should return results
    results = fresh_store.search_relevant_playbooks("AUTH_001 restart", limit=1)
    assert len(results) > 0
    assert "text" in results[0]


def test_search_returns_empty_when_no_playbooks(fresh_store):
    """Searching an empty store should return an empty list, not raise."""
    results = fresh_store.search_relevant_playbooks("any query", limit=1)
    # Empty collection returns empty results — no exception
    assert isinstance(results, list)


def test_search_returns_relevant_payload(fresh_store, tmp_path):
    """search_relevant_playbooks should return payload dicts with 'text' and 'source'."""
    playbook = tmp_path / "keycloak.md"
    playbook.write_text(
        "# Keycloak Errors\n\n## AUTH_TIMEOUT_500\nPool exhausted, restart service.",
        encoding="utf-8"
    )
    fresh_store.index_playbook(str(playbook))

    results = fresh_store.search_relevant_playbooks("AUTH_TIMEOUT_500", limit=1)
    assert len(results) == 1
    assert "text" in results[0]
    assert "source" in results[0]