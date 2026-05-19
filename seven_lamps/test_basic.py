"""
Quick test script to validate imports and basic functionality
"""
import sys
import os

# Add parent dir to path
parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent)

print("Testing imports...")

def test_import(name, module_path):
    try:
        __import__(module_path)
        print(f"  [OK] {name}")
        return True
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        return False

# Test all imports
results = []
results.append(test_import("core.enums", "seven_lamps.core.enums"))
results.append(test_import("core.constants", "seven_lamps.core.constants"))
results.append(test_import("cards.card_base", "seven_lamps.cards.card_base"))
results.append(test_import("cards.card_registry", "seven_lamps.cards.card_registry"))
results.append(test_import("mechanics.lamp_system", "seven_lamps.mechanics.lamp_system"))
results.append(test_import("mechanics.response_zone", "seven_lamps.mechanics.response_zone"))
results.append(test_import("mechanics.win_checker", "seven_lamps.mechanics.win_checker"))
results.append(test_import("deck.deck_builder", "seven_lamps.deck.deck_builder"))
results.append(test_import("core.game_state", "seven_lamps.core.game_state"))
results.append(test_import("ui.cli", "seven_lamps.ui.cli"))

if not all(results):
    print("\nSome imports failed! Exiting.")
    sys.exit(1)

print("\nTesting basic functionality...")

from seven_lamps.core.enums import ClassType
from seven_lamps.cards.card_registry import get_pool, list_all_cards
from seven_lamps.deck.deck_builder import quick_build_deck
from seven_lamps.core.game_state import GameState
from seven_lamps.mechanics.win_checker import WinChecker

# Test card registry
all_cards = list_all_cards()
print(f"  [OK] Total cards: {len(all_cards)}")

for cls in [ClassType.LAMPLIGHTER, ClassType.NIGHTWATCH, ClassType.EXTINGUISHER]:
    pool = get_pool(cls)
    print(f"  [OK] {cls.value}: {len(pool)} cards")

# Test deck builder
deck = quick_build_deck(ClassType.LAMPLIGHTER, "斩杀型")
print(f"  [OK] Deck built: {len(deck)} cards")
for c in deck:
    print(f"       - {c.name} ({c.category.value})")

# Test game state
gs = GameState([
    {"id": "p1", "name": "Alice", "class": ClassType.LAMPLIGHTER},
    {"id": "p2", "name": "Bob", "class": ClassType.EXTINGUISHER},
])
print(f"\n  [OK] GameState created")
print(f"       P1 lamps: {gs.get_lamps('p1')}")
print(f"       P2 lamps: {gs.get_lamps('p2')}")

# Test lamp operations
result = gs.add_lamps("p1", 2)
print(f"  [OK] Add lamps: {result['msg']}")
result = gs.reduce_lamps("p2", 1)
print(f"  [OK] Reduce lamps: {result['msg']}")

# Test win checker
wc = WinChecker()
r = wc.check_victory(gs, "p1")
print(f"  [OK] Win check: won={r['won']}")

# Test position system (Nightwatch)
from seven_lamps.mechanics.lamp_system import LampSystem
ls = LampSystem()
ls.light_position(1)
ls.light_position(3)
print(f"  [OK] Nightwatch positions: odd_lit={ls.count_odd_lit()}, all_odd={ls.all_odd_lit()}")

print("\n=== ALL TESTS PASSED ===")
