"""
Russian Roulette Mechanic

Implements the death mechanic for Liar's Bar.
6-chamber revolver with 1 bullet.
"""

import random
from .constants import ROULETTE_CHAMBERS, ROULETTE_BULLETS
from .models import RouletteState


class RussianRoulette:
    """
    Russian Roulette implementation.

    - 6 chambers, 1 bullet
    - Each pull advances the chamber
    - Probability increases as empty chambers are used
    - Resets after someone is eliminated
    """

    def __init__(self):
        self.state = self._create_fresh_state()

    def _create_fresh_state(self) -> RouletteState:
        """Create a new roulette state with random bullet position"""
        return RouletteState(
            chambers=ROULETTE_CHAMBERS,
            bullet_position=random.randint(0, ROULETTE_CHAMBERS - 1),
            current_chamber=0,
            shots_fired=0
        )

    def reset(self):
        """Reset the revolver (after someone is eliminated)"""
        self.state = self._create_fresh_state()

    def pull_trigger(self) -> tuple[bool, int]:
        """
        Pull the trigger.

        Returns:
            tuple[bool, int]: (survived, chamber_number)
                - survived: True if empty chamber, False if bullet
                - chamber_number: Which chamber was fired (1-6 for display)
        """
        chamber = self.state.current_chamber
        survived = chamber != self.state.bullet_position

        # Advance to next chamber
        self.state.current_chamber = (self.state.current_chamber + 1) % self.state.chambers
        self.state.shots_fired += 1

        # Return 1-indexed chamber number for display
        return survived, chamber + 1

    def get_survival_probability(self) -> float:
        """
        Get the probability of surviving the next shot.

        As chambers are used without hitting the bullet,
        the probability of hitting decreases (remaining chambers).
        """
        # How many chambers have we gone through?
        chambers_checked = self.state.shots_fired

        # If we've checked chambers without finding the bullet,
        # the probability changes based on remaining chambers
        remaining_chambers = self.state.chambers - chambers_checked

        if remaining_chambers <= 0:
            # This shouldn't happen in normal play
            return 0.0

        # Probability of survival = (remaining - 1) / remaining
        # Because 1 of the remaining chambers has the bullet
        return (remaining_chambers - 1) / remaining_chambers

    def get_death_probability(self) -> float:
        """Get the probability of being eliminated on the next shot"""
        return 1.0 - self.get_survival_probability()

    def get_shots_fired(self) -> int:
        """Get number of shots fired since last reset"""
        return self.state.shots_fired

    def get_state(self) -> RouletteState:
        """Get current roulette state"""
        return self.state.model_copy()
