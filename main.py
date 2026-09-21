import os

# ── GAME STATE ────────────────────────────────────────────────────────────────
state = {
    "turn":       1,
    "money":      10000,
    "happiness":  50,
    "population": 500,
    "gdp":        25000,
}

# ── UI HELPERS ────────────────────────────────────────────────────────────────
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def box_lines(title, value, width=28):
    inner = width - 2
    top = "+" + "-" * inner + "+"
    mid = "|" + title.center(inner) + "|"
    val = "|" + str(value).center(inner) + "|"
    bot = "+" + "-" * inner + "+"
    return [top, mid, val, bot]

def render_stats():
    W = 28
    money_b      = box_lines("MONEY",      f"${state['money']:,}",     W)
    happiness_b  = box_lines("HAPPINESS",  f"{state['happiness']}%",   W)
    population_b = box_lines("POPULATION", f"{state['population']:,}", W)
    gdp_b        = box_lines("GDP",        f"${state['gdp']:,}",       W)

    gap = "    "
    print()
    for l, r in zip(money_b, happiness_b):
        print(f"  {l}{gap}{r}")
    print()
    for l, r in zip(population_b, gdp_b):
        print(f"  {l}{gap}{r}")
    print()

def render_header():
    width = 64
    print()
    print("  " + "=" * width)
    print(f"  VOLTAIRE  --  MANAGEMENT PROTOTYPE   [ Turn {state['turn']} ]")
    print("  " + "=" * width)

BOX_WIDTH = 64  # total inner width (between the | characters)

def render_event(event):
    div = "  +" + "-" * BOX_WIDTH + "+"
    def row(text=""):
        text = text[:BOX_WIDTH - 4]
        return "  | " + text.ljust(BOX_WIDTH - 2) + " |"

    print()
    print(div)
    print("  |" + " EVENT ".center(BOX_WIDTH) + "|")
    print(div)
    for line in event["description"]:
        print(row(line))
    print(div)
    for i, opt in enumerate(event["options"]):
        print(row(f"[{i+1}]  {opt['label']}"))
    print(div)
    print()

def render_outcome(message, effects):
    div = "  +" + "-" * BOX_WIDTH + "+"
    def row(text=""):
        text = text[:BOX_WIDTH - 4]
        return "  | " + text.ljust(BOX_WIDTH - 2) + " |"

    print()
    print(div)
    print("  |" + " OUTCOME ".center(BOX_WIDTH) + "|")
    print(div)
    print(row(message))
    print(div)
    for effect in effects:
        print(row(effect))
    print(div)
    print()

# ── EVENTS ────────────────────────────────────────────────────────────────────
EVENTS = [
    {
        "id": "teacher_pay",
        "description": [
            "The Teachers Union has submitted a formal request.",
            "",
            "  'Our members haven't had a pay rise in three years.",
            "   We are asking for a $2,000 budget increase to fund",
            "   better wages. Classrooms are suffering.'",
        ],
        "options": [
            {
                "label":   "Grant the pay rise         (-$2,000  |  +10 happiness)",
                "outcome": {"money": -2000, "happiness": +10},
                "message": "You approved the pay rise. Teachers are delighted.",
                "effects": ["Money:      -$2,000", "Happiness:  +10%"],
            },
            {
                "label":   "Offer a smaller rise       (-$800    |  +4 happiness)",
                "outcome": {"money": -800, "happiness": +4},
                "message": "A partial rise was offered. Teachers are satisfied, not thrilled.",
                "effects": ["Money:      -$800", "Happiness:  +4%"],
            },
            {
                "label":   "Reject the request         (+$0      |  -8 happiness)",
                "outcome": {"money": 0, "happiness": -8},
                "message": "Request denied. The Teachers Union is furious.",
                "effects": ["Money:      no change", "Happiness:  -8%"],
            },
        ],
    },
    # Future events go here
]

# ── TURN LOGIC ────────────────────────────────────────────────────────────────
def apply_outcome(outcome):
    for key, delta in outcome.items():
        state[key] = max(0, state[key] + delta)
    state["happiness"] = max(0, min(100, state["happiness"]))

def passive_turn_effects():
    gdp_growth = int(state["gdp"] * 0.01)
    state["gdp"] += gdp_growth
    tax_income = int(state["gdp"] * 0.05)
    state["money"] += tax_income

def get_event_for_turn():
    index = (state["turn"] - 1) % len(EVENTS)
    return EVENTS[index]

def get_player_choice(num_options):
    while True:
        try:
            choice = int(input("  Your choice: "))
            if 1 <= choice <= num_options:
                return choice - 1
            print(f"  Enter a number between 1 and {num_options}.")
        except ValueError:
            print("  Please enter a valid number.")

def check_game_over():
    if state["happiness"] <= 0:
        print()
        print("  +" + "=" * 56 + "+")
        print("  |" + "GAME OVER -- YOU HAVE BEEN VOTED OUT".center(56) + "|")
        print("  |" + "Happiness hit 0%. The people have had enough.".center(56) + "|")
        print("  +" + "=" * 56 + "+")
        print()
        return True
    if state["money"] <= 0:
        print()
        print("  +" + "=" * 56 + "+")
        print("  |" + "GAME OVER -- THE GOVERNMENT IS BANKRUPT".center(56) + "|")
        print("  |" + "You ran out of money. Classic rookie mistake.".center(56) + "|")
        print("  +" + "=" * 56 + "+")
        print()
        return True
    return False

# ── MAIN LOOP ─────────────────────────────────────────────────────────────────
def main():
    while True:
        clear()
        render_header()
        render_stats()

        if check_game_over():
            input("  Press Enter to quit...")
            break

        event = get_event_for_turn()
        render_event(event)

        choice_index = get_player_choice(len(event["options"]))
        chosen = event["options"][choice_index]

        apply_outcome(chosen["outcome"])
        passive_turn_effects()

        clear()
        render_header()
        render_stats()
        render_outcome(chosen["message"], chosen["effects"])

        state["turn"] += 1
        input("  Press Enter to continue to next turn...")

if __name__ == "__main__":
    main()