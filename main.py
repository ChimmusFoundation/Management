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
def cli_main():
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

class ManagementApp:
    """Cross-platform desktop UI for the management game."""

    def __init__(self, root):
        import tkinter as tk
        from tkinter import messagebox, ttk

        self.tk = tk
        self.messagebox = messagebox
        self.ttk = ttk
        self.root = root
        self.root.title("Voltaire - Management")
        self.root.minsize(820, 620)
        self.root.geometry("980x720")
        self.history = []
        self.current_event = None
        self.game_over = False
        self.turn_complete = False
        self.dark_mode = False

        self.style = ttk.Style(root)
        style = self.style
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("TkDefaultFont", 20, "bold"))
        style.configure("StatValue.TLabel", font=("TkDefaultFont", 16, "bold"))
        style.configure("Card.TFrame", relief="groove", borderwidth=1)
        style.configure("Option.TButton", anchor="w", padding=(12, 10))

        self.status = tk.StringVar()
        self.theme_label = tk.StringVar(value="Dark theme")
        self.stat_vars = {
            "money": tk.StringVar(),
            "happiness": tk.StringVar(),
            "population": tk.StringVar(),
            "gdp": tk.StringVar(),
            "income": tk.StringVar(),
        }

        self._build_shell()
        self.root.bind("<Key>", self._handle_key)
        self._start_turn()

    def _build_shell(self):
        from tkinter import ttk

        header = ttk.Frame(self.root, padding=(24, 18, 24, 8))
        header.pack(fill="x")
        ttk.Label(header, text="VOLTAIRE", style="Title.TLabel").pack(side="left")
        ttk.Checkbutton(
            header,
            textvariable=self.theme_label,
            command=self._toggle_theme,
        ).pack(side="right", padx=(12, 0))
        ttk.Label(header, textvariable=self.status).pack(side="right", pady=6)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        self.dashboard = ttk.Frame(self.notebook, padding=20)
        self.events_tab = ttk.Frame(self.notebook, padding=20)
        self.investments_tab = ttk.Frame(self.notebook, padding=20)
        self.history_tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(self.dashboard, text="Dashboard")
        self.notebook.add(self.events_tab, text="Events")
        self.notebook.add(self.investments_tab, text="Investments")
        self.notebook.add(self.history_tab, text="History")

        self._build_dashboard()
        self._build_events()
        self._build_investments()
        self._build_history()

    def _build_dashboard(self):
        from tkinter import ttk

        ttk.Label(self.dashboard, text="State overview",
                  font=("TkDefaultFont", 15, "bold")).pack(anchor="w")
        stats = ttk.Frame(self.dashboard)
        stats.pack(fill="x", pady=(14, 20))
        labels = [
            ("money", "Money"), ("happiness", "Happiness"),
            ("population", "Population"), ("gdp", "GDP"),
            ("income", "Income / turn"),
        ]
        for column, (key, label) in enumerate(labels):
            card = ttk.Frame(stats, style="Card.TFrame", padding=12)
            card.grid(row=0, column=column, sticky="nsew", padx=4)
            stats.columnconfigure(column, weight=1)
            ttk.Label(card, text=label).pack(anchor="w")
            ttk.Label(card, textvariable=self.stat_vars[key],
                      style="StatValue.TLabel").pack(anchor="w", pady=(7, 0))

        self.dashboard_message = ttk.Label(
            self.dashboard, text="Choose an option in the Events tab to govern your state.",
            wraplength=720)
        self.dashboard_message.pack(anchor="w", pady=10)
        ttk.Button(self.dashboard, text="View current event",
                   command=lambda: self.notebook.select(self.events_tab)).pack(anchor="w", pady=8)

    def _build_events(self):
        from tkinter import ttk

        self.event_title = ttk.Label(self.events_tab, font=("TkDefaultFont", 15, "bold"))
        self.event_title.pack(anchor="w")
        self.event_kind = ttk.Label(self.events_tab)
        self.event_kind.pack(anchor="w", pady=(2, 12))
        self.event_description = ttk.Label(
            self.events_tab, justify="left", anchor="w", wraplength=820)
        self.event_description.pack(fill="x", pady=(0, 18))
        ttk.Label(self.events_tab, text="Your decision",
                  font=("TkDefaultFont", 12, "bold")).pack(anchor="w")
        self.options_frame = ttk.Frame(self.events_tab)
        self.options_frame.pack(fill="x", pady=8)
        self.event_result = ttk.Label(
            self.events_tab, justify="left", anchor="w", wraplength=820)
        self.event_result.pack(fill="x", pady=16)
        self.next_turn_button = ttk.Button(
            self.events_tab, text="Next turn  [N]", command=self._next_turn,
            state="disabled")
        self.next_turn_button.pack(anchor="w", pady=(4, 0))
        ttk.Label(
            self.events_tab,
            text="Keyboard: 1/2 choose an option  •  N next turn  •  D toggle theme  •  Tab switch tabs",
        ).pack(anchor="w", pady=(14, 0))

    def _build_investments(self):
        from tkinter import ttk

        ttk.Label(self.investments_tab, text="Active investments",
                  font=("TkDefaultFont", 15, "bold")).pack(anchor="w")
        self.investments_text = ttk.Label(
            self.investments_tab, justify="left", anchor="nw", wraplength=820)
        self.investments_text.pack(fill="both", expand=True, pady=(14, 0))

    def _build_history(self):
        from tkinter import ttk

        ttk.Label(self.history_tab, text="Decision history",
                  font=("TkDefaultFont", 15, "bold")).pack(anchor="w")
        self.history_text = ttk.Label(
            self.history_tab, justify="left", anchor="nw", wraplength=820)
        self.history_text.pack(fill="both", expand=True, pady=(14, 0))

    def _update_stats(self):
        self.stat_vars["money"].set(f"${state['money']:,}")
        self.stat_vars["happiness"].set(f"{state['happiness']}%")
        self.stat_vars["population"].set(f"{state['population']:,}")
        self.stat_vars["gdp"].set(f"${state['gdp']:,}")
        self.stat_vars["income"].set(f"+${income_per_turn():,}")
        self.status.set(f"Turn {state['turn']}")

    def _update_investments(self):
        if not pending_investments:
            self.investments_text.configure(text="No active investments.")
            return
        lines = [
            f"{item['label']} - returns in {item['turns_left']} "
            f"turn{'s' if item['turns_left'] != 1 else ''}"
            for item in pending_investments
        ]
        self.investments_text.configure(text="\n\n".join(lines))

    def _update_history(self):
        if not self.history:
            self.history_text.configure(text="No decisions yet.")
        else:
            self.history_text.configure(text="\n\n".join(self.history))

    def _start_turn(self):
        if self.game_over:
            return
        self.turn_complete = False
        self.next_turn_button.configure(state="disabled")
        returned = []
        for investment in pending_investments:
            investment["turns_left"] -= 1
            if investment["turns_left"] <= 0:
                returned.append(investment)
        for investment in returned:
            pending_investments.remove(investment)
            apply_outcome(investment["payoff"]["outcome"])
            payoff = investment["payoff"]
            returned_text = "Investment returned:\n" + "\n".join(
                payoff["return_message"] + payoff["return_effects_display"])
            self.history.insert(0, returned_text)
            self.dashboard_message.configure(text=returned_text)

        self.current_event = next_event()
        self._render_event()
        self._update_stats()
        self._update_investments()
        self._update_history()
        self.notebook.select(self.events_tab)

    def _render_event(self):
        event = self.current_event
        self.event_title.configure(text=event["id"].replace("_", " ").title())
        self.event_kind.configure(
            text="Investment opportunity" if event.get("investment") else "Public event")
        self.event_description.configure(text="\n".join(event["description"]))
        self.event_result.configure(text="")
        for child in self.options_frame.winfo_children():
            child.destroy()
        for index, option in enumerate(event["options"]):
            button = self.ttk.Button(
                self.options_frame,
                text=f"{index + 1}. {option['label']}",
                style="Option.TButton",
                command=lambda selected=index: self._choose(selected))
            button.pack(fill="x", pady=4)

    def _choose(self, index):
        if self.game_over:
            return
        event = self.current_event
        chosen = event["options"][index]
        if event.get("investment") and "investment_payoff" in chosen:
            payoff = chosen["investment_payoff"]
            pending_investments.append({
                "turns_left": payoff["turns"],
                "label": event["id"].replace("_", " ").title(),
                "payoff": payoff,
            })
        apply_outcome(chosen["outcome"])
        passive_turn_effects()
        result = chosen["message"] + "\n\n" + "\n".join(chosen["effects"])
        self.event_result.configure(text=result)
        self.dashboard_message.configure(text=result)
        self.history.insert(0, f"Turn {state['turn']}: {result}")
        state["turn"] += 1
        self.turn_complete = True
        self.next_turn_button.configure(state="normal")
        for child in self.options_frame.winfo_children():
            child.configure(state="disabled")
        self._update_stats()
        self._update_investments()
        self._update_history()
        if check_game_over():
            self.game_over = True
            self.turn_complete = False
            self.next_turn_button.configure(state="disabled")
            for child in self.options_frame.winfo_children():
                child.configure(state="disabled")
            self.status.set("Game over")
            self.messagebox.showinfo("Game over", self._game_over_message())
            return

    def _next_turn(self):
        if self.game_over or not self.turn_complete:
            return
        self._start_turn()

    def _handle_key(self, event):
        key = event.keysym.lower()
        if key in ("1", "2") and not self.turn_complete:
            index = int(key) - 1
            if self.current_event and index < len(self.current_event["options"]):
                self._choose(index)
        elif key == "n":
            self._next_turn()
        elif key == "d":
            self._toggle_theme()

    def _toggle_theme(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.style.configure(".", background="#202124", foreground="#f1f3f4")
            self.style.configure("TFrame", background="#202124")
            self.style.configure("TLabel", background="#202124", foreground="#f1f3f4")
            self.style.configure("Card.TFrame", background="#2d2f31")
            self.style.configure("TCheckbutton", background="#202124", foreground="#f1f3f4")
            self.style.configure("TNotebook", background="#202124")
            self.style.configure("TNotebook.Tab", background="#303134", foreground="#f1f3f4")
            self.style.map(
                "TButton",
                background=[("active", "#4b5563"), ("!disabled", "#35383c")],
                foreground=[("!disabled", "#f1f3f4")],
            )
            self.style.configure("Option.TButton", background="#35383c", foreground="#f1f3f4")
            self.root.configure(background="#202124")
            self.theme_label.set("Light theme")
        else:
            self.style.configure(".", background="#f0f0f0", foreground="#000000")
            self.style.configure("TFrame", background="#f0f0f0")
            self.style.configure("TLabel", background="#f0f0f0", foreground="#000000")
            self.style.configure("Card.TFrame", background="#f0f0f0")
            self.style.configure("TCheckbutton", background="#f0f0f0", foreground="#000000")
            self.style.configure("TNotebook", background="#f0f0f0")
            self.style.configure("TNotebook.Tab", background="#f0f0f0", foreground="#000000")
            self.style.map(
                "TButton",
                background=[("active", "#e0e0e0"), ("!disabled", "#f0f0f0")],
                foreground=[("!disabled", "#000000")],
            )
            self.style.configure("Option.TButton", background="#f0f0f0", foreground="#000000")
            self.root.configure(background="#f0f0f0")
            self.theme_label.set("Dark theme")

    def _game_over_message(self):
        if state["happiness"] <= 0:
            return "Happiness reached 0%. You have been voted out."
        if state["money"] <= 0:
            return "The government is bankrupt."
        return "The population has reached zero."


def main():
    import tkinter as tk
    try:
        root = tk.Tk()
    except tk.TclError as error:
        # Servers and containers often have no X11/Wayland display. Keep the
        # game usable there instead of failing before the first turn.
        if "display" not in str(error).lower():
            raise
        print("No graphical display detected; starting the terminal interface.")
        cli_main()
        return
    ManagementApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()