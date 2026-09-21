import os
import random

# ── GAME STATE ────────────────────────────────────────────────────────────────
state = {
    "turn":       1,
    "money":      10000,
    "happiness":  50,
    "population": 500,
    "gdp":        25000,
}

pending_investments = []   # delayed payoff queue
event_pool          = []   # shuffled event queue, refilled when empty

# ── INCOME CALCULATION ───────────────────────────────────────────────────────
def income_per_turn():
    """Tax income earned each turn from GDP."""
    return int(state["gdp"] * 0.05)

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

def box_lines_two(title, val1, val2, width=28):
    """Stat box with two value rows (e.g. GDP + income per turn)."""
    inner = width - 2
    top  = "+" + "-" * inner + "+"
    mid  = "|" + title.center(inner) + "|"
    v1   = "|" + str(val1).center(inner) + "|"
    v2   = "|" + str(val2).center(inner) + "|"
    bot  = "+" + "-" * inner + "+"
    return [top, mid, v1, v2, bot]

def render_stats():
    W   = 28
    gap = "    "

    money_b      = box_lines("MONEY",      f"${state['money']:,}",     W)
    happiness_b  = box_lines("HAPPINESS",  f"{state['happiness']}%",   W)
    population_b = box_lines("POPULATION", f"{state['population']:,}", W)
    # GDP box: show income per turn, and happiness bonus if active
    overflow = max(0, state["happiness"] - 100)
    if overflow > 0:
        bonus_pct = overflow * 0.5
        gdp_b = box_lines(
            "GDP",
            f"${state['gdp']:,}",
            W
        )
        # insert two extra lines before the closing +---+
        inner = W - 2
        line_income = "|" + f"+${income_per_turn():,} / turn".center(inner) + "|"
        line_bonus  = "|" + f"{bonus_pct:.0f}% boost (happiness)".center(inner) + "|"
        gdp_b = gdp_b[:-1] + [line_income, line_bonus, gdp_b[-1]]
    else:
        gdp_b = box_lines_two(
            "GDP",
            f"${state['gdp']:,}",
            f"+${income_per_turn():,} / turn",
            W
        )

    print()
    # Row 1: money | happiness
    for l, r in zip(money_b, happiness_b):
        print(f"  {l}{gap}{r}")
    print()
    # Row 2: population | gdp — pad population to match gdp height
    inner = W - 2
    blank = "|" + " " * inner + "|"
    while len(population_b) < len(gdp_b):
        population_b.insert(-1, blank)  # insert blank rows before closing +
    for l, r in zip(population_b, gdp_b):
        print(f"  {l}{gap}{r}")
    print()

def render_header():
    width = 64
    print()
    print("  " + "=" * width)
    print(f"  VOLTAIRE  --  MANAGEMENT PROTOTYPE   [ Turn {state['turn']} ]")
    print("  " + "=" * width)

BOX_WIDTH = 64

def _div():  return "  +" + "-" * BOX_WIDTH + "+"
def _row(text=""):
    text = text[:BOX_WIDTH - 4]
    return "  | " + text.ljust(BOX_WIDTH - 2) + " |"

def render_event(event):
    tag = " OPPORTUNITY " if event.get("investment") else " EVENT "
    print()
    print(_div())
    print("  |" + tag.center(BOX_WIDTH) + "|")
    print(_div())
    for line in event["description"]:
        print(_row(line))
    print(_div())
    for i, opt in enumerate(event["options"]):
        label = opt['label']
        prefix = f"[{i+1}]  "
        max_len = BOX_WIDTH - 4 - len(prefix)
        if len(label) <= max_len:
            print(_row(f"{prefix}{label}"))
        else:
            print(_row(f"{prefix}{label[:max_len]}"))
            print(_row(f"      {label[max_len:].strip()}"))
    print(_div())
    print()

def render_outcome(message, effects):
    print()
    print(_div())
    print("  |" + " OUTCOME ".center(BOX_WIDTH) + "|")
    print(_div())
    print(_row(message))
    print(_div())
    for effect in effects:
        print(_row(effect))
    print(_div())
    print()

def render_investment_return(payoff):
    print()
    print(_div())
    print("  |" + " RESULT ".center(BOX_WIDTH) + "|")
    print(_div())
    for line in payoff["return_message"]:
        print(_row(line))
    print(_div())
    for effect in payoff["return_effects_display"]:
        print(_row(effect))
    print(_div())
    print()

