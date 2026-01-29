"""
Memory Service Singleton

Shared MemoryService instance for all game components.
Configured with OpenRouter LLM profiles for different AI agents.
"""

import os
from typing import Any

# Try to import MemoryService, but don't fail if not available
try:
    from memu.app import MemoryService
    MEMU_AVAILABLE = True
except ImportError:
    MEMU_AVAILABLE = False
    MemoryService = None

from .config import memorize_config, retrieve_config


# Singleton instance
_SHARED_MEMORY_SERVICE: Any = None


def get_memory_service() -> Any:
    """
    Get or create the shared MemoryService instance.

    Uses OpenRouter for all LLM profiles with different models:
    - default: Claude 3.5 Sonnet (for memory operations)
    - claude_agent: Claude 3.5 Sonnet
    - gpt_agent: GPT-4o
    - llama_agent: Llama 3.1 70B

    Returns:
        MemoryService instance or None if memu is not available
    """
    global _SHARED_MEMORY_SERVICE

    if not MEMU_AVAILABLE:
        print("[Warning] memu package not available, memory features disabled")
        return None

    if _SHARED_MEMORY_SERVICE is not None:
        return _SHARED_MEMORY_SERVICE

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("[Warning] OPENROUTER_API_KEY not set, memory features disabled")
        return None

    try:
        _SHARED_MEMORY_SERVICE = MemoryService(
            llm_profiles={
                "default": {
                    "provider": "openrouter",
                    "client_backend": "httpx",
                    "base_url": "https://openrouter.ai/api/v1",
                    "api_key": api_key,
                    "chat_model": "anthropic/claude-3.5-sonnet",
                    "embed_model": "openai/text-embedding-3-small",
                },
                "claude_agent": {
                    "provider": "openrouter",
                    "client_backend": "httpx",
                    "base_url": "https://openrouter.ai/api/v1",
                    "api_key": api_key,
                    "chat_model": "anthropic/claude-3.5-sonnet",
                    "embed_model": "openai/text-embedding-3-small",
                },
                "gpt_agent": {
                    "provider": "openrouter",
                    "client_backend": "httpx",
                    "base_url": "https://openrouter.ai/api/v1",
                    "api_key": api_key,
                    "chat_model": "openai/gpt-4o",
                    "embed_model": "openai/text-embedding-3-small",
                },
                "llama_agent": {
                    "provider": "openrouter",
                    "client_backend": "httpx",
                    "base_url": "https://openrouter.ai/api/v1",
                    "api_key": api_key,
                    "chat_model": "meta-llama/llama-3.1-70b-instruct",
                    "embed_model": "openai/text-embedding-3-small",
                },
            },
            memorize_config=memorize_config,
            retrieve_config=retrieve_config,
        )
        print("[Memory] MemoryService initialized successfully")
    except Exception as e:
        print(f"[Warning] Failed to initialize MemoryService: {e}")
        _SHARED_MEMORY_SERVICE = None

    return _SHARED_MEMORY_SERVICE


def reset_memory_service() -> None:
    """Reset the memory service singleton (for testing)"""
    global _SHARED_MEMORY_SERVICE
    _SHARED_MEMORY_SERVICE = None
