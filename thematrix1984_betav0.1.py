#!/usr/bin/env python3
import curses
import random
import sys

# === ASCII Banner ===
TITLE = r"""
░▒▓██████████████▓▒░ ░▒▓██████▓▒░▒▓████████▓▒░▒▓███████▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░ ░▒▓█▓▒░   ░▒▓███████▓▒░░▒▓█▓▒░░▒▓██████▓▒░
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
1982
by b145k0 2025
"""

# === Game Data ===
CYCLES = 30
NODES = [
    "The Trainstation",
    "The Construct",
    "Nebuchadnezzar",
    "Oracle's Apartment",
    "Merovingian's Chateau"
]
WAREZ = {
    "RootKit":   (15000, 28000),
    "BlackICE":  (2000,  10000),
    "Datashard": (300,    1000),
    "Trojan":    (1000,   4200),
    "Worm":      (18,     75)
}
WEAPONS = {
    "Beretta 92FS":   {"price":2000, "acc":0.70, "dmg":15, "ammo_key":"Beretta Ammo"},
    "HK MP5K SMG":    {"price":5000, "acc":0.50, "dmg":20, "ammo_key":"MP5K Ammo"},
    "M4 Carbine":     {"price":8000, "acc":0.60, "dmg":25, "ammo_key":"M4 Ammo"}
}
AMMO_PRICES = {
    "Beretta Ammo": 5,
    "MP5K Ammo":    3,
    "M4 Ammo":      7
}

# === Player State ===
credits = 2000
life    = 100
inventory   = {w: 0 for w in WAREZ}
weapons_inv = {}
ammo_inv    = {k: 0 for k in AMMO_PRICES}
location    = random.choice(NODES)

# === Helpers ===
def clamp_life():
    global life
    life = max(0, min(100, life))

def get_prices():
    return {w: random.randint(*rng) for w, rng in WAREZ.items()}

# === Curses-based Simulation ===
def curses_sim(stdscr):
    global credits, life, location

    # Initialize curses
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    stdscr.bkgd(' ', curses.color_pair(1))
    stdscr.clear()

    for cycle in range(1, CYCLES + 1):
        prices = get_prices()

        # Agent scan
        stdscr.addstr(1, 2, f"[Cycle {cycle}/{CYCLES}] Scanning for Agents... ")
        stdscr.refresh()
        curses.napms(300)
        ev, val = random_event()
        if ev == "trace":
            battle_screen(stdscr, trace_amt=val)
        elif ev == "ambush":
            battle_screen(stdscr, trace_amt=None)

        clamp_life()
        draw_screen(stdscr, cycle, prices)

        # Player actions
        while True:
            ch = stdscr.getkey().upper()
            if ch == 'D':
                handle_download_curses(stdscr, prices)
            elif ch == 'U':
                handle_upload_curses(stdscr, prices)
            elif ch == 'W':
                handle_buy_armory_curses(stdscr)
            elif ch == 'J':
                location = random.choice(NODES)
                draw_screen(stdscr, cycle, prices)
            elif ch == 'N':
                break
            elif ch == 'Q':
                return

            clamp_life()
            draw_screen(stdscr, cycle, prices)
            if life <= 0:
                stdscr.addstr(12, 2, "💀 You have been terminated. Game Over.")
                stdscr.refresh()
                stdscr.getkey()
                return

    # End summary
    stdscr.clear()
    stdscr.addstr(5, 5, "=== SIMULATION COMPLETE ===", curses.A_BOLD)
    stdscr.addstr(7, 5, f"Final Credits: {credits}")
    stdscr.addstr(8, 5, f"Final Life:    {life}")
    stdscr.addstr(10,5, "Press any key to return to menu.")
    stdscr.refresh()
    stdscr.getkey()

