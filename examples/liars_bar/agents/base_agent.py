"""
Base Agent Interface

Abstract base class for all players (human and AI).
"""

from abc import ABC, abstractmethod
from typing import Union

from game.constants import GameMode
from game.models import (
    Player,
    GameState,
    DeckAction,
    DiceAction,
)


class BaseAgent(ABC):
    """
    Abstract base class for all players in Liar's Bar.

    Both human players and AI agents inherit from this class.
    """

    def __init__(self, player: Player):
        """
        Initialize the agent.

        Args:
            player: The Player model associated with this agent
        """
        self.player = player

    @property
    def player_id(self) -> str:
        """Get the player's ID"""
        return self.player.id

    @property
    def name(self) -> str:
        """Get the player's name"""
        return self.player.name

    @property
    def is_human(self) -> bool:
        """Check if this is a human player"""
        return self.player.is_human

    def is_alive(self) -> bool:
        """Check if the player is still in the game"""
        return self.player.is_alive()

    @abstractmethod
    async def decide_action(
        self,
        state: GameState
    ) -> Union[DeckAction, DiceAction]:
        """
        Decide what action to take on this turn.

        For Deck mode: Choose cards to play and what to claim
        For Dice mode: Make a bid (count and face)

        Args:
            state: Current game state

        Returns:
            The action to take (DeckAction or DiceAction)
        """
        pass

    @abstractmethod
    async def decide_challenge(
        self,
        state: GameState,
        last_action: Union[DeckAction, DiceAction]
    ) -> bool:
        """
        Decide whether to challenge the previous player's action.

        Args:
            state: Current game state
            last_action: The action made by the previous player

        Returns:
            True to challenge ("Liar!"), False to accept and continue
        """
        pass

    async def on_game_start(self, state: GameState) -> None:
        """
        Called when a new game starts.

        Override to implement initialization logic.

        Args:
            state: Initial game state
        """
        pass

    async def on_round_start(self, state: GameState) -> None:
        """
        Called when a new round starts.

        Override to implement round initialization.

        Args:
            state: Game state at round start
        """
        pass

    async def on_action(
        self,
        player_id: str,
        action: Union[DeckAction, DiceAction],
        state: GameState
    ) -> None:
        """
        Called when any player takes an action.

        Override to track opponent behavior.

        Args:
            player_id: ID of the player who acted
            action: The action taken
            state: Current game state
        """
        pass

    async def on_challenge(
        self,
        challenger_id: str,
        challenged_id: str,
        was_bluff: bool,
        loser_id: str,
        survived: bool,
        state: GameState
    ) -> None:
        """
        Called when a challenge occurs.

        Override to track challenge outcomes.

        Args:
            challenger_id: ID of the challenger
            challenged_id: ID of the challenged player
            was_bluff: Whether the challenged player was bluffing
            loser_id: ID of the player who lost
            survived: Whether the loser survived roulette
            state: Current game state
        """
        pass

    async def on_elimination(
        self,
        eliminated_id: str,
        eliminated_by: str,
        state: GameState
    ) -> None:
        """
        Called when a player is eliminated.

        Override to handle eliminations.

        Args:
            eliminated_id: ID of the eliminated player
            eliminated_by: ID of the player who caused elimination
            state: Current game state
        """
        pass

    async def on_game_over(
        self,
        winner_id: str,
        state: GameState
    ) -> None:
        """
        Called when the game ends.

        Override to handle game completion.

        Args:
            winner_id: ID of the winning player
            state: Final game state
        """
        pass

    def get_visible_state(self, state: GameState) -> dict:
        """
        Get the game state visible to this player.

        Hides other players' cards/dice but shows game history.

        Args:
            state: Full game state

        Returns:
            Dictionary with visible information
        """
        visible = {
            "mode": state.mode.value,
            "round_number": state.round_number,
            "turn_number": state.turn_number,
            "my_hand": self.player.hand if state.mode == GameMode.LIARS_DECK else None,
            "my_dice": self.player.dice if state.mode == GameMode.LIARS_DICE else None,
            "current_round_claim": state.current_round_claim.value if state.current_round_claim else None,
            "current_bid": None,
            "cards_on_table": state.cards_on_table,
            "players": [],
            "action_history": [],
            "challenge_history": [],
            "roulette_shots_fired": state.roulette.shots_fired if state.roulette else 0,
        }

        # Add current bid for dice mode
        if state.current_bid:
            visible["current_bid"] = {
                "player_id": state.current_bid.player_id,
                "count": state.current_bid.bid_count,
                "face": state.current_bid.bid_face
            }

        # Add player info (without hidden cards/dice)
        for p in state.players:
            player_info = {
                "id": p.id,
                "name": p.name,
                "is_alive": p.is_alive(),
                "bullets_survived": p.bullets_survived,
                "cards_in_hand": len(p.hand) if state.mode == GameMode.LIARS_DECK else None,
                "is_current": p.id == state.get_current_player().id,
            }
            visible["players"].append(player_info)

        # Add action history (without revealing actual cards)
        if state.mode == GameMode.LIARS_DECK:
            for action in state.deck_actions:
                visible["action_history"].append({
                    "player_id": action.player_id,
                    "cards_count": action.cards_count,
                    "claimed_type": action.claimed_type.value,
                })
        else:
            for action in state.dice_actions:
                visible["action_history"].append({
                    "player_id": action.player_id,
                    "bid_count": action.bid_count,
                    "bid_face": action.bid_face,
                })

        # Add challenge history
        for challenge in state.challenge_history:
            visible["challenge_history"].append({
                "challenger_id": challenge.challenger_id,
                "challenged_id": challenge.challenged_id,
                "was_bluff": challenge.was_bluff,
                "loser_id": challenge.loser_id,
                "result": challenge.roulette_result,
            })

        return visible
