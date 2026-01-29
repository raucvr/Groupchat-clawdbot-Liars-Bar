"""
ASCII Art for Liar's Bar

Card and dice ASCII art, plus game decorations.
"""

from game.constants import CardType


# Card ASCII art
CARD_ART = {
    CardType.QUEEN: r"""
┌─────────┐
│ Q       │
│         │
│    ♠    │
│         │
│       Q │
└─────────┘""",
    CardType.KING: r"""
┌─────────┐
│ K       │
│         │
│    ♠    │
│         │
│       K │
└─────────┘""",
    CardType.ACE: r"""
┌─────────┐
│ A       │
│         │
│    ♠    │
│         │
│       A │
└─────────┘""",
    CardType.JOKER: r"""
┌─────────┐
│ ★  ★  ★ │
│         │
│  JOKER  │
│         │
│ ★  ★  ★ │
└─────────┘""",
}

# Card back (hidden cards)
CARD_BACK = r"""
┌─────────┐
│░░░░░░░░░│
│░░░░░░░░░│
│░░░░░░░░░│
│░░░░░░░░░│
│░░░░░░░░░│
└─────────┘"""

# Small card representations
SMALL_CARD = {
    CardType.QUEEN: "[Q]",
    CardType.KING: "[K]",
    CardType.ACE: "[A]",
    CardType.JOKER: "[★]",
}

# Dice ASCII art
DICE_ART = {
    1: r"""
┌───────┐
│       │
│   ●   │
│       │
└───────┘""",
    2: r"""
┌───────┐
│ ●     │
│       │
│     ● │
└───────┘""",
    3: r"""
┌───────┐
│ ●     │
│   ●   │
│     ● │
└───────┘""",
    4: r"""
┌───────┐
│ ●   ● │
│       │
│ ●   ● │
└───────┘""",
    5: r"""
┌───────┐
│ ●   ● │
│   ●   │
│ ●   ● │
└───────┘""",
    6: r"""
┌───────┐
│ ●   ● │
│ ●   ● │
│ ●   ● │
└───────┘""",
}

# Unicode dice faces
DICE_UNICODE = {
    1: "⚀",
    2: "⚁",
    3: "⚂",
    4: "⚃",
    5: "⚄",
    6: "⚅",
}

# Revolver ASCII art
REVOLVER_ART = r"""
      _______
     /       \
    |  O   O  |
    |    O    |  <-- 6 CHAMBERS
    |  O   O  |
     \_______/
        ||
       /||\
      / || \
     /  ||  \
    RUSSIAN ROULETTE
"""

REVOLVER_FIRE = r"""
    💥 BANG! 💥
"""

REVOLVER_CLICK = r"""
    *click*
"""

# Game title
TITLE_ART = r"""
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║   ██╗     ██╗ █████╗ ██████╗ ███████╗                ║
║   ██║     ██║██╔══██╗██╔══██╗██╔════╝                ║
║   ██║     ██║███████║██████╔╝███████╗                ║
║   ██║     ██║██╔══██║██╔══██╗╚════██║                ║
║   ███████╗██║██║  ██║██║  ██║███████║                ║
║   ╚══════╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝                ║
║                                                       ║
║   ██████╗  █████╗ ██████╗                            ║
║   ██╔══██╗██╔══██╗██╔══██╗                           ║
║   ██████╔╝███████║██████╔╝                           ║
║   ██╔══██╗██╔══██║██╔══██╗                           ║
║   ██████╔╝██║  ██║██║  ██║                           ║
║   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝                           ║
║                                                       ║
║           🍺 The Bluffing Game 🎭                    ║
╚═══════════════════════════════════════════════════════╝
"""

# Simple title for smaller terminals
TITLE_SIMPLE = r"""
╔═══════════════════════════════╗
║     🎭 LIAR'S BAR 🍺         ║
║     The Bluffing Game         ║
╚═══════════════════════════════╝
"""

# Player status indicators
PLAYER_ALIVE = "✓"
PLAYER_DEAD = "💀"
PLAYER_CURRENT = "👉"

# Character icons
CHARACTER_ICONS = {
    "scub": "🐶",      # Bulldog
    "foxy": "🦊",      # Fox
    "bristle": "🐷",   # Pig
    "toar": "🐂",      # Bull
    "human": "👤",     # Human
    "claude": "🤖",    # Claude AI
    "gpt": "🧠",       # GPT AI
    "llama": "🦙",     # Llama AI
}


def get_card_art(card: CardType) -> str:
    """Get ASCII art for a card"""
    return CARD_ART.get(card, CARD_BACK)


def get_dice_art(value: int) -> str:
    """Get ASCII art for a die face"""
    return DICE_ART.get(value, DICE_ART[1])


def get_dice_unicode(value: int) -> str:
    """Get Unicode character for a die face"""
    return DICE_UNICODE.get(value, "?")


def format_dice_row(dice: list[int]) -> str:
    """Format a row of dice as Unicode"""
    return " ".join(get_dice_unicode(d) for d in dice)


def get_cards_inline(cards: list[CardType]) -> str:
    """Format cards inline"""
    return " ".join(SMALL_CARD.get(c, "[?]") for c in cards)


def get_character_icon(character: str) -> str:
    """Get icon for a character"""
    return CHARACTER_ICONS.get(character.lower(), "👤")


def print_horizontal_cards(cards: list[CardType]) -> str:
    """Print cards horizontally side by side"""
    if not cards:
        return ""

    # Get art for each card
    arts = [CARD_ART.get(c, CARD_BACK).strip().split("\n") for c in cards]

    # Combine lines
    result = []
    for row_idx in range(len(arts[0])):
        row = "  ".join(art[row_idx] for art in arts)
        result.append(row)

    return "\n".join(result)


def print_horizontal_dice(dice: list[int]) -> str:
    """Print dice horizontally side by side"""
    if not dice:
        return ""

    # Get art for each die
    arts = [DICE_ART.get(d, DICE_ART[1]).strip().split("\n") for d in dice]

    # Combine lines
    result = []
    for row_idx in range(len(arts[0])):
        row = "  ".join(art[row_idx] for art in arts)
        result.append(row)

    return "\n".join(result)
