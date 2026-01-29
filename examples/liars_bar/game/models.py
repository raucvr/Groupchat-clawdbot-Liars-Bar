"""
Liar's Bar Game Models

Pydantic models for game state, players, and actions.
"""

from datetime import datetime
from typing import Literal, Union
from pydantic import BaseModel, Field

from .constants import GameMode, CardType, PlayerStatus


class Player(BaseModel):
    """Represents a player in the game"""
    id: str
    name: str
    is_human: bool = False
    model_id: str | None = None  # OpenRouter model ID for AI players
    status: PlayerStatus = PlayerStatus.ALIVE
    bullets_survived: int = 0  # Number of empty chambers survived
    hand: list[CardType] = Field(default_factory=list)  # Cards in hand (Deck mode)
    dice: list[int] = Field(default_factory=list)  # Dice values (Dice mode)

    def is_alive(self) -> bool:
        return self.status == PlayerStatus.ALIVE


class DeckAction(BaseModel):
    """Action in Liar's Deck mode - playing cards"""
    player_id: str
    cards_played: list[CardType]  # Actual cards played (hidden from others)
    cards_count: int  # Number of cards played (visible)
    claimed_type: CardType  # What the player claims the cards are
    is_truth: bool  # Whether the claim is actually true
    timestamp: datetime = Field(default_factory=datetime.now)

    @classmethod
    def create(cls, player_id: str, cards: list[CardType], claim: CardType) -> "DeckAction":
        """Create a deck action and automatically determine if it's truth"""
        is_truth = all(
            card == claim or card == CardType.JOKER
            for card in cards
        )
        return cls(
            player_id=player_id,
            cards_played=cards,
            cards_count=len(cards),
            claimed_type=claim,
            is_truth=is_truth
        )


class DiceAction(BaseModel):
    """Action in Liar's Dice mode - making a bid"""
    player_id: str
    bid_count: int  # Number of dice claimed (e.g., "3 fives")
    bid_face: int  # Die face value (1-6)
    timestamp: datetime = Field(default_factory=datetime.now)

    def is_higher_than(self, other: "DiceAction | None") -> bool:
        """Check if this bid is higher than another bid"""
        if other is None:
            return True
        # Higher count wins, or same count with higher face
        if self.bid_count > other.bid_count:
            return True
        if self.bid_count == other.bid_count and self.bid_face > other.bid_face:
            return True
        return False


class ChallengeResult(BaseModel):
    """Result of a challenge"""
    challenger_id: str
    challenged_id: str
    was_bluff: bool  # True if the challenged player was bluffing
    loser_id: str  # The player who lost the challenge
    roulette_result: Literal["survived", "eliminated"]
    chamber_number: int  # Which chamber was fired (1-6)


class RouletteState(BaseModel):
    """State of the Russian roulette revolver"""
    chambers: int = 6
    bullet_position: int  # 0-5, which chamber has the bullet
    current_chamber: int = 0  # Current chamber position
    shots_fired: int = 0  # Total shots fired since last reset


class GameState(BaseModel):
    """Complete game state"""
    mode: GameMode
    round_number: int = 1
    turn_number: int = 0  # Turn within current round
    current_player_idx: int = 0
    players: list[Player] = Field(default_factory=list)

    # Deck mode specific
    current_round_claim: CardType | None = None  # Target card type for this round
    cards_on_table: int = 0  # Number of cards played this round

    # Dice mode specific
    current_bid: DiceAction | None = None

    # Action history
    deck_actions: list[DeckAction] = Field(default_factory=list)
    dice_actions: list[DiceAction] = Field(default_factory=list)
    challenge_history: list[ChallengeResult] = Field(default_factory=list)

    # Roulette state
    roulette: RouletteState | None = None

    # Game status
    game_over: bool = False
    winner_id: str | None = None

    def get_active_players(self) -> list[Player]:
        """Return list of players still in the game"""
        return [p for p in self.players if p.is_alive()]

    def get_current_player(self) -> Player:
        """Get the current player"""
        return self.players[self.current_player_idx]

    def get_player_by_id(self, player_id: str) -> Player | None:
        """Find a player by ID"""
        for player in self.players:
            if player.id == player_id:
                return player
        return None

    def get_last_action(self) -> Union[DeckAction, DiceAction, None]:
        """Get the last action taken"""
        if self.mode == GameMode.LIARS_DECK:
            return self.deck_actions[-1] if self.deck_actions else None
        else:
            return self.dice_actions[-1] if self.dice_actions else None


class GameEvent(BaseModel):
    """Generic game event for logging and memory"""
    event_type: str
    player_id: str | None = None
    details: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