def draw_screen(stdscr, cycle, prices):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    # Header
    hdr = f" MATRIX WARS  |  Cycle {cycle}/{CYCLES}  |  Life {life}%  |  Node: {location} "
    stdscr.addstr(0, max(0, (w - len(hdr))//2), hdr, curses.A_REVERSE)

    # STASH
    stdscr.addstr(2, 2, "STASH")
    for i, wname in enumerate(WAREZ, start=1):
        stdscr.addstr(2 + i, 4, f"{wname:<10} {inventory[wname]:>3}")

    # ARMORY
    arm_x = w // 3
    stdscr.addstr(2, arm_x, "ARMORY")
    for i, (wpn, qty) in enumerate(weapons_inv.items(), start=1):
        stdscr.addstr(2 + i, arm_x + 2, f"{wpn[:12]:<12} x{qty}")
    ammo_start = 3 + len(weapons_inv)
    stdscr.addstr(ammo_start, arm_x, "AMMO")
    for j, (am, qty) in enumerate(ammo_inv.items(), start=1):
        stdscr.addstr(ammo_start + j, arm_x + 2, f"{am:<12} x{qty}")

    # MARKET
    mkt_x = 2 * w // 3
    stdscr.addstr(2, mkt_x, "MARKET")
    for i, (wname, price) in enumerate(prices.items(), start=1):
        stdscr.addstr(2 + i, mkt_x + 2, f"{wname:<10} {price:>5} cr")

    # Footer
    stdscr.addstr(h - 3, 2, f"Credits: {credits} cr".ljust(30))
    stdscr.addstr(h - 2, 2, "[D]ownload [U]pload [W]eapons/Ammo [J]ack In [N]ext [Q]uit")
    stdscr.refresh()

# === Curses Input Handlers ===
def handle_download_curses(stdscr, prices):
    global credits
    stdscr.addstr(12, 2, "DOWNLOAD which? ".ljust(60))
    curses.echo()
    choice = stdscr.getstr(12, 18, 15).decode().title()
    curses.noecho()
    if choice not in WAREZ:
        return
    price = prices[choice]
    max_q = credits // price
    if max_q < 1:
        return
    stdscr.addstr(13, 2, f"Qty? (1-{max_q}): ".ljust(60))
    curses.echo()
    q = stdscr.getstr(13, 15, 5).decode()
    curses.noecho()
    try:
        qty = max(1, min(max_q, int(q)))
        credits -= price * qty
        inventory[choice] += qty
    except:
        pass

def handle_upload_curses(stdscr, prices):
    global credits
    stdscr.addstr(12, 2, "UPLOAD which?   ".ljust(60))
    curses.echo()
    choice = stdscr.getstr(12, 18, 15).decode().title()
    curses.noecho()
    if choice not in WAREZ or inventory[choice] == 0:
        return
    max_q = inventory[choice]
    stdscr.addstr(13, 2, f"Qty? (1-{max_q}): ".ljust(60))
    curses.echo()
    q = stdscr.getstr(13, 15, 5).decode()
    curses.noecho()
    try:
        qty = max(1, min(max_q, int(q)))
        credits += prices[choice] * qty
        inventory[choice] -= qty
    except:
        pass

def handle_buy_armory_curses(stdscr):
    global credits
    y0 = 12
    stdscr.addstr(y0, 2, "ARMORY: Weapons & Ammo".ljust(60))
    for i, (wpn, info) in enumerate(WEAPONS.items(), start=1):
        stdscr.addstr(y0 + i, 2, f"{i}. {wpn[:20]:<20} {info['price']}cr")
    offset = len(WEAPONS)
    for j, (am, pr) in enumerate(AMMO_PRICES.items(), start=1):
        stdscr.addstr(y0 + offset + j, 2, f"{offset + j}. {am:<20} {pr}cr")
    stdscr.addstr(y0 + offset + len(AMMO_PRICES) + 1, 2, "Select # or [Q]: ".ljust(60))
    stdscr.refresh()

    curses.echo()
    sel = stdscr.getstr(y0 + offset + len(AMMO_PRICES) + 1, 17, 3).decode()
    curses.noecho()
    if sel.upper() == 'Q':
        return

    try:
        idx = int(sel) - 1
        if idx < len(WEAPONS):
            key = list(WEAPONS.keys())[idx]
            price = WEAPONS[key]['price']
            inv = weapons_inv
        else:
            key = list(AMMO_PRICES.keys())[idx - len(WEAPONS)]
            price = AMMO_PRICES[key]
            inv = ammo_inv
        max_q = credits // price
        if max_q < 1:
            return
        stdscr.addstr(y0 + offset + len(AMMO_PRICES) + 3, 2, f"Qty? (1-{max_q}): ".ljust(60))
        curses.echo()
        q = stdscr.getstr(y0 + offset + len(AMMO_PRICES) + 3, 18, 5).decode()
        curses.noecho()
        qty = max(1, min(max_q, int(q)))
        credits -= price * qty
        inv[key] = inv.get(key, 0) + qty
    except:
        pass

# === Random Events & Battle ===
def random_event():
    if random.random() < 0.25:
        if random.random() < 0.5:
            loss = int(credits * 0.2)
            return ("trace", loss)
        else:
            return ("ambush", None)
    return (None, None)

def battle_screen(stdscr, trace_amt=None):
    global credits, life
    # Full-screen mini-event
    stdscr.clear()
    stdscr.refresh()

    if trace_amt is not None:
        stdscr.addstr(5, 5, f"⚠️  AGENT TRACE! You lost {trace_amt} credits.")
        credits -= trace_amt
        stdscr.addstr(7, 5, "Press any key to continue...")
        stdscr.refresh()
        stdscr.getkey()
        return

    # Ambush: turn-based
    agent_hp = 50
    while True:
        stdscr.clear()
        stdscr.addstr(1, 2, f"💥 AGENT AMBUSH! Life: {life}%  Agent HP: {agent_hp}")
        stdscr.addstr(3, 2, "[F]ight   [R]un")
        stdscr.refresh()
        choice = stdscr.getkey().upper()

        if choice == 'R':
            if random.random() < 0.5:
                loss = int(credits * 0.1)
                credits -= loss
                stdscr.addstr(5, 2, f"Escaped! -{loss}cr")
            else:
                life_loss = 15
                life -= life_loss; clamp_life()
                stdscr.addstr(5, 2, f"Failed to run! -{life_loss}% life")
            stdscr.addstr(7, 2, "Press any key...")
            stdscr.refresh()
            stdscr.getkey()
            return

        # Fight turn
        stdscr.addstr(5, 2, "Choose weapon #:")
        for i, (wpn, qty) in enumerate(weapons_inv.items(), start=1):
            ammo_key = WEAPONS[wpn]['ammo_key']
            stdscr.addstr(6 + i, 2, f"{i}. {wpn} x{qty} ammo:{ammo_inv[ammo_key]}")
        stdscr.refresh()
        curses.echo()
        sel = stdscr.getstr(6 + len(weapons_inv) + 1, 2, 2).decode()
        curses.noecho()

        try:
            wpn = list(weapons_inv.keys())[int(sel) - 1]
            ammo_key = WEAPONS[wpn]['ammo_key']
            if ammo_inv.get(ammo_key, 0) < 1:
                stdscr.addstr(8 + len(weapons_inv), 2, "No ammo!")
                stdscr.refresh(); stdscr.getkey()
                continue
            ammo_inv[ammo_key] -= 1
            if random.random() < WEAPONS[wpn]['acc']:
                dmg = WEAPONS[wpn]['dmg']
                agent_hp -= dmg
                stdscr.addstr(8 + len(weapons_inv), 2, f"You hit! -{dmg} HP")
            else:
                stdscr.addstr(8 + len(weapons_inv), 2, "You miss!")
            stdscr.refresh(); curses.napms(300)
        except:
            continue

        if agent_hp <= 0:
            gain = random.randint(50, 200)
            credits += gain
            stdscr.addstr(10 + len(weapons_inv), 2, f"Agent down! +{gain} cr")
            stdscr.addstr(12 + len(weapons_inv), 2, "Press any key...")
            stdscr.refresh()
            stdscr.getkey()
            return

        # Agent's turn
        stdscr.addstr(10 + len(weapons_inv), 2, "Agent fires...")
        stdscr.refresh(); curses.napms(300)
        if random.random() < 0.5:
            dmg = random.randint(5, 15)
            life -= dmg; clamp_life()
            stdscr.addstr(12 + len(weapons_inv), 2, f"Agent hit you -{dmg}% life")
        else:
            stdscr.addstr(12 + len(weapons_inv), 2, "Agent missed!")
        stdscr.addstr(14 + len(weapons_inv), 2, "Press any key...")
        stdscr.refresh()
        stdscr.getkey()

        if life <= 0:
            return

# === Non-curses Sections ===
def show_story():
    print(r"""
In a world enslaved by the Matrix, you are a rogue operator.
Your mission: infiltrate nodes, trade contraband software,
evade Agents, and amass enough credits to be a power user.
""")

def show_instructions():
    print(r"""
Instructions:
- [D]ownload: Acquire programs (buy low).
- [U]pload: Dispatch programs for credits (sell high).
- [W]eapons: Purchase weapons & ammo.
- [J]ack In: Travel between nodes.
- [N]ext Cycle: Advance time.
- [Q]uit: Abandon simulation.
Life starts at 100%. Reach 0% and you die.
""")

def show_acknowledgments():
    print(r"""
Acknowledgments:
- Yellow Tail Tech
- Boot.dev Python course
- The Sophos Cohort
- John E. Dell (BASIC pioneer)
- All beta testers & supporters
- The Matrix, Neuromancer, Blade Runner
- Cyberpunk & all things high-tech/low-life
""")

# === Main Menu ===
def main_menu():
    while True:
        print(TITLE)
        print("1) Start Simulation")
        print("2) View Story")
        print("3) How to Play")
        print("4) Acknowledgments")
        print("5) Exit")
        choice = input("Select an option: ").strip()
        if choice == '1':
            curses.wrapper(curses_sim)
        elif choice == '2':
            show_story();        input("Press Enter to return...")
        elif choice == '3':
            show_instructions(); input("Press Enter to return...")
        elif choice == '4':
            show_acknowledgments(); input("Press Enter to return...")
        elif choice == '5':
            print("Good luck, Operator.")
            sys.exit(0)
        else:
            print("Invalid selection.")

if __name__ == "__main__":
    main_menu()