def render_pending_investments():
    if not pending_investments:
        return
    print(_div())
    print("  |" + " ACTIVE INVESTMENTS ".center(BOX_WIDTH) + "|")
    print(_div())
    for inv in pending_investments:
        print(_row(f"  {inv['label']}"))
    print(_div())
    print()

# ── EVENTS ────────────────────────────────────────────────────────────────────
# Each regular event: 2 options only (grant or reject).
# Investment events: marked investment=True, no future hint in labels.
# Population changes: events that logically affect people moving in/out.

EVENTS = [

    # ── 1. TEACHERS ──────────────────────────────────────────────────────────
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
                "label":   "Grant the pay rise      (-$2,000  |  +10 happiness)",
                "outcome": {"money": -2000, "happiness": +10},
                "message": "You approved the pay rise. Teachers are delighted.",
                "effects": ["Money:      -$2,000", "Happiness:  +10%"],
            },
            {
                "label":   "Reject the request      (+$0      |  -12 happiness)",
                "outcome": {"money": 0, "happiness": -12},
                "message": "Request denied. The Teachers Union is furious.",
                "effects": ["Money:      no change", "Happiness:  -12%"],
            },
        ],
    },

    # ── 2. DOCTORS ───────────────────────────────────────────────────────────
    {
        "id": "doctor_shortage",
        "description": [
            "Rural towns are reporting a critical shortage of GPs.",
            "",
            "  Residents are driving 3+ hours for basic appointments.",
            "  The AMA is requesting funding for rural incentive",
            "  packages to attract doctors to regional areas.",
        ],
        "options": [
            {
                "label":   "Fund rural incentives   (-$3,500  |  +12 happiness)",
                "outcome": {"money": -3500, "happiness": +12},
                "message": "Doctors recruited to rural areas. Communities relieved.",
                "effects": ["Money:      -$3,500", "Happiness:  +12%"],
            },
            {
                "label":   "Do nothing              (+$0      |  -12 happiness  |  -30 population)",
                "outcome": {"money": 0, "happiness": -12, "population": -30},
                "message": "No action. Families are leaving for regions with better healthcare.",
                "effects": ["Money:      no change", "Happiness:  -12%", "Population: -30"],
            },
        ],
    },

    # ── 3. HOUSING ───────────────────────────────────────────────────────────
    {
        "id": "housing_crisis",
        "description": [
            "Renters across the state are struggling with record-high",
            "rent increases. A tenant advocacy group is demanding",
            "rental caps and emergency social housing funding.",
        ],
        "options": [
            {
                "label":   "Fund social housing     (-$4,000  |  +13 happiness  |  +40 population)",
                "outcome": {"money": -4000, "happiness": +13, "population": +40},
                "message": "500 housing units approved. Renters moving in from elsewhere.",
                "effects": ["Money:      -$4,000", "Happiness:  +13%", "Population: +40"],
            },
            {
                "label":   "Refer to a committee    (+$0      |  -9 happiness  |  -20 population)",
                "outcome": {"money": 0, "happiness": -9, "population": -20},
                "message": "Referred to committee. Report due in 18 months. Renters leaving.",
                "effects": ["Money:      no change", "Happiness:  -9%", "Population: -20"],
            },
        ],
    },

    # ── 4. AGED CARE ─────────────────────────────────────────────────────────
    {
        "id": "aged_care",
        "description": [
            "A damning report found understaffing in aged care",
            "facilities. Elderly residents are not receiving basic",
            "hygiene or meal support. The media is running the story.",
        ],
        "options": [
            {
                "label":   "Increase aged care funding  (-$3,000  |  +11 happiness)",
                "outcome": {"money": -3000, "happiness": +11},
                "message": "New staffing minimums funded. Families of residents relieved.",
                "effects": ["Money:      -$3,000", "Happiness:  +11%"],
            },
            {
                "label":   "Blame the previous govt     (+$0      |  -11 happiness)",
                "outcome": {"money": 0, "happiness": -11},
                "message": "Blame deflected. Nobody believed it. Happiness craters.",
                "effects": ["Money:      no change", "Happiness:  -11%"],
            },
        ],
    },

    # ── 5. MENTAL HEALTH ─────────────────────────────────────────────────────
    {
        "id": "mental_health",
        "description": [
            "Wait times for public mental health services have blown",
            "out to 14 weeks. Community groups are demanding urgent",
            "investment in psychologist and counsellor positions.",
        ],
        "options": [
            {
                "label":   "Fund 50 new counsellors  (-$2,500  |  +10 happiness)",
                "outcome": {"money": -2500, "happiness": +10},
                "message": "New mental health positions funded. Wait times begin to drop.",
                "effects": ["Money:      -$2,500", "Happiness:  +10%"],
            },
            {
                "label":   "Launch an ad campaign    (-$600    |  -7 happiness  |  -15 population)",
                "outcome": {"money": -600, "happiness": -7, "population": -15},
                "message": "Nice posters. Wait times unchanged. People are leaving.",
                "effects": ["Money:      -$600", "Happiness:  -7%", "Population: -15"],
            },
        ],
    },

    # ── 6. COST OF LIVING ────────────────────────────────────────────────────
    {
        "id": "cost_of_living",
        "description": [
            "Grocery prices have surged 18% this year. Families are",
            "skipping meals. A petition with 80,000 signatures demands",
            "a grocery price inquiry and cost-of-living relief.",
        ],
        "options": [
            {
                "label":   "Issue relief payments    (-$3,200  |  +12 happiness  |  +25 population)",
                "outcome": {"money": -3200, "happiness": +12, "population": +25},
                "message": "Relief payments issued. Word spreads -- people moving in.",
                "effects": ["Money:      -$3,200", "Happiness:  +12%", "Population: +25"],
            },
            {
                "label":   "Tell them to budget better  (+$0  |  -14 happiness  |  -35 population)",
                "outcome": {"money": 0, "happiness": -14, "population": -35},
                "message": "The press conference was a disaster. Families are packing up.",
                "effects": ["Money:      no change", "Happiness:  -14%", "Population: -35"],
            },
        ],
    },

    # ── 7. ROADS ─────────────────────────────────────────────────────────────
    {
        "id": "roads",
        "description": [
            "Regional roads have deteriorated badly after the wet season.",
            "Three towns are semi-isolated. The transport department",
            "is requesting emergency repair funding.",
        ],
        "options": [
            {
                "label":   "Fund full repairs        (-$2,800  |  +9 happiness  |  +10 population)",
                "outcome": {"money": -2800, "happiness": +9, "population": +10},
                "message": "Roads repaired. Towns reconnected. Regional growth resumes.",
                "effects": ["Money:      -$2,800", "Happiness:  +9%", "Population: +10"],
            },
            {
                "label":   "Defer to next year       (+$0      |  -8 happiness  |  -20 population)",
                "outcome": {"money": 0, "happiness": -8, "population": -20},
                "message": "Deferred. An isolated town begins to empty out.",
                "effects": ["Money:      no change", "Happiness:  -8%", "Population: -20"],
            },
        ],
    },

    # ── 8. BUSHFIRE ──────────────────────────────────────────────────────────
    {
        "id": "bushfire_prep",
        "description": [
            "Fire authorities are warning of a severe bushfire season.",
            "Hazard reduction burns have fallen 40% behind schedule.",
            "Rural communities are demanding urgent action.",
        ],
        "options": [
            {
                "label":   "Fund hazard burns        (-$2,200  |  +9 happiness)",
                "outcome": {"money": -2200, "happiness": +9},
                "message": "Burns scheduled immediately. Rural communities feel safer.",
                "effects": ["Money:      -$2,200", "Happiness:  +9%"],
            },
            {
                "label":   "Wait and see             (+$0      |  -10 happiness  |  -25 population)",
                "outcome": {"money": 0, "happiness": -10, "population": -25},
                "message": "No action. A bad fire season drives families out of the region.",
                "effects": ["Money:      no change", "Happiness:  -10%", "Population: -25"],
            },
        ],
    },

    # ── 9. REMOTE COMMUNITIES ────────────────────────────────────────────────
    {
        "id": "remote_communities",
        "description": [
            "Remote Indigenous communities are reporting critical gaps",
            "in clean water access, housing, and school attendance.",
            "A community coalition has requested federal support.",
        ],
        "options": [
            {
                "label":   "Fund a full package      (-$4,500  |  +14 happiness  |  +20 population)",
                "outcome": {"money": -4500, "happiness": +14, "population": +20},
                "message": "Comprehensive funding approved. Communities stabilise and grow.",
                "effects": ["Money:      -$4,500", "Happiness:  +14%", "Population: +20"],
            },
            {
                "label":   "Send a delegation        (-$300    |  -9 happiness  |  -15 population)",
                "outcome": {"money": -300, "happiness": -9, "population": -15},
                "message": "A delegation sent. No action follows. Communities continue to shrink.",
                "effects": ["Money:      -$300", "Happiness:  -9%", "Population: -15"],
            },
        ],
    },

    # ── 10. PUBLIC TRANSPORT ─────────────────────────────────────────────────
    {
        "id": "public_transport",
        "description": [
            "Chronic delays and overcrowding on the metro network.",
            "A peak-hour breakdown stranded 12,000 passengers.",
            "Commuters are demanding action.",
        ],
        "options": [
            {
                "label":   "Invest in upgrades       (-$3,800  |  +11 happiness  |  +30 population)",
                "outcome": {"money": -3800, "happiness": +11, "population": +30},
                "message": "Upgrades funded. Better transport attracts workers to the area.",
                "effects": ["Money:      -$3,800", "Happiness:  +11%", "Population: +30"],
            },
            {
                "label":   "Apologise and move on    (+$0      |  -9 happiness  |  -20 population)",
                "outcome": {"money": 0, "happiness": -9, "population": -20},
                "message": "Apology issued. Commuters start working from home. Or leaving.",
                "effects": ["Money:      no change", "Happiness:  -9%", "Population: -20"],
            },
        ],
    },

    # ── 11. IMMIGRANT FAMILY ─────────────────────────────────────────────────
    {
        "id": "immigrant_family",
        "description": [
            "An immigrant family has submitted a formal residency",
            "application. They are skilled workers and wish to",
            "bring extended family. They need housing support",
            "and a community settlement package to get started.",
        ],
        "options": [
            {
                "label":   "Approve and fund them    (-$1,800  |  +7 happiness  |  +60 population)",
                "outcome": {"money": -1800, "happiness": +7, "population": +60},
                "message": "Family approved and settled. Word spreads internationally.",
                "effects": ["Money:      -$1,800", "Happiness:  +7%", "Population: +60"],
            },
            {
                "label":   "Reject the application   (+$0      |  -6 happiness)",
                "outcome": {"money": 0, "happiness": -6},
                "message": "Application rejected. Community advocates are disappointed.",
                "effects": ["Money:      no change", "Happiness:  -6%"],
            },
        ],
    },

    # ── INVESTMENT 1: LITHIUM SURVEY ─────────────────────────────────────────
    {
        "id": "lithium_survey",
        "investment": True,
        "description": [
            "A mining company has identified signs of a large lithium",
            "deposit in the outback. They need $5,000 in government",
            "survey co-funding to confirm viability of the site.",
        ],
        "options": [
            {
                "label":   "Co-fund the survey       (-$5,000)",
                "outcome": {"money": -5000},
                "message": "Survey funded. The geologists are heading out to the site.",
                "effects": ["Money:  -$5,000"],
                "investment_payoff": {
                    "turns": 3,
                    "outcome": {"money": +18000, "gdp": +8000},
                    "return_message": [
                        "The lithium deposit was confirmed -- it's enormous.",
                        "The mining company has signed a royalties agreement.",
                        "Revenue and GDP have received a significant boost.",
                    ],
                    "return_effects_display": ["Money:  +$18,000", "GDP:    +$8,000"],
                },
            },
            {
                "label":   "Decline the opportunity  (+$0      |  no change)",
                "outcome": {"money": 0},
                "message": "Declined. The company takes the proposal to another state.",
                "effects": ["Money:  no change"],
            },
        ],
    },

    # ── INVESTMENT 2: TRADE DELEGATION ───────────────────────────────────────
    {
        "id": "trade_delegation",
        "investment": True,
        "description": [
            "The trade minister is proposing an overseas delegation",
            "to negotiate an agricultural export deal with Southeast",
            "Asia. The trip will cost $4,200 in government funding.",
        ],
        "options": [
            {
                "label":   "Send the delegation      (-$4,200  |  +3 happiness)",
                "outcome": {"money": -4200, "happiness": +3},
                "message": "Delegation departed. The minister has packed 14 bags.",
                "effects": ["Money:      -$4,200", "Happiness:  +3% (business confidence)"],
                "investment_payoff": {
                    "turns": 4,
                    "outcome": {"money": +15000, "gdp": +12000, "happiness": +8, "population": +50},
                    "return_message": [
                        "The trade delegation was a success.",
                        "A landmark agricultural export deal has been signed.",
                        "Farmers are reporting record order books.",
                        "New jobs are drawing workers to the region.",
                    ],
                    "return_effects_display": [
                        "Money:      +$15,000",
                        "GDP:        +$12,000",
                        "Happiness:  +8%",
                        "Population: +50",
                    ],
                },
            },
            {
                "label":   "Cancel the delegation    (+$0      |  -3 happiness)",
                "outcome": {"money": 0, "happiness": -3},
                "message": "Delegation cancelled. The trade minister is devastated.",
                "effects": ["Money:      no change", "Happiness:  -3%"],
            },
        ],
    },

]

