"""
Human Player Implementation

Terminal-based human player with input prompts.
"""

import asyncio
from typing import Union

from game.constants import GameMode, CardType, DECK_CLAIMABLE_TYPES
from game.models import (
    Player,
    GameState,
    DeckAction,
    DiceAction,
)
from .base_agent import BaseAgent


class HumanPlayer(BaseAgent):
    """
    Human player that takes input from the terminal.
    """

    def __init__(self, player: Player):
        """
        Initialize the human player.

        Args:
            player: Player model
        """
        super().__init__(player)

    async def _get_input(self, prompt: str) -> str:
        """Get input from user asynchronously"""
        # Run input in thread pool to not block
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: input(prompt).strip())

    async def decide_action(self, state: GameState) -> Union[DeckAction, DiceAction]:
        """Get action from human via terminal"""
        if state.mode == GameMode.LIARS_DECK:
            return await self._decide_deck_action(state)
        else:
            return await self._decide_dice_action(state)

    async def _decide_deck_action(self, state: GameState) -> DeckAction:
        """Get deck action from human"""
        print("\n" + "=" * 40)
        print(f"YOUR TURN - {self.name}")
        print("=" * 40)

        # Show hand
        hand_str = " ".join(f"[{i+1}:{c.value}]" for i, c in enumerate(self.player.hand))
        print(f"\nYour hand: {hand_str}")
        print(f"Target card this round: {state.current_round_claim.value if state.current_round_claim else 'Any'}")
        print(f"Cards on table: {state.cards_on_table}")

        while True:
            try:
                # Get cards to play
                cards_input = await self._get_input(
                    "\nEnter card numbers to play (1-3 cards, e.g., '1 2' or '3'): "
                )

                if not cards_input:
                    print("You must play at least 1 card.")
                    continue

                # Parse card indices
                indices = [int(x) - 1 for x in cards_input.split()]

                if not indices:
                    print("You must play at least 1 card.")
                    continue

                if len(indices) > 3:
                    print("You can only play up to 3 cards.")
                    continue

                # Validate indices
                cards = []
                valid = True
                for idx in indices:
                    if idx < 0 or idx >= len(self.player.hand):
                        print(f"Invalid card number: {idx + 1}")
                        valid = False
                        break
                    cards.append(self.player.hand[idx])

                if not valid:
                    continue

                # Get claim
                claim_input = await self._get_input(
                    f"What do you claim these cards are? (Q/K/A) [default: {state.current_round_claim.value if state.current_round_claim else 'K'}]: "
                )

                if not claim_input:
                    claim = state.current_round_claim or CardType.KING
                else:
                    claim_upper = claim_input.upper()
                    if claim_upper in ["Q", "QUEEN"]:
                        claim = CardType.QUEEN
                    elif claim_upper in ["K", "KING"]:
                        claim = CardType.KING
                    elif claim_upper in ["A", "ACE"]:
                        claim = CardType.ACE
                    else:
                        print("Invalid claim. Use Q, K, or A.")
                        continue

                # Show what they're doing
                cards_str = ", ".join(c.value for c in cards)
                is_truth = all(c == claim or c == CardType.JOKER for c in cards)
                truth_str = "(TRUTH)" if is_truth else "(BLUFF!)"

                print(f"\nYou play {len(cards)} card(s): {cards_str}")
                print(f"You claim they are all: {claim.value} {truth_str}")

                confirm = await self._get_input("Confirm? (y/n) [y]: ")
                if confirm.lower() not in ["", "y", "yes"]:
                    continue

                return DeckAction.create(self.player_id, cards, claim)

            except ValueError:
                print("Invalid input. Please enter card numbers separated by spaces.")
            except Exception as e:
                print(f"Error: {e}. Please try again.")

    async def _decide_dice_action(self, state: GameState) -> DiceAction:
        """Get dice action from human"""
        print("\n" + "=" * 40)
        print(f"YOUR TURN - {self.name}")
        print("=" * 40)

        # Show dice
        from game.dice_mode import LiarsDice
        dice_str = LiarsDice.format_dice(self.player.dice)
        print(f"\nYour dice: {dice_str}")
        print(f"Your dice values: {self.player.dice}")

        if state.current_bid:
            print(f"Current bid: {state.current_bid.bid_count}x {state.current_bid.bid_face}'s")
            print("(Your bid must be higher)")
        else:
            print("No current bid - you start!")

        while True:
            try:
                # Get bid
                count_input = await self._get_input("\nHow many dice? (count): ")
                count = int(count_input)

                if count < 1:
                    print("Count must be at least 1.")
                    continue

                face_input = await self._get_input("What face value? (1-6): ")
                face = int(face_input)

                if face < 1 or face > 6:
                    print("Face must be between 1 and 6.")
                    continue

                # Create action and validate
                action = DiceAction(
                    player_id=self.player_id,
                    bid_count=count,
                    bid_face=face
                )

                if not action.is_higher_than(state.current_bid):
                    print("Your bid must be higher than the current bid!")
                    print("Either increase the count or keep count and increase face.")
                    continue

                print(f"\nYou bid: {count}x {face}'s")
                confirm = await self._get_input("Confirm? (y/n) [y]: ")
                if confirm.lower() not in ["", "y", "yes"]:
                    continue

                return action

            except ValueError:
                print("Invalid input. Please enter numbers.")
            except Exception as e:
                print(f"Error: {e}. Please try again.")

    async def decide_challenge(
        self,
        state: GameState,
        last_action: Union[DeckAction, DiceAction]
    ) -> bool:
        """Ask human if they want to challenge"""
        print("\n" + "-" * 40)

        if state.mode == GameMode.LIARS_DECK:
            print(f"Previous player played {last_action.cards_count} card(s)")
            print(f"They claim: {last_action.claimed_type.value}")
        else:
            print(f"Previous player bid: {last_action.bid_count}x {last_action.bid_face}'s")

        # Show roulette danger
        shots = state.roulette.shots_fired if state.roulette else 0
        death_prob = (shots + 1) / 6 * 100
        print(f"\nRoulette danger: {shots}/6 chambers fired")
        print(f"If you lose, death probability: {death_prob:.0f}%")

        while True:
            response = await self._get_input("\nChallenge? Call LIAR! (y/n): ")
            response = response.lower()

            if response in ["y", "yes", "liar", "liar!"]:
                print("\nYou call: LIAR!")
                return True
            elif response in ["n", "no", ""]:
                print("\nYou accept the play.")
                return False
            else:
                print("Please enter 'y' to challenge or 'n' to accept.")

    async def on_game_start(self, state: GameState) -> None:
        """Show game start message"""
        print("\n" + "=" * 50)
        print("   WELCOME TO LIAR'S BAR!")
        print("=" * 50)
        mode = "LIAR'S DECK" if state.mode == GameMode.LIARS_DECK else "LIAR'S DICE"
        print(f"\nGame mode: {mode}")
        print(f"You are playing as: {self.name}")
        print("\nOther players:")
        for p in state.players:
            if p.id != self.player_id:
                model = f" ({p.model_id})" if p.model_id else ""
                print(f"  - {p.name}{model}")
        print()

    async def on_round_start(self, state: GameState) -> None:
        """Show round start message"""
        print("\n" + "=" * 50)
        print(f"   ROUND {state.round_number}")
        print("=" * 50)

        if state.mode == GameMode.LIARS_DECK:
            print(f"Target card: {state.current_round_claim.value if state.current_round_claim else 'TBD'}")
        print()

    async def on_challenge(
        self,
        challenger_id: str,
        challenged_id: str,
        was_bluff: bool,
        loser_id: str,
        survived: bool,
        state: GameState
    ) -> None:
        """Show challenge result"""
        challenger = state.get_player_by_id(challenger_id)
        challenged = state.get_player_by_id(challenged_id)
        loser = state.get_player_by_id(loser_id)

        print("\n" + "!" * 50)
        print("   CHALLENGE!")
        print("!" * 50)
        print(f"\n{challenger.name if challenger else challenger_id} challenges {challenged.name if challenged else challenged_id}!")

        if was_bluff:
            print("REVEAL: It WAS a bluff!")
        else:
            print("REVEAL: It was TRUTH!")

        print(f"\n{loser.name if loser else loser_id} must play Russian Roulette...")

        if survived:
            print("*CLICK* ... Empty chamber! SURVIVED!")
        else:
            print("*BANG* ... ELIMINATED!")

        print("!" * 50)

    async def on_elimination(
        self,
        eliminated_id: str,
        eliminated_by: str,
        state: GameState
    ) -> None:
        """Show elimination message"""
        eliminated = state.get_player_by_id(eliminated_id)
        if eliminated_id == self.player_id:
            print("\n" + "X" * 50)
            print("   YOU HAVE BEEN ELIMINATED!")
            print("X" * 50)
        else:
            print(f"\n{eliminated.name if eliminated else eliminated_id} has been eliminated!")

    async def on_game_over(self, winner_id: str, state: GameState) -> None:
        """Show game over message"""
        winner = state.get_player_by_id(winner_id)

        print("\n" + "=" * 50)
        print("   GAME OVER!")
        print("=" * 50)

        if winner_id == self.player_id:
            print("\n   CONGRATULATIONS! YOU WIN!")
        else:
            print(f"\n   Winner: {winner.name if winner else winner_id}")

        print("\nFinal standings:")
        for i, p in enumerate(state.players):
            status = "WINNER" if p.id == winner_id else "Eliminated"
            print(f"  {i+1}. {p.name} - {status}")

        print("=" * 50)
