#!/usr/bin/env python3
"""
Liar's Bar - Main Entry Point

A bluffing game where 1 human plays against 3 AI agents.
Each AI is powered by a different LLM via OpenRouter.

Usage:
    export OPENROUTER_API_KEY=your_api_key
    python main.py
"""

import asyncio
import os
import sys
from typing import Union

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.constants import GameMode
from game.models import Player, GameState, DeckAction, DiceAction
from game.engine import GameEngine
from agents.base_agent import BaseAgent
from agents.human_player import HumanPlayer
from agents.ai_agent import AIAgent
from agents.personalities import AGENT_CONFIGS
from memory.memorize import (
    create_game_over_event,
    memorize_game_events,
)
from ui.terminal import TerminalUI
from ui.ascii_art import TITLE_SIMPLE


async def get_input(prompt: str) -> str:
    """Get user input asynchronously"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: input(prompt).strip())


async def select_game_mode(ui: TerminalUI) -> GameMode:
    """Let user select game mode"""
    ui.clear_screen()
    print(TITLE_SIMPLE)
    print("\n🎮 SELECT GAME MODE:")
    print("-" * 40)
    print("  1. Liar's Deck (Poker Bluffing)")
    print("     - Play cards Q/K/A/Joker")
    print("     - Claim cards match the round target")
    print()
    print("  2. Liar's Dice (Dice Bluffing)")
    print("     - Roll and hide 5 dice")
    print("     - Bid on total count across all players")
    print()

    while True:
        choice = await get_input("Enter choice (1 or 2): ")
        if choice == "1":
            return GameMode.LIARS_DECK
        elif choice == "2":
            return GameMode.LIARS_DICE
        else:
            print("Invalid choice. Please enter 1 or 2.")


async def setup_game(ui: TerminalUI) -> tuple[GameEngine, list[BaseAgent]]:
    """Set up the game with players"""
    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("\n❌ ERROR: OPENROUTER_API_KEY environment variable not set!")
        print("\nPlease set your OpenRouter API key:")
        print("  export OPENROUTER_API_KEY=your_api_key_here")
        print("\nGet your API key at: https://openrouter.ai/keys")
        sys.exit(1)

    # Select game mode
    mode = await select_game_mode(ui)

    # Get human player name
    ui.clear_screen()
    print(TITLE_SIMPLE)
    print("\n👤 PLAYER SETUP:")
    print("-" * 40)

    name = await get_input("Enter your name: ")
    if not name:
        name = "Player"

    print(f"\nWelcome, {name}!")
    print("\nYou will be playing against 3 AI opponents:")

    # Create players
    players: list[Player] = []
    agents: list[BaseAgent] = []

    # Human player
    human_player = Player(
        id="human",
        name=name,
        is_human=True
    )
    players.append(human_player)
    agents.append(HumanPlayer(human_player))

    # AI players
    for agent_key, config in AGENT_CONFIGS.items():
        print(f"  • {config['name']} ({config['character']}) - {config['model_id']}")

        ai_player = Player(
            id=agent_key,
            name=config["name"],
            is_human=False,
            model_id=config["model_id"]
        )
        players.append(ai_player)

        ai_agent = AIAgent(
            player=ai_player,
            api_key=api_key,
            agent_key=agent_key
        )
        agents.append(ai_agent)

    print()
    await get_input("Press Enter to start the game...")

    # Create game engine
    engine = GameEngine(mode=mode, players=players)

    return engine, agents


def get_agent_for_player(agents: list[BaseAgent], player_id: str) -> BaseAgent | None:
    """Find the agent for a given player ID"""
    for agent in agents:
        if agent.player_id == player_id:
            return agent
    return None


async def run_turn(
    engine: GameEngine,
    agents: list[BaseAgent],
    ui: TerminalUI
) -> bool:
    """
    Run a single turn.

    Returns True if the game should continue, False if over.
    """
    state = engine.get_game_state()
    current_player = engine.get_current_player()
    current_agent = get_agent_for_player(agents, current_player.id)

    if not current_agent:
        ui.show_error(f"No agent found for player {current_player.id}")
        return False

    # Render current state
    if current_player.is_human:
        ui.render_full_state(state, current_player)
    else:
        # Brief update for AI turns
        ui.show_thinking(current_player.name)

    # Check if player can and wants to challenge
    last_action = engine.get_last_action()
    previous_player = engine.get_previous_player()

    if last_action and previous_player and previous_player.id != current_player.id:
        # Ask if player wants to challenge
        if current_player.is_human:
            ui.render_action(last_action, state)

        should_challenge = await current_agent.decide_challenge(state, last_action)

        if should_challenge:
            # Handle challenge
            result = await engine.handle_challenge(current_player, previous_player)

            # Show result
            ui.render_challenge_result(result, engine.get_game_state())

            # Notify all agents
            for agent in agents:
                await agent.on_challenge(
                    result.challenger_id,
                    result.challenged_id,
                    result.was_bluff,
                    result.loser_id,
                    result.roulette_result == "survived",
                    engine.get_game_state()
                )

                if result.roulette_result == "eliminated":
                    await agent.on_elimination(
                        result.loser_id,
                        result.challenger_id if result.was_bluff else result.challenged_id,
                        engine.get_game_state()
                    )

            # Check for game over
            if engine.check_game_over():
                return False

            # Start new round after challenge
            engine.setup_round()

            # Notify round start
            for agent in agents:
                await agent.on_round_start(engine.get_game_state())

            if current_player.is_human:
                ui.wait_for_enter()

            return True

    # No challenge, player takes action
    if not current_player.is_human:
        ui.show_thinking(current_player.name)

    action = await current_agent.decide_action(state)

    # Process the action
    if state.mode == GameMode.LIARS_DECK:
        success = engine.process_deck_action(action)
    else:
        success = engine.process_dice_action(action)

    if not success:
        ui.show_error("Invalid action!")
        return True

    # Show the action
    ui.render_action(action, engine.get_game_state())

    # Notify all agents
    for agent in agents:
        await agent.on_action(current_player.id, action, engine.get_game_state())

    # Check if round is over (only for deck mode when cards run out)
    if engine.check_round_over():
        engine.setup_round()
        for agent in agents:
            await agent.on_round_start(engine.get_game_state())

    # Advance to next player
    engine.advance_turn()

    # Brief pause for AI turns
    if not current_player.is_human:
        await asyncio.sleep(1)

    return True


async def main():
    """Main game loop"""
    ui = TerminalUI()

    try:
        # Setup
        engine, agents = await setup_game(ui)

        # Notify game start
        initial_state = engine.get_game_state()
        for agent in agents:
            await agent.on_game_start(initial_state)

        # Setup first round
        engine.setup_round()

        # Notify round start
        for agent in agents:
            await agent.on_round_start(engine.get_game_state())

        # Main game loop
        while True:
            continue_game = await run_turn(engine, agents, ui)

            if not continue_game:
                break

            # Check for game over
            if engine.check_game_over():
                break

        # Game over
        winner = engine.get_winner()
        if winner:
            ui.render_game_over(winner, engine.get_game_state())

            # Notify all agents
            for agent in agents:
                await agent.on_game_over(winner.id, engine.get_game_state())

            # Memorize final game state
            game_events = [
                create_game_over_event(
                    winner.id,
                    engine.get_game_state().round_number,
                    {
                        p.id: {
                            "survived": p.is_alive(),
                            "bullets_survived": p.bullets_survived
                        }
                        for p in engine.get_game_state().players
                    }
                )
            ]

            # Memorize for all AI agents
            for agent in agents:
                if isinstance(agent, AIAgent):
                    await memorize_game_events(game_events, agent.player_id)

        print("\nThanks for playing Liar's Bar!")

    except KeyboardInterrupt:
        print("\n\nGame interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