# ── EVENT QUEUE ───────────────────────────────────────────────────────────────
def next_event():
    """Return the next event from a shuffled pool. Refill when exhausted."""
    global event_pool
    if not event_pool:
        event_pool = EVENTS[:]
        random.shuffle(event_pool)
    return event_pool.pop()

# ── TURN LOGIC ────────────────────────────────────────────────────────────────
def apply_outcome(outcome):
    for key, delta in outcome.items():
        state[key] = max(0, state[key] + delta)
    state["happiness"]  = max(0, min(200, state["happiness"]))
    state["population"] = max(0, state["population"])

def happiness_gdp_bonus():
    """Every 1% of happiness above 100 adds 0.5% to GDP each turn."""
    overflow = max(0, state["happiness"] - 100)
    if overflow > 0:
        bonus = int(state["gdp"] * (overflow * 0.005))
        state["gdp"] += bonus
        return bonus
    return 0

def passive_turn_effects():
    gdp_growth = int(state["gdp"] * 0.01)
    state["gdp"] += gdp_growth
    happiness_gdp_bonus()
    state["money"] += income_per_turn()

def tick_investments():
    returned = []
    for inv in pending_investments:
        inv["turns_left"] -= 1
        if inv["turns_left"] <= 0:
            returned.append(inv)
    for inv in returned:
        pending_investments.remove(inv)
        apply_outcome(inv["payoff"]["outcome"])
        render_investment_return(inv["payoff"])
        input("  Press Enter to continue...")

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
        print("  +" + "=" * 60 + "+")
        print("  |" + "GAME OVER -- YOU HAVE BEEN VOTED OUT".center(60) + "|")
        print("  |" + "Happiness hit 0%. The people have had enough.".center(60) + "|")
        print("  +" + "=" * 60 + "+")
        print()
        return True
    if state["money"] <= 0:
        print()
        print("  +" + "=" * 60 + "+")
        print("  |" + "GAME OVER -- THE GOVERNMENT IS BANKRUPT".center(60) + "|")
        print("  |" + "You ran out of money. Classic rookie mistake.".center(60) + "|")
        print("  +" + "=" * 60 + "+")
        print()
        return True
    if state["population"] <= 0:
        print()
        print("  +" + "=" * 60 + "+")
        print("  |" + "GAME OVER -- EVERYONE HAS LEFT".center(60) + "|")
        print("  |" + "Population hit 0. You governed an empty territory.".center(60) + "|")
        print("  +" + "=" * 60 + "+")
        print()
        return True
    return False

# ── MAIN LOOP ─────────────────────────────────────────────────────────────────
def main():
    while True:
        clear()
        render_header()
        render_stats()
        render_pending_investments()

        if check_game_over():
            input("  Press Enter to quit...")
            break

        tick_investments()

        event = next_event()
        render_event(event)

        choice_index = get_player_choice(len(event["options"]))
        chosen = event["options"][choice_index]

        if event.get("investment") and "investment_payoff" in chosen:
            p = chosen["investment_payoff"]
            pending_investments.append({
                "turns_left": p["turns"],
                "label":      event["id"].replace("_", " ").title(),
                "payoff":     p,
            })

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