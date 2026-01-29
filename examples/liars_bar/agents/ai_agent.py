"""
AI Agent Implementation

AI player using OpenRouter API with memory integration.
"""

import json
import random
import re
from typing import Union, Any

import httpx

from game.constants import GameMode, CardType, DECK_CLAIMABLE_TYPES
from game.models import (
    Player,
    GameState,
    DeckAction,
    DiceAction,
)
from memory.memorize import retrieve_memories, create_bluff_event, create_challenge_event
from .base_agent import BaseAgent
from .personalities import get_agent_config, get_system_prompt, AgentConfig


class AIAgent(BaseAgent):
    """
    AI player that uses OpenRouter API for decision making.

    Features:
    - Configurable personality via agent configs
    - Memory integration for learning from past games
    - Different LLM models for each agent
    """

    def __init__(
        self,
        player: Player,
        api_key: str,
        agent_key: str,
    ):
        """
        Initialize the AI agent.

        Args:
            player: Player model
            api_key: OpenRouter API key
            agent_key: Key to agent configuration (claude, gpt, llama)
        """
        super().__init__(player)
        self.api_key = api_key
        self.agent_key = agent_key
        self.config: AgentConfig = get_agent_config(agent_key) or {}
        self.model_id = self.config.get("model_id", "anthropic/claude-3.5-sonnet")
        self.base_url = "https://openrouter.ai/api/v1"

        # Track events for memorization
        self.game_events: list[dict[str, Any]] = []

    async def _query_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> str:
        """
        Query the LLM via OpenRouter API.

        Args:
            system_prompt: System message
            user_prompt: User message
            temperature: Sampling temperature

        Returns:
            LLM response text
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://liars-bar-game.local",
                        "X-Title": "Liars Bar Game"
                    },
                    json={
                        "model": self.model_id,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": temperature,
                        "max_tokens": 500
                    },
                    timeout=30.0
                )

                if response.status_code != 200:
                    print(f"[AI] API error: {response.status_code} - {response.text}")
                    return ""

                data = response.json()
                return data["choices"][0]["message"]["content"]

            except Exception as e:
                print(f"[AI] Query failed: {e}")
                return ""

    async def _get_memories(self, query: str) -> str:
        """Retrieve relevant memories and format them"""
        memories = await retrieve_memories(query, self.player_id, top_k=5)

        if not memories:
            return "No previous game memories."

        memory_texts = []
        for mem in memories:
            content = mem.get("content", mem.get("summary", ""))
            if content:
                memory_texts.append(f"- {content}")

        return "Relevant memories from past games:\n" + "\n".join(memory_texts)

    def _parse_json_from_response(self, response: str) -> dict[str, Any]:
        """Extract JSON from LLM response"""
        # Try to find JSON in the response
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Try parsing the whole response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        return {}

    async def decide_action(self, state: GameState) -> Union[DeckAction, DiceAction]:
        """Decide what action to take"""
        if state.mode == GameMode.LIARS_DECK:
            return await self._decide_deck_action(state)
        else:
            return await self._decide_dice_action(state)

    async def _decide_deck_action(self, state: GameState) -> DeckAction:
        """Decide action for Liar's Deck mode"""
        visible_state = self.get_visible_state(state)
        memories = await self._get_memories("deck bluffing strategy card game")

        system_prompt = get_system_prompt(self.agent_key)
        user_prompt = f"""Current game state:
- Round: {visible_state['round_number']}
- Target card for this round: {visible_state['current_round_claim']}
- Your hand: {[c.value for c in self.player.hand]}
- Cards on table: {visible_state['cards_on_table']}
- Roulette shots fired: {visible_state['roulette_shots_fired']}

Players:
{json.dumps(visible_state['players'], indent=2)}

Recent actions this round:
{json.dumps(visible_state['action_history'][-5:], indent=2)}

{memories}

What cards do you play and what do you claim? You must play 1-3 cards.
Respond with JSON: {{"action": "play", "cards": ["Q", "K"], "claim": "K"}}"""

        response = await self._query_llm(system_prompt, user_prompt)
        parsed = self._parse_json_from_response(response)

        # Parse or fallback to random action
        return self._create_deck_action(parsed, state)

    def _create_deck_action(self, parsed: dict, state: GameState) -> DeckAction:
        """Create a DeckAction from parsed response or generate random"""
        target = state.current_round_claim or random.choice(DECK_CLAIMABLE_TYPES)

        # Try to use parsed response
        if parsed.get("action") == "play" and "cards" in parsed:
            try:
                cards_str = parsed["cards"]
                claim_str = parsed.get("claim", target.value)

                # Parse cards
                cards = []
                for c in cards_str[:3]:  # Max 3 cards
                    card_upper = c.upper()
                    if card_upper in ["Q", "QUEEN"]:
                        cards.append(CardType.QUEEN)
                    elif card_upper in ["K", "KING"]:
                        cards.append(CardType.KING)
                    elif card_upper in ["A", "ACE"]:
                        cards.append(CardType.ACE)
                    elif card_upper in ["JOKER", "J"]:
                        cards.append(CardType.JOKER)

                # Validate cards are in hand
                hand_copy = self.player.hand.copy()
                valid_cards = []
                for card in cards:
                    if card in hand_copy:
                        valid_cards.append(card)
                        hand_copy.remove(card)

                if valid_cards:
                    # Parse claim
                    claim_upper = claim_str.upper()
                    if claim_upper in ["Q", "QUEEN"]:
                        claim = CardType.QUEEN
                    elif claim_upper in ["K", "KING"]:
                        claim = CardType.KING
                    elif claim_upper in ["A", "ACE"]:
                        claim = CardType.ACE
                    else:
                        claim = target

                    return DeckAction.create(self.player_id, valid_cards, claim)

            except Exception as e:
                print(f"[AI] Failed to parse action: {e}")

        # Fallback: random action based on personality
        return self._random_deck_action(state)

    def _random_deck_action(self, state: GameState) -> DeckAction:
        """Generate a random deck action based on personality"""
        target = state.current_round_claim or random.choice(DECK_CLAIMABLE_TYPES)
        hand = self.player.hand.copy()

        if not hand:
            # Edge case: empty hand
            return DeckAction.create(self.player_id, [], target)

        # Decide how many cards to play (1-3)
        max_cards = min(3, len(hand))
        num_cards = random.randint(1, max_cards)

        # Based on bluff tendency, decide whether to bluff
        bluff_tendency = self.config.get("bluff_tendency", 0.5)
        should_bluff = random.random() < bluff_tendency

        # Find matching cards
        matching = [c for c in hand if c == target or c == CardType.JOKER]

        if should_bluff or len(matching) < num_cards:
            # Bluff: play random cards and claim they match
            cards = random.sample(hand, num_cards)
        else:
            # Truth: play matching cards
            cards = matching[:num_cards]

        return DeckAction.create(self.player_id, cards, target)

    async def _decide_dice_action(self, state: GameState) -> DiceAction:
        """Decide action for Liar's Dice mode"""
        visible_state = self.get_visible_state(state)
        memories = await self._get_memories("dice bidding bluffing strategy")

        system_prompt = get_system_prompt(self.agent_key)

        current_bid_str = "No current bid - you start"
        if visible_state["current_bid"]:
            cb = visible_state["current_bid"]
            current_bid_str = f"{cb['count']}x {cb['face']}'s by {cb['player_id']}"

        user_prompt = f"""Current game state:
- Round: {visible_state['round_number']}
- Your dice: {self.player.dice}
- Current bid: {current_bid_str}
- Active players: {len([p for p in visible_state['players'] if p['is_alive']])}
- Roulette shots fired: {visible_state['roulette_shots_fired']}

Players:
{json.dumps(visible_state['players'], indent=2)}

Recent bids:
{json.dumps(visible_state['action_history'][-5:], indent=2)}

{memories}

Make your bid. It must be higher than the current bid.
Respond with JSON: {{"action": "bid", "count": 3, "face": 5}}"""

        response = await self._query_llm(system_prompt, user_prompt)
        parsed = self._parse_json_from_response(response)

        return self._create_dice_action(parsed, state)

    def _create_dice_action(self, parsed: dict, state: GameState) -> DiceAction:
        """Create a DiceAction from parsed response or generate random"""
        current_bid = state.current_bid

        # Try to use parsed response
        if parsed.get("action") == "bid" and "count" in parsed and "face" in parsed:
            try:
                count = int(parsed["count"])
                face = int(parsed["face"])

                # Validate
                if 1 <= face <= 6 and count >= 1:
                    action = DiceAction(
                        player_id=self.player_id,
                        bid_count=count,
                        bid_face=face
                    )
                    if action.is_higher_than(current_bid):
                        return action

            except (ValueError, TypeError):
                pass

        # Fallback: random valid bid
        return self._random_dice_action(state)

    def _random_dice_action(self, state: GameState) -> DiceAction:
        """Generate a random dice bid"""
        current = state.current_bid

        if current is None:
            # First bid: start conservatively
            my_dice = self.player.dice
            most_common = max(set(my_dice), key=my_dice.count) if my_dice else 3
            count = my_dice.count(most_common) if my_dice else 1
            return DiceAction(
                player_id=self.player_id,
                bid_count=max(1, count),
                bid_face=most_common
            )

        # Raise the bid
        bluff_tendency = self.config.get("bluff_tendency", 0.5)

        if random.random() < bluff_tendency:
            # Aggressive raise
            count = current.bid_count + random.randint(1, 2)
            face = random.randint(current.bid_face, 6)
        else:
            # Conservative raise
            if current.bid_face < 6:
                count = current.bid_count
                face = current.bid_face + 1
            else:
                count = current.bid_count + 1
                face = random.randint(1, 6)

        return DiceAction(
            player_id=self.player_id,
            bid_count=count,
            bid_face=face
        )

    async def decide_challenge(
        self,
        state: GameState,
        last_action: Union[DeckAction, DiceAction]
    ) -> bool:
        """Decide whether to challenge the previous player"""
        visible_state = self.get_visible_state(state)
        memories = await self._get_memories(
            f"challenge bluff detection {last_action.player_id}"
        )

        system_prompt = get_system_prompt(self.agent_key)

        if state.mode == GameMode.LIARS_DECK:
            action_desc = f"played {last_action.cards_count} card(s) claiming {last_action.claimed_type.value}"
        else:
            action_desc = f"bid {last_action.bid_count}x {last_action.bid_face}'s"

        user_prompt = f"""Previous player {last_action.player_id} {action_desc}.

Your situation:
- Your hand/dice: {self.player.hand if state.mode == GameMode.LIARS_DECK else self.player.dice}
- Roulette shots fired: {visible_state['roulette_shots_fired']} (higher = more dangerous)
- Death probability if you lose: {(visible_state['roulette_shots_fired'] + 1) / 6 * 100:.0f}%

{memories}

Should you challenge and call "LIAR!"?
- If correct: they play roulette
- If wrong: YOU play roulette

Respond with JSON: {{"challenge": true}} or {{"challenge": false}}"""

        response = await self._query_llm(system_prompt, user_prompt, temperature=0.5)
        parsed = self._parse_json_from_response(response)

        # Parse or use personality-based decision
        if "challenge" in parsed:
            return bool(parsed["challenge"])

        # Fallback based on personality
        challenge_tendency = self.config.get("challenge_tendency", 0.5)

        # Adjust based on roulette danger
        shots_fired = state.roulette.shots_fired if state.roulette else 0
        danger_modifier = shots_fired * 0.1  # More cautious as danger increases

        return random.random() < (challenge_tendency - danger_modifier)

    async def on_challenge(
        self,
        challenger_id: str,
        challenged_id: str,
        was_bluff: bool,
        loser_id: str,
        survived: bool,
        state: GameState
    ) -> None:
        """Track challenge events for memory"""
        event = create_challenge_event(
            challenger_id=challenger_id,
            challenged_id=challenged_id,
            was_correct=was_bluff,
            loser_id=loser_id,
            survived_roulette=survived,
            round_number=state.round_number
        )
        self.game_events.append(event)

    async def on_game_over(self, winner_id: str, state: GameState) -> None:
        """Memorize game events at end of game"""
        from memory.memorize import memorize_game_events

        if self.game_events:
            await memorize_game_events(self.game_events, self.player_id)
            self.game_events = []
