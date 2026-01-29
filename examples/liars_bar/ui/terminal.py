"""
Terminal UI for Liar's Bar

Handles all terminal display and formatting.
"""

import os
import sys
from typing import TYPE_CHECKING

from game.constants import GameMode, PlayerStatus
from game.models import GameState, Player, ChallengeResult
from .ascii_art import (
    TITLE_SIMPLE,
    PLAYER_ALIVE,
    PLAYER_DEAD,
    PLAYER_CURRENT,
    get_cards_inline,
    get_character_icon,
    format_dice_row,
    print_horizontal_cards,
    print_horizontal_dice,
    REVOLVER_FIRE,
    REVOLVER_CLICK,
)

if TYPE_CHECKING:
    from game.models import DeckAction, DiceAction


class TerminalUI:
    """
    Terminal-based UI for Liar's Bar.

    Handles:
    - Screen clearing and rendering
    - Game state display
    - Player information
    - Action history
    - Challenge results
    """

    def __init__(self):
        self.width = 60  # Default terminal width

    def clear_screen(self) -> None:
        """Clear the terminal screen"""
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix/Linux/Mac
            os.system('clear')

    def print_line(self, char: str = "─", width: int | None = None) -> None:
        """Print a horizontal line"""
        w = width or self.width
        print(char * w)

    def print_centered(self, text: str, width: int | None = None) -> None:
        """Print centered text"""
        w = width or self.width
        print(text.center(w))

    def print_title(self) -> None:
        """Print the game title"""
        print(TITLE_SIMPLE)

    def render_game_header(self, state: GameState) -> None:
        """Render the game header with mode and round info"""
        mode_name = "LIAR'S DECK" if state.mode == GameMode.LIARS_DECK else "LIAR'S DICE"

        print("╔" + "═" * (self.width - 2) + "╗")
        self.print_centered(f"║  🎭 LIAR'S BAR - {mode_name} 🎭  ║")
        self.print_centered(f"║  Round: {state.round_number}  ║")
        print("╚" + "═" * (self.width - 2) + "╝")

    def render_players(self, state: GameState, current_player_id: str | None = None) -> None:
        """Render player list with status"""
        print("\n👥 PLAYERS:")
        print(self.line("─", 40))

        for player in state.players:
            # Status icon
            if player.status == PlayerStatus.ELIMINATED:
                status = PLAYER_DEAD
            else:
                status = PLAYER_ALIVE

            # Current player indicator
            is_current = player.id == state.get_current_player().id
            current = PLAYER_CURRENT if is_current else "  "

            # Character icon
            icon = get_character_icon(player.id)

            # Model info for AI
            model = ""
            if player.model_id:
                model = f" [{player.model_id.split('/')[-1]}]"
            elif player.is_human:
                model = " [Human]"

            # Bullets survived
            bullets = f" (survived: {player.bullets_survived})" if player.bullets_survived > 0 else ""

            print(f"  {current} {status} {icon} {player.name}{model}{bullets}")

        print()

    def render_deck_state(self, state: GameState, player: Player | None = None) -> None:
        """Render Liar's Deck mode state"""
        print("\n🃏 DECK MODE:")
        print(self.line("─", 40))

        # Current round target
        if state.current_round_claim:
            print(f"  Target card: [{state.current_round_claim.value}]")

        # Cards on table
        print(f"  Cards on table: {state.cards_on_table}")

        # Show player's hand if provided
        if player and player.hand:
            print(f"\n  Your hand: {get_cards_inline(player.hand)}")
            print(f"  ({len(player.hand)} cards)")

        # Recent actions
        if state.deck_actions:
            print("\n  Recent plays:")
            for action in state.deck_actions[-5:]:
                actor = state.get_player_by_id(action.player_id)
                name = actor.name if actor else action.player_id
                print(f"    • {name}: {action.cards_count} card(s) → [{action.claimed_type.value}]")

        print()

    def render_dice_state(self, state: GameState, player: Player | None = None) -> None:
        """Render Liar's Dice mode state"""
        print("\n🎲 DICE MODE:")
        print(self.line("─", 40))

        # Current bid
        if state.current_bid:
            bidder = state.get_player_by_id(state.current_bid.player_id)
            name = bidder.name if bidder else state.current_bid.player_id
            print(f"  Current bid: {state.current_bid.bid_count}x {state.current_bid.bid_face}'s by {name}")
        else:
            print("  No bid yet - first player starts")

        # Show player's dice if provided
        if player and player.dice:
            print(f"\n  Your dice: {format_dice_row(player.dice)}")
            print(f"  Values: {player.dice}")

        # Recent bids
        if state.dice_actions:
            print("\n  Recent bids:")
            for action in state.dice_actions[-5:]:
                bidder = state.get_player_by_id(action.player_id)
                name = bidder.name if bidder else action.player_id
                print(f"    • {name}: {action.bid_count}x {action.bid_face}'s")

        print()

    def render_roulette_state(self, state: GameState) -> None:
        """Render Russian roulette state"""
        if state.roulette:
            shots = state.roulette.shots_fired
            chambers = state.roulette.chambers
            death_prob = (shots + 1) / chambers * 100 if shots < chambers else 100

            print("\n🔫 RUSSIAN ROULETTE:")
            print(self.line("─", 40))

            # Visual representation
            chamber_display = ""
            for i in range(chambers):
                if i < shots:
                    chamber_display += "○ "  # Empty chamber (fired)
                else:
                    chamber_display += "● "  # Unfired chamber

            print(f"  Chambers: {chamber_display}")
            print(f"  Shots fired: {shots}/{chambers}")
            print(f"  Next shot death probability: {death_prob:.0f}%")
            print()

    def render_challenge_result(self, result: ChallengeResult, state: GameState) -> None:
        """Render challenge result dramatically"""
        challenger = state.get_player_by_id(result.challenger_id)
        challenged = state.get_player_by_id(result.challenged_id)
        loser = state.get_player_by_id(result.loser_id)

        print("\n" + "!" * self.width)
        self.print_centered("🔫 CHALLENGE! 🔫")
        print("!" * self.width)

        c1_name = challenger.name if challenger else result.challenger_id
        c2_name = challenged.name if challenged else result.challenged_id
        loser_name = loser.name if loser else result.loser_id

        print(f"\n  {c1_name} challenges {c2_name}!")
        print()

        if result.was_bluff:
            print("  📢 REVEAL: It WAS a BLUFF!")
            print(f"  {c2_name} was lying!")
        else:
            print("  📢 REVEAL: It was TRUTH!")
            print(f"  {c1_name} was wrong to challenge!")

        print(f"\n  {loser_name} must face the revolver...")
        print(f"  Chamber #{result.chamber_number}")

        if result.roulette_result == "survived":
            print(REVOLVER_CLICK)
            print("  *CLICK* ... Empty chamber!")
            print(f"  {loser_name} SURVIVES!")
        else:
            print(REVOLVER_FIRE)
            print(f"  {loser_name} is ELIMINATED!")

        print("\n" + "!" * self.width)

    def render_action(self, action: "DeckAction | DiceAction", state: GameState) -> None:
        """Render an action that was just taken"""
        from game.models import DeckAction, DiceAction

        actor = state.get_player_by_id(action.player_id)
        name = actor.name if actor else action.player_id

        print("\n" + "-" * 40)

        if isinstance(action, DeckAction):
            print(f"  {name} plays {action.cards_count} card(s)")
            print(f"  Claims: [{action.claimed_type.value}]")
        else:
            print(f"  {name} bids:")
            print(f"  {action.bid_count}x {action.bid_face}'s")

        print("-" * 40)

    def render_game_over(self, winner: Player, state: GameState) -> None:
        """Render game over screen"""
        print("\n" + "=" * self.width)
        self.print_centered("🎉 GAME OVER! 🎉")
        print("=" * self.width)

        icon = get_character_icon(winner.id)
        print(f"\n  {icon} WINNER: {winner.name}!")

        print("\n  Final standings:")
        print(self.line("─", 40))

        # Sort by elimination order (winner first)
        sorted_players = sorted(
            state.players,
            key=lambda p: 0 if p.id == winner.id else 1
        )

        for i, p in enumerate(sorted_players, 1):
            icon = get_character_icon(p.id)
            status = "👑 WINNER" if p.id == winner.id else "💀 Eliminated"
            print(f"  {i}. {icon} {p.name} - {status}")

        print("\n" + "=" * self.width)

    def render_full_state(
        self,
        state: GameState,
        current_player: Player | None = None
    ) -> None:
        """Render the complete game state"""
        self.clear_screen()
        self.render_game_header(state)
        self.render_players(state)

        if state.mode == GameMode.LIARS_DECK:
            self.render_deck_state(state, current_player)
        else:
            self.render_dice_state(state, current_player)

        self.render_roulette_state(state)

    def wait_for_enter(self, message: str = "Press Enter to continue...") -> None:
        """Wait for user to press Enter"""
        input(f"\n{message}")

    def line(self, char: str = "─", width: int | None = None) -> str:
        """Return a line string"""
        w = width or self.width
        return char * w

    def show_thinking(self, player_name: str) -> None:
        """Show that an AI is thinking"""
        print(f"\n  🤔 {player_name} is thinking...")

    def show_error(self, message: str) -> None:
        """Show an error message"""
        print(f"\n  ❌ Error: {message}")

    def show_info(self, message: str) -> None:
        """Show an info message"""
        print(f"\n  ℹ️  {message}")
