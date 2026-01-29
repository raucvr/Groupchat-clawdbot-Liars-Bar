"""
Memory Configuration for Liar's Bar

Defines memory categories, types, and prompts for AI agents.
"""

# Memory types for game events
MEMORY_TYPES = [
    "game_event",
    "strategy",
    "player_profile"
]

# Memory type prompts for extraction
MEMORY_TYPE_PROMPTS = {
    "game_event": {
        "objective": {
            "ordinal": 10,
            "prompt": """# Task Objective
Extract game events from the Liar's Bar game log. Focus on:
- Bluff attempts and their outcomes (caught or successful)
- Challenge decisions and results
- Russian roulette outcomes (survived or eliminated)
- Winning and losing patterns
- Card/dice plays and claims made"""
        },
        "workflow": {
            "ordinal": 20,
            "prompt": """# Workflow
Read through the game events and extract:
1. Who bluffed and when (player, round, cards/dice involved)
2. Challenge successes and failures
3. Player elimination events
4. Strategic turning points in the game
5. Patterns of aggressive vs conservative play"""
        },
        "examples": {
            "ordinal": 60,
            "prompt": """# Example Output
<item>
    <memory>
        <content>Claude bluffed with 2 Kings claiming Aces in round 3, was challenged by GPT and lost, survived roulette</content>
        <categories>
            <category>bluff_history</category>
            <category>claude_profile</category>
        </categories>
    </memory>
</item>
<item>
    <memory>
        <content>Human player successfully bluffed 3 Queens as Kings, not challenged</content>
        <categories>
            <category>bluff_history</category>
            <category>human_profile</category>
        </categories>
    </memory>
</item>"""
        }
    },
    "strategy": {
        "objective": {
            "ordinal": 10,
            "prompt": """# Task Objective
Extract strategic insights and patterns from game events. Learn what works and what doesn't in Liar's Bar."""
        },
        "workflow": {
            "ordinal": 20,
            "prompt": """# Workflow
Analyze game outcomes to identify:
1. Successful bluffing strategies (timing, frequency, card combinations)
2. Patterns that get caught (overbluffing, predictable behavior)
3. Optimal challenge timing (when to call Liar!)
4. Risk assessment for roulette (when to play safe)
5. Adaptation strategies based on opponent behavior"""
        },
        "examples": {
            "ordinal": 60,
            "prompt": """# Example Output
<item>
    <memory>
        <content>Bluffing with 2 cards is safer than 3 cards - higher success rate observed</content>
        <categories>
            <category>winning_strategies</category>
        </categories>
    </memory>
</item>"""
        }
    },
    "player_profile": {
        "objective": {
            "ordinal": 10,
            "prompt": """# Task Objective
Build profiles of each player's tendencies and playing style in Liar's Bar."""
        },
        "workflow": {
            "ordinal": 20,
            "prompt": """# Workflow
Track for each player:
1. Bluff frequency (how often they lie)
2. Challenge aggression (how often they call Liar!)
3. Risk tolerance (conservative vs aggressive plays)
4. Predictability patterns (tells, consistent behaviors)
5. Performance under pressure (roulette survival history)"""
        },
        "examples": {
            "ordinal": 60,
            "prompt": """# Example Output
<item>
    <memory>
        <content>GPT tends to bluff more in early rounds, becomes conservative after surviving roulette</content>
        <categories>
            <category>gpt_profile</category>
        </categories>
    </memory>
</item>"""
        }
    }
}

# Memory categories for organizing memories
MEMORY_CATEGORIES = [
    {
        "name": "bluff_history",
        "description": "History of bluffs made and their outcomes - who bluffed, what they claimed, if they were caught",
        "target_length": 500
    },
    {
        "name": "challenge_history",
        "description": "History of challenges made and their results - who challenged whom, was it correct",
        "target_length": 500
    },
    {
        "name": "claude_profile",
        "description": "Playing patterns and tendencies of the Claude AI agent",
        "target_length": 300
    },
    {
        "name": "gpt_profile",
        "description": "Playing patterns and tendencies of the GPT AI agent",
        "target_length": 300
    },
    {
        "name": "llama_profile",
        "description": "Playing patterns and tendencies of the Llama AI agent",
        "target_length": 300
    },
    {
        "name": "human_profile",
        "description": "Playing patterns and tendencies of the human player",
        "target_length": 300
    },
    {
        "name": "winning_strategies",
        "description": "Strategies that led to game wins - successful bluffing techniques, optimal challenge timing",
        "target_length": 400
    },
    {
        "name": "game_statistics",
        "description": "Overall game statistics and trends - win rates, elimination patterns, round outcomes",
        "target_length": 300
    }
]

# Memorize configuration
memorize_config = {
    "memory_types": MEMORY_TYPES,
    "memory_type_prompts": MEMORY_TYPE_PROMPTS,
    "memory_categories": MEMORY_CATEGORIES,
}

# Retrieve configuration
retrieve_config = {
    "method": "rag",
    "route_intention": False,
    "sufficiency_check": False,
    "category": {"enabled": True, "top_k": 5},
    "item": {"enabled": True, "top_k": 10},
    "resource": {"enabled": False}
}
