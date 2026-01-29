"""
Game Event Memorization

Functions to store game events in the MemoryService for AI learning.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .common import get_memory_service


# Data directory for memory resources
DATA_DIR = Path(__file__).parent / "data"


def ensure_data_dir() -> Path:
    """Ensure the data directory exists"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def format_game_event(
    event_type: str,
    player_id: str | None = None,
    details: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Format a game event for storage"""
    return {
        "event_type": event_type,
        "player_id": player_id,
        "details": details or {},
        "timestamp": datetime.now().isoformat()
    }


def dump_events_to_file(
    events: list[dict[str, Any]],
    agent_id: str
) -> str | None:
    """
    Save game events to a JSON file for memorization.

    Args:
        events: List of game events
        agent_id: ID of the agent these events are for

    Returns:
        Path to the saved file, or None if failed
    """
    try:
        ensure_data_dir()

        # Format as conversation resource for MemoryService
        resource_data = {
            "content": [
                {
                    "role": "system",
                    "content": {"text": json.dumps(event, ensure_ascii=False)},
                    "created_at": event.get("timestamp", datetime.now().isoformat())
                }
                for event in events
            ]
        }

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"game_{agent_id}_{timestamp}.json"
        filepath = DATA_DIR / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(resource_data, f, indent=2, ensure_ascii=False)

        return filepath.as_posix()

    except Exception as e:
        print(f"[Memory] Failed to dump events: {e}")
        return None


async def memorize_game_events(
    events: list[dict[str, Any]],
    agent_id: str
) -> dict[str, Any] | None:
    """
    Memorize game events for an agent.

    Args:
        events: List of game events to memorize
        agent_id: ID of the agent

    Returns:
        Memorization result or None if failed
    """
    memory_service = get_memory_service()
    if memory_service is None:
        return None

    # Save events to file
    resource_url = dump_events_to_file(events, agent_id)
    if resource_url is None:
        return None

    try:
        result = await memory_service.memorize(
            resource_url=resource_url,
            modality="conversation",
            user={"agent_id": agent_id}
        )
        print(f"[Memory] Memorized {len(events)} events for {agent_id}")
        return result

    except Exception as e:
        print(f"[Memory] Memorization failed: {e}")
        return None


async def retrieve_memories(
    query: str,
    agent_id: str,
    top_k: int = 5
) -> list[dict[str, Any]]:
    """
    Retrieve relevant memories for an agent.

    Args:
        query: Search query
        agent_id: ID of the agent
        top_k: Number of memories to retrieve

    Returns:
        List of relevant memories
    """
    memory_service = get_memory_service()
    if memory_service is None:
        return []

    try:
        result = await memory_service.retrieve(
            queries=[{"role": "user", "content": query}],
            where={"agent_id": agent_id}
        )
        return result.get("items", [])[:top_k]

    except Exception as e:
        print(f"[Memory] Retrieval failed: {e}")
        return []


def create_bluff_event(
    player_id: str,
    was_bluff: bool,
    cards_or_bid: str,
    claim: str,
    caught: bool | None = None,
    round_number: int = 0
) -> dict[str, Any]:
    """Create a bluff event"""
    return format_game_event(
        event_type="bluff",
        player_id=player_id,
        details={
            "was_bluff": was_bluff,
            "cards_or_bid": cards_or_bid,
            "claim": claim,
            "caught": caught,
            "round": round_number
        }
    )


def create_challenge_event(
    challenger_id: str,
    challenged_id: str,
    was_correct: bool,
    loser_id: str,
    survived_roulette: bool,
    round_number: int = 0
) -> dict[str, Any]:
    """Create a challenge event"""
    return format_game_event(
        event_type="challenge",
        player_id=challenger_id,
        details={
            "challenged": challenged_id,
            "correct_challenge": was_correct,
            "loser": loser_id,
            "survived_roulette": survived_roulette,
            "round": round_number
        }
    )


def create_elimination_event(
    player_id: str,
    eliminated_by: str,
    round_number: int = 0
) -> dict[str, Any]:
    """Create an elimination event"""
    return format_game_event(
        event_type="elimination",
        player_id=player_id,
        details={
            "eliminated_by": eliminated_by,
            "round": round_number
        }
    )


def create_game_over_event(
    winner_id: str,
    total_rounds: int,
    player_stats: dict[str, Any]
) -> dict[str, Any]:
    """Create a game over event"""
    return format_game_event(
        event_type="game_over",
        player_id=winner_id,
        details={
            "total_rounds": total_rounds,
            "player_stats": player_stats
        }
    )
