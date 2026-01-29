"""
Liar's Dice Mode

Classic dice bluffing game.
Players bid on the total count of a face value across all dice.
"""

import random
from typing import TYPE_CHECKING

from .constants import (
    DICE_PER_PLAYER,
    DICE_MIN_FACE,
    DICE_MAX_FACE,
)
from .models import Player, DiceAction

if TYPE_CHECKING:
    from .models import GameState


class LiarsDice:
    """
    Liar's Dice game mode implementation.

    Rules:
    - Each player rolls 5 dice (hidden from others)
    - Players take turns bidding on total count of a face value
    - Bid must be higher than previous (more dice or same count with higher face)
    - Can challenge ("Liar!") instead of raising
    - All dice revealed on challenge
    - If actual count >= bid: challenger loses
    - If actual count < bid: bidder loses
    """

    def __init__(self):
        self.current_bid: DiceAction | None = None

    def roll_dice(self, players: list[Player]) -> None:
        """Roll dice for all active players"""
        for player in players:
            if player.is_alive():
                player.dice = [
                    random.randint(DICE_MIN_FACE, DICE_MAX_FACE)
                    for _ in range(DICE_PER_PLAYER)
                ]

    def validate_bid(self, new_bid: DiceAction) -> tuple[bool, str]:
        """
        Validate if a bid is legal.

        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        # Check face value is valid
        if not (DICE_MIN_FACE <= new_bid.bid_face <= DICE_MAX_FACE):
            return False, f"Face value must be between {DICE_MIN_FACE} and {DICE_MAX_FACE}"

        # Check count is positive
        if new_bid.bid_count < 1:
            return False, "Bid count must be at least 1"

        # Check if bid is higher than current
        if self.current_bid is not None:
            if not new_bid.is_higher_than(self.current_bid):
                return False, (
                    f"Bid must be higher than current "
                    f"({self.current_bid.bid_count}x {self.current_bid.bid_face})"
                )

        return True, ""

    def make_bid(self, action: DiceAction) -> None:
        """Record a new bid"""
        self.current_bid = action

    def count_face(self, players: list[Player], face: int) -> int:
        """Count how many dice show a specific face across all active players"""
        total = 0
        for player in players:
            if player.is_alive():
                total += sum(1 for d in player.dice if d == face)
        return total

    def resolve_challenge(
        self, players: list[Player]
    ) -> tuple[bool, int, int]:
        """
        Resolve a challenge by counting actual dice.

        Returns:
            tuple[bool, int, int]: (bidder_was_bluffing, actual_count, bid_count)
        """
        if self.current_bid is None:
            raise ValueError("No bid to challenge")

        actual_count = self.count_face(players, self.current_bid.bid_face)
        bid_count = self.current_bid.bid_count

        # Bidder was bluffing if actual count is less than claimed
        bidder_bluffed = actual_count < bid_count

        return bidder_bluffed, actual_count, bid_count

    def reset_round(self) -> None:
        """Reset for a new round"""
        self.current_bid = None

    def get_current_bid(self) -> DiceAction | None:
        """Get the current bid"""
        return self.current_bid

    def get_all_dice(self, players: list[Player]) -> dict[str, list[int]]:
        """Get all dice from all active players (for reveal)"""
        return {
            player.id: player.dice.copy()
            for player in players
            if player.is_alive()
        }

    def get_max_possible_count(self, players: list[Player]) -> int:
        """Get maximum possible count of any face (all dice from active players)"""
        return sum(
            DICE_PER_PLAYER
            for player in players
            if player.is_alive()
        )

    @staticmethod
    def format_dice(dice: list[int]) -> str:
        """Format dice for display"""
        dice_faces = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
        return " ".join(dice_faces.get(d, str(d)) for d in dice)

    @staticmethod
    def format_bid(bid: DiceAction | None) -> str:
        """Format a bid for display"""
        if bid is None:
            return "No bid yet"
        return f"{bid.bid_count}x {bid.bid_face}'s"
