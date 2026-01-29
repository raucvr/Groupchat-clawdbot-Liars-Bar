"""
Liar's Deck Mode

Poker bluffing game with Q, K, A, and Joker cards.
Players must claim their cards match the round's target type.
"""

import random
from typing import TYPE_CHECKING

from .constants import (
    CardType,
    DECK_CARDS_PER_PLAYER,
    DECK_CARD_DISTRIBUTION,
    DECK_MIN_CARDS_PER_PLAY,
    DECK_MAX_CARDS_PER_PLAY,
    DECK_CLAIMABLE_TYPES,
)
from .models import Player, DeckAction

if TYPE_CHECKING:
    from .models import GameState


class LiarsDeck:
    """
    Liar's Deck game mode implementation.

    Rules:
    - Each player gets 5 cards from a deck of Q, K, A, and Joker
    - Each round, a target card type (Q/K/A) is randomly selected
    - Players must play 1-3 cards and claim they match the target
    - Joker cards always count as matching (cannot be caught lying)
    - Next player can challenge or continue playing
    - If challenged: reveal cards, loser plays roulette
    """

    def __init__(self):
        self.deck: list[CardType] = []
        self.round_target: CardType | None = None
        self.cards_on_table: list[list[CardType]] = []  # All cards played this round

    def create_deck(self) -> list[CardType]:
        """Create and shuffle a new deck"""
        deck = []
        for card_type, count in DECK_CARD_DISTRIBUTION.items():
            deck.extend([card_type] * count)
        random.shuffle(deck)
        self.deck = deck
        return deck

    def deal_cards(self, players: list[Player]) -> None:
        """Deal cards to all players"""
        if not self.deck:
            self.create_deck()

        for player in players:
            if player.is_alive():
                player.hand = []
                for _ in range(DECK_CARDS_PER_PLAYER):
                    if self.deck:
                        player.hand.append(self.deck.pop())

    def start_round(self) -> CardType:
        """Start a new round - randomly select target card type"""
        self.round_target = random.choice(DECK_CLAIMABLE_TYPES)
        self.cards_on_table = []
        return self.round_target

    def validate_play(self, player: Player, cards: list[CardType]) -> tuple[bool, str]:
        """
        Validate if a play is legal.

        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        # Check card count
        if len(cards) < DECK_MIN_CARDS_PER_PLAY:
            return False, f"Must play at least {DECK_MIN_CARDS_PER_PLAY} card(s)"

        if len(cards) > DECK_MAX_CARDS_PER_PLAY:
            return False, f"Cannot play more than {DECK_MAX_CARDS_PER_PLAY} cards"

        # Check if player has these cards
        hand_copy = player.hand.copy()
        for card in cards:
            if card not in hand_copy:
                return False, f"You don't have {card.value} in your hand"
            hand_copy.remove(card)

        return True, ""

    def play_cards(self, player: Player, action: DeckAction) -> None:
        """Execute a card play action"""
        # Remove cards from player's hand
        for card in action.cards_played:
            if card in player.hand:
                player.hand.remove(card)

        # Add to table
        self.cards_on_table.append(action.cards_played)

    def reveal_last_play(self, action: DeckAction) -> tuple[bool, list[CardType]]:
        """
        Reveal the last play to check if it was a bluff.

        Returns:
            tuple[bool, list[CardType]]: (was_truthful, actual_cards)
        """
        return action.is_truth, action.cards_played

    def check_round_end(self, players: list[Player]) -> bool:
        """Check if the round should end (all cards played or only one player left)"""
        active_players = [p for p in players if p.is_alive()]

        # Check if any active player still has cards
        for player in active_players:
            if player.hand:
                return False

        return True

    def get_round_target(self) -> CardType | None:
        """Get the current round's target card type"""
        return self.round_target

    def reset_round(self) -> None:
        """Reset for a new round"""
        self.cards_on_table = []
        self.round_target = None

    def get_table_card_count(self) -> int:
        """Get total number of cards on the table"""
        return sum(len(cards) for cards in self.cards_on_table)

    @staticmethod
    def format_hand(hand: list[CardType]) -> str:
        """Format a hand for display"""
        if not hand:
            return "[Empty]"
        return " ".join(f"[{card.value}]" for card in hand)

    @staticmethod
    def is_valid_claim(cards: list[CardType], claim: CardType) -> bool:
        """Check if a claim is actually truthful"""
        return all(card == claim or card == CardType.JOKER for card in cards)
