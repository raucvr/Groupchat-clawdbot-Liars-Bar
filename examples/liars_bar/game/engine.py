"""
Game Engine

Main game orchestrator that coordinates game flow, turns, and state management.
"""

from typing import Union, Callable, Awaitable, TYPE_CHECKING

from .constants import GameMode, PlayerStatus
from .models import (
    Player,
    GameState,
    DeckAction,
    DiceAction,
    ChallengeResult,
    RouletteState,
    GameEvent,
)
from .roulette import RussianRoulette
from .deck_mode import LiarsDeck
from .dice_mode import LiarsDice

if TYPE_CHECKING:
    pass

# Type alias for action callback
ActionCallback = Callable[[Player, GameState], Awaitable[Union[DeckAction, DiceAction, str]]]
ChallengeCallback = Callable[[Player, GameState, Union[DeckAction, DiceAction]], Awaitable[bool]]
EventCallback = Callable[[GameEvent], Awaitable[None]]


class GameEngine:
    """
    Main game engine that orchestrates the Liar's Bar game.

    Handles:
    - Game initialization and setup
    - Turn management
    - Challenge resolution
    - Russian roulette execution
    - Win condition checking
    """

    def __init__(self, mode: GameMode, players: list[Player]):
        self.state = GameState(mode=mode, players=players)
        self.roulette = RussianRoulette()
        self.state.roulette = self.roulette.get_state()

        # Mode-specific handlers
        self.deck_game: LiarsDeck | None = None
        self.dice_game: LiarsDice | None = None

        if mode == GameMode.LIARS_DECK:
            self.deck_game = LiarsDeck()
        else:
            self.dice_game = LiarsDice()

        # Event callbacks
        self._event_callbacks: list[EventCallback] = []

    def register_event_callback(self, callback: EventCallback) -> None:
        """Register a callback for game events"""
        self._event_callbacks.append(callback)

    async def _emit_event(self, event: GameEvent) -> None:
        """Emit a game event to all registered callbacks"""
        for callback in self._event_callbacks:
            await callback(event)

    def setup_round(self) -> None:
        """Set up a new round"""
        if self.state.mode == GameMode.LIARS_DECK:
            self._setup_deck_round()
        else:
            self._setup_dice_round()

        self.state.turn_number = 0

    def _setup_deck_round(self) -> None:
        """Set up a Liar's Deck round"""
        if self.deck_game is None:
            return

        # Create new deck and deal cards
        self.deck_game.create_deck()
        active_players = self.state.get_active_players()
        self.deck_game.deal_cards(active_players)

        # Select round target
        target = self.deck_game.start_round()
        self.state.current_round_claim = target
        self.state.cards_on_table = 0
        self.state.deck_actions = []

    def _setup_dice_round(self) -> None:
        """Set up a Liar's Dice round"""
        if self.dice_game is None:
            return

        # Roll dice for all players
        active_players = self.state.get_active_players()
        self.dice_game.roll_dice(active_players)
        self.dice_game.reset_round()
        self.state.current_bid = None
        self.state.dice_actions = []

    def get_current_player(self) -> Player:
        """Get the current player"""
        return self.state.get_current_player()

    def advance_turn(self) -> Player:
        """Advance to the next active player"""
        active_players = self.state.get_active_players()
        if len(active_players) <= 1:
            return active_players[0] if active_players else self.state.players[0]

        # Find current player in active list
        current = self.get_current_player()
        current_active_idx = next(
            (i for i, p in enumerate(active_players) if p.id == current.id),
            0
        )

        # Move to next active player
        next_active_idx = (current_active_idx + 1) % len(active_players)
        next_player = active_players[next_active_idx]

        # Update state to point to this player in the full list
        self.state.current_player_idx = next(
            i for i, p in enumerate(self.state.players) if p.id == next_player.id
        )

        self.state.turn_number += 1
        return next_player

    def process_deck_action(self, action: DeckAction) -> bool:
        """
        Process a Liar's Deck action.

        Returns True if action was valid and processed.
        """
        if self.deck_game is None:
            return False

        player = self.state.get_player_by_id(action.player_id)
        if player is None:
            return False

        # Validate and execute
        is_valid, error = self.deck_game.validate_play(player, action.cards_played)
        if not is_valid:
            return False

        self.deck_game.play_cards(player, action)
        self.state.deck_actions.append(action)
        self.state.cards_on_table += action.cards_count

        return True

    def process_dice_action(self, action: DiceAction) -> bool:
        """
        Process a Liar's Dice action.

        Returns True if action was valid and processed.
        """
        if self.dice_game is None:
            return False

        # Validate bid
        is_valid, error = self.dice_game.validate_bid(action)
        if not is_valid:
            return False

        self.dice_game.make_bid(action)
        self.state.dice_actions.append(action)
        self.state.current_bid = action

        return True

    async def handle_challenge(
        self,
        challenger: Player,
        challenged: Player
    ) -> ChallengeResult:
        """
        Handle a challenge between two players.

        Returns the result including roulette outcome.
        """
        # Determine if the challenged player was bluffing
        was_bluff = self._check_bluff()

        # Determine loser
        if was_bluff:
            loser = challenged
        else:
            loser = challenger

        # Execute Russian roulette
        survived, chamber = self.roulette.pull_trigger()

        if not survived:
            # Player eliminated
            loser_obj = self.state.get_player_by_id(loser.id)
            if loser_obj:
                loser_obj.status = PlayerStatus.ELIMINATED
            self.roulette.reset()
        else:
            # Player survived
            loser_obj = self.state.get_player_by_id(loser.id)
            if loser_obj:
                loser_obj.bullets_survived += 1

        # Update roulette state
        self.state.roulette = self.roulette.get_state()

        result = ChallengeResult(
            challenger_id=challenger.id,
            challenged_id=challenged.id,
            was_bluff=was_bluff,
            loser_id=loser.id,
            roulette_result="survived" if survived else "eliminated",
            chamber_number=chamber
        )

        self.state.challenge_history.append(result)

        # Emit event
        await self._emit_event(GameEvent(
            event_type="challenge",
            player_id=challenger.id,
            details={
                "challenged": challenged.id,
                "was_bluff": was_bluff,
                "loser": loser.id,
                "survived": survived,
                "chamber": chamber
            }
        ))

        return result

    def _check_bluff(self) -> bool:
        """Check if the last action was a bluff"""
        if self.state.mode == GameMode.LIARS_DECK:
            last_action = self.state.deck_actions[-1] if self.state.deck_actions else None
            if isinstance(last_action, DeckAction):
                return not last_action.is_truth
        else:
            if self.dice_game is None:
                return False
            active_players = self.state.get_active_players()
            was_bluff, _, _ = self.dice_game.resolve_challenge(active_players)
            return was_bluff

        return False

    def check_game_over(self) -> bool:
        """Check if the game is over (only one player remaining)"""
        active_players = self.state.get_active_players()

        if len(active_players) <= 1:
            self.state.game_over = True
            if active_players:
                self.state.winner_id = active_players[0].id
            return True

        return False

    def check_round_over(self) -> bool:
        """Check if the current round is over"""
        if self.state.mode == GameMode.LIARS_DECK:
            if self.deck_game is None:
                return False
            return self.deck_game.check_round_end(self.state.get_active_players())
        else:
            # Dice mode: round ends after challenge
            return False

    def get_last_action(self) -> Union[DeckAction, DiceAction, None]:
        """Get the last action taken"""
        return self.state.get_last_action()

    def get_previous_player(self) -> Player | None:
        """Get the player who made the last action"""
        last_action = self.get_last_action()
        if last_action is None:
            return None
        return self.state.get_player_by_id(last_action.player_id)

    def can_challenge(self) -> bool:
        """Check if the current player can challenge"""
        # Can challenge if there's a previous action
        return self.get_last_action() is not None

    def get_game_state(self) -> GameState:
        """Get a copy of the current game state"""
        return self.state.model_copy(deep=True)

    def get_winner(self) -> Player | None:
        """Get the winner if game is over"""
        if not self.state.game_over or not self.state.winner_id:
            return None
        return self.state.get_player_by_id(self.state.winner_id)

    def get_roulette_probability(self) -> float:
        """Get current probability of death in roulette"""
        return self.roulette.get_death_probability()

    def get_deck_game(self) -> LiarsDeck | None:
        """Get the deck game handler"""
        return self.deck_game

    def get_dice_game(self) -> LiarsDice | None:
        """Get the dice game handler"""
        return self.dice_game
