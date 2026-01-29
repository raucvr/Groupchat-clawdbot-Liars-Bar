"""
Liar's Bar Game Constants

Card types, rules, and game configuration constants.
"""

from enum import Enum


class GameMode(str, Enum):
    """Available game modes"""
    LIARS_DECK = "liars_deck"  # Poker bluffing with Q/K/A/Joker
    LIARS_DICE = "liars_dice"  # Dice bluffing


class CardType(str, Enum):
    """Card types in Liar's Deck mode"""
    QUEEN = "Q"
    KING = "K"
    ACE = "A"
    JOKER = "JOKER"  # Always counts as truth - cannot be successfully challenged


class PlayerStatus(str, Enum):
    """Player status in the game"""
    ALIVE = "alive"
    ELIMINATED = "eliminated"


# Liar's Deck configuration
DECK_CARDS_PER_PLAYER = 5
DECK_CARD_DISTRIBUTION = {
    CardType.QUEEN: 6,
    CardType.KING: 6,
    CardType.ACE: 6,
    CardType.JOKER: 2,
}
DECK_MIN_CARDS_PER_PLAY = 1
DECK_MAX_CARDS_PER_PLAY = 3
DECK_CLAIMABLE_TYPES = [CardType.QUEEN, CardType.KING, CardType.ACE]

# Liar's Dice configuration
DICE_PER_PLAYER = 5
DICE_FACES = 6  # Standard dice: 1-6
DICE_MIN_FACE = 1
DICE_MAX_FACE = 6

# Russian Roulette configuration
ROULETTE_CHAMBERS = 6
ROULETTE_BULLETS = 1

# Game configuration
MIN_PLAYERS = 2
MAX_PLAYERS = 4
DEFAULT_PLAYERS = 4

# Character names for AI agents (matching the original game)
CHARACTER_NAMES = {
    "scub": "Scub",      # Bulldog
    "foxy": "Foxy",      # Fox
    "bristle": "Bristle", # Pig
    "toar": "Toar",      # Bull
}
