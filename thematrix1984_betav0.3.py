#!/usr/bin/env python3
import curses
import random
import sys
import json
import os

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

SAVEFILE = 'matrix_wars_save.json'

# === Game Data & Modifiers ===
CYCLES = 30.0
NODES = {
    'Trainstation': 0.9,
    'Construct': 1.0,
    'Nebuchadnezzar': 1.2,
    'Oracle': 1.1,
    'Chateau': 1.3
}
WAREZ = {
    'RootKit':   (15000, 28000),
    'BlackICE':  (2000,  10000),
    'Datashard': (300,    1000),
    'Trojan':    (1000,   4200),
    'Worm':      (18,     75)
}
WEAPONS = {
    'Beretta 92FS': {'price': 2000, 'acc':0.70, 'dmg':15, 'ammo':'Beretta Ammo', 'mag':18},
    'MP5K SMG':     {'price': 5000, 'acc':0.50, 'dmg':20, 'ammo':'MP5K Ammo',    'mag':40},
    'M4 Carbine':   {'price': 8000, 'acc':0.60, 'dmg':25, 'ammo':'M4 Ammo',       'mag':30}
}
AMMO_PRICES = {
    'Beretta Ammo': 5,
    'MP5K Ammo':    3,
    'M4 Ammo':      7,
    'Health Pack':  50,
    'Armor Kit':    100
}

# === Player State ===
state = {
    'credits': 2000,
    'life': 100,
    'armor': 0,
    'inventory': {w:0 for w in WAREZ},
    'weapons': {},
    'ammo': {k:0 for k in AMMO_PRICES},
    'location': random.choice(list(NODES)),
    'cycle': 1.0,
    'escapes': 0,
    'profit_start': 2000,
    'people_freed': 0,
    'perks': []
}

# === Helpers ===
def clamp(v, lo, hi): return max(lo, min(hi, v))

def save_game():
    with open(SAVEFILE, 'w') as f:
        json.dump(state, f)


def load_game():
    if os.path.exists(SAVEFILE):
        with open(SAVEFILE) as f:
            state.update(json.load(f))
    update_perks()

# === Perk Logic ===
def update_perks():
    p = state['perks']
    # Heavily Armed
    if len(state['weapons']) == len(WEAPONS) and 'Heavily Armed' not in p:
        p.append('Heavily Armed')
    # Edge Runner
    if state['escapes'] >= 2 and 'Edge Runner' not in p:
        p.append('Edge Runner')
    # Data Broker
    if state['credits'] > state['profit_start'] * 1.6 and 'Data Broker' not in p:
        p.append('Data Broker')
    # Elite Operator
    base = ['Heavily Armed', 'Edge Runner', 'Data Broker']
    if all(x in p for x in base) and 'Elite Operator' not in p:
        p.append('Elite Operator')

# === Battle Screen ===
def battle_screen(stdscr, trace_amt=None):
    curses.curs_set(0)
    stdscr.clear()
    stdscr.refresh()
    # Trace event
    if trace_amt is not None:
        state['credits'] -= trace_amt
        stdscr.addstr(5, 5, f"⚠️ AGENT TRACE! -{trace_amt}cr")
        stdscr.addstr(7, 5, "Press any key...")
        stdscr.refresh()
        stdscr.getkey()
        return
    # Ambush
    agent_hp = 50
    while True:
        stdscr.clear()
        stdscr.addstr(1, 2, f"💥 AGENT AMBUSH! Life: {state['life']}%  HP: {agent_hp}")
        stdscr.addstr(3, 2, "[F]ight   [R]un")
        stdscr.refresh()
        choice = stdscr.getkey().upper()
        if choice == 'R':
            run_chance = 0.5 + (0.2 if 'Edge Runner' in state['perks'] else 0)
            if random.random() < run_chance:
                loss = int(state['credits'] * 0.1)
                state['credits'] -= loss
                stdscr.addstr(5, 2, f"Escaped! -{loss}cr")
            else:
                state['life'] -= 15
                state['life'] = clamp(state['life'], 0, 100)
                stdscr.addstr(5, 2, "Failed to run! -15% life")
            stdscr.addstr(7, 2, "Press any key...")
            stdscr.refresh()
            stdscr.getkey()
            return
        # Fight
        stdscr.addstr(5, 2, "Choose weapon #:")
        for i, (wp, qty) in enumerate(state['weapons'].items(), start=1):
            ammo_key = WEAPONS[wp]['ammo']
            stdscr.addstr(6 + i, 2, f"{i}. {wp} x{qty} ammo:{state['ammo'][ammo_key]}")
        stdscr.refresh()
        curses.echo()
        sel = stdscr.getstr(7 + len(state['weapons']), 2, 2).decode()
        curses.noecho()
        try:
            wpn = list(state['weapons'])[int(sel) - 1]
            info = WEAPONS[wpn]
            ammo_key = info['ammo']
            if state['ammo'][ammo_key] < 1:
                stdscr.addstr(9 + len(state['weapons']), 2, "No ammo!")
                stdscr.refresh()
                stdscr.getkey()
                continue
            state['ammo'][ammo_key] -= 1
            # Headshot perk
            if 'Heavily Armed' in state['perks'] and random.random() < 0.2:
                agent_hp = 0
                stdscr.addstr(9 + len(state['weapons']), 2, "DODGE THIS! Critical!")
            elif random.random() < info['acc']:
                agent_hp -= info['dmg']
                stdscr.addstr(9 + len(state['weapons']), 2, f"Hit! -{info['dmg']} HP")
            else:
                stdscr.addstr(9 + len(state['weapons']), 2, "Miss!")
            stdscr.refresh()
            curses.napms(300)
        except (ValueError, IndexError):
            continue
        if agent_hp <= 0:
            gain = random.randint(50, 200)
            state['credits'] += gain
            stdscr.addstr(11 + len(state['weapons']), 2, f"Agent down! +{gain}cr")
            stdscr.addstr(13 + len(state['weapons']), 2, "Press any key...")
            stdscr.refresh()
            stdscr.getkey()
            return
        # Agent attack
        stdscr.addstr(11 + len(state['weapons']), 2, "Agent fires...")
        stdscr.refresh()
        curses.napms(300)
        if random.random() < 0.5:
            dmg = random.randint(5, 15)
            state['life'] -= dmg
            state['life'] = clamp(state['life'], 0, 100)
            stdscr.addstr(13 + len(state['weapons']), 2, f"Agent hit you -{dmg}% life")
        else:
            stdscr.addstr(13 + len(state['weapons']), 2, "Agent missed!")
        stdscr.addstr(15 + len(state['weapons']), 2, "Press any key...")
        stdscr.refresh()
        stdscr.getkey()
        if state['life'] <= 0:
            return

# === Curses-based Simulation ===
def curses_sim(stdscr):
    load_game()
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
    stdscr.bkgd(' ', curses.color_pair(1))
    stdscr.clear()

    while state['cycle'] <= CYCLES and state['life'] > 0:
        prices = {w:int(random.randint(*rng)*NODES[state['location']]) for w,rng in WAREZ.items()}
        ev = random.random()
        if ev < 0.15:
            battle_screen(stdscr, trace_amt=int(state['credits']*0.2))
        elif ev < 0.30:
            battle_screen(stdscr, trace_amt=None)
        elif ev < 0.40:
            field_medic(stdscr)
        elif ev < 0.45:
            free_civilian(stdscr)
        draw_screen(stdscr, prices)

        ch = stdscr.getkey().upper()
        if ch == 'D': handle_download(stdscr, prices)
        elif ch == 'U': handle_upload(stdscr, prices)
        elif ch == 'W': handle_buy_armory(stdscr)
        elif ch == 'J':
            state['location'] = random.choice(list(NODES))
            state['cycle'] += 0.5
        elif ch == 'N':
            state['cycle'] += 1.0
        elif ch == 'Q':
            break
        save_game()

    stdscr.clear()
    stdscr.addstr(5,5, '=== SIMULATION COMPLETE ===', curses.A_BOLD)
    stdscr.addstr(7,5, f"Credits: {state['credits']}")
    stdscr.addstr(8,5, f"Life:    {state['life']}%    Armor: {state['armor']}%")
    stdscr.addstr(9,5, f"Freed:   {state['people_freed']}")
    stdscr.addstr(11,5, 'Press any key to return to menu...')
    stdscr.refresh()
    stdscr.getkey()

# === Drawing HUD ===
def draw_screen(stdscr, prices):
    stdscr.clear()
    h,w = stdscr.getmaxyx()
    hdr = f" MATRIX WARS | Cyc {state['cycle']:.1f}/{CYCLES} | Life {state['life']}% | Armor {state['armor']}% | {state['location']} "
    stdscr.addstr(0,0, hdr.ljust(w), curses.color_pair(2))
    for i,(wz,qty) in enumerate(state['inventory'].items(), start=2):
        stdscr.addstr(i,2, f"{wz[:10]:<10}{qty:>4}")
    ax = w//3
    stdscr.addstr(2,ax, 'WEAPONS')
    for i,(wp,qty) in enumerate(state['weapons'].items(), start=3):
        stdscr.addstr(i, ax+2, f"{wp[:12]:<12} x{qty}")
    ay = 4+len(state['weapons'])
    stdscr.addstr(ay, ax, 'AMMO')
    for j,(am,qty) in enumerate(state['ammo'].items(), start=1):
        stdscr.addstr(ay+j, ax+2, f"{am[:12]:<12} x{qty}")
    mx = 2*w//3
    stdscr.addstr(2, mx, 'MARKET')
    for i,(wz,pr) in enumerate(prices.items(), start=3):
        stdscr.addstr(i, mx+2, f"{wz[:10]:<10}{pr:>6}cr")
    stdscr.addstr(h-3,2, f"Credits: {state['credits']} cr")
    stdscr.addstr(h-2,2, '[D]ownload [U]pload [W]eapons [J]ack In [N]ext [Q]uit')
    stdscr.refresh()

# === Input Handlers ===

def handle_download(stdscr, prices):
    curses.echo()
    stdscr.addstr(12,2,'DOWNLOAD which? '.ljust(60))
    item = stdscr.getstr(12,18,15).decode().title()
    curses.noecho()
    if item not in WAREZ:
        return
    price = prices[item]
    max_qty = state['credits'] // price
    if max_qty < 1:
        return
    curses.echo()
    stdscr.addstr(13,2,f'Qty? (1-{max_qty}): '.ljust(60))
    qty_str = stdscr.getstr(13,18,5).decode()
    curses.noecho()
    try:
        qty = max(1, min(max_qty, int(qty_str)))
        state['credits'] -= price * qty
        state['inventory'][item] += qty
    except ValueError:
        pass


def handle_upload(stdscr, prices):
    curses.echo()
    stdscr.addstr(12,2,'UPLOAD which?   '.ljust(60))
    item = stdscr.getstr(12,18,15).decode().title()
    curses.noecho()
    if item not in WAREZ or state['inventory'][item] == 0:
        return
    max_qty = state['inventory'][item]
    curses.echo()
    stdscr.addstr(13,2,f'Qty? (1-{max_qty}): '.ljust(60))
    qty_str = stdscr.getstr(13,18,5).decode()
    curses.noecho()
    try:
        qty = max(1, min(max_qty, int(qty_str)))
        state['credits'] += prices[item] * qty
        state['inventory'][item] -= qty
    except ValueError:
        pass


def handle_buy_armory(stdscr):
    curses.echo()
    y0 = 12
    stdscr.addstr(y0,2,'ARMORY: Choose #'.ljust(60))
    # List weapons
    for i,(wp,info) in enumerate(WEAPONS.items(), start=1):
        stdscr.addstr(y0+i,2,f'{i}. {wp[:20]:<20}{info["price"]}cr')
    offset = len(WEAPONS)
    # List ammo, health, armor
    for j,(am,pr) in enumerate(AMMO_PRICES.items(), start=1):
        stdscr.addstr(y0+offset+j,2,f'{offset+j}. {am[:20]:<20}{pr}cr')
    stdscr.addstr(y0+offset+len(AMMO_PRICES)+1,2,'# or [Q]: '.ljust(60))
    sel = stdscr.getstr(y0+offset+len(AMMO_PRICES)+1,12,3).decode()
    curses.noecho()
    if sel.upper() == 'Q':
        return
    try:
        idx = int(sel) - 1
        if idx < len(WEAPONS):
            key = list(WEAPONS.keys())[idx]
            price = WEAPONS[key]['price']
            mag = WEAPONS[key]['mag']
            ammo_key = WEAPONS[key]['ammo']
            inv_dict = state['weapons']
        else:
            idx2 = idx - len(WEAPONS)
            key = list(AMMO_PRICES.keys())[idx2]
            price = AMMO_PRICES[key]
            mag = 1
            ammo_key = None
            inv_dict = state['ammo']
        max_qty = state['credits'] // price
        if max_qty < 1:
            return
        curses.echo()
        stdscr.addstr(y0+offset+len(AMMO_PRICES)+3,2,f'Qty? (1-{max_qty}): '.ljust(60))
        qty_str = stdscr.getstr(y0+offset+len(AMMO_PRICES)+3,16,5).decode()
        curses.noecho()
        qty = max(1, min(max_qty, int(qty_str)))
        state['credits'] -= price * qty
        inv_dict[key] = inv_dict.get(key, 0) + qty
        # Bonus ammo for weapon
        if idx < len(WEAPONS) and ammo_key:
            state['ammo'][ammo_key] += mag * qty
    except (ValueError, IndexError):
        pass


def field_medic(stdscr):
    stdscr.clear()
    if state['life'] < 100:
        heal = min(50, 100 - state['life'])
        state['life'] += heal
        msg = f'Blasko heals +{heal}% life'
    else:
        state['armor'] += 20
        state['armor'] = clamp(state['armor'], 0, 100)
        msg = 'Blasko grants +20% armor'
    stdscr.addstr(5,5,msg)
    stdscr.addstr(7,5,'Take care Operator. If you need more armor, visit the armory.')
    stdscr.addstr(9,5,'Press any key...')
    stdscr.refresh()
    stdscr.getkey()


def free_civilian(stdscr):
    state['people_freed'] += 1
    stdscr.clear()
    stdscr.addstr(5,5,f'You freed a civilian! Total freed: {state["people_freed"]}')
    stdscr.addstr(7,5,'Press any key...')
    stdscr.refresh()
    stdscr.getkey()


def main_menu():
    load_game()
    while True:
        print(TITLE)
        print('1) Start Simulation')
        print('2) View Story')
        print('3) How to Play')
        print('4) Acknowledgments')
        print('5) Exit')
        choice = input('Select: ').strip()
        if choice == '1':
            curses.wrapper(curses_sim)
        elif choice == '2':
            show_story(); input('Press Enter to return...')
        elif choice == '3':
            show_instructions(); input('Press Enter to return...')
        elif choice == '4':
            show_acknowledgments(); input('Press Enter to return...')
        elif choice == '5':
            sys.exit(0)
        else:
            print('Invalid selection.')

# === Non-curses Screens ===
def show_story():
    print("""
In a world enslaved by the Matrix, you are a rogue operator.
Your mission: infiltrate nodes, trade digital contraband,
evade Agents, and amass credits to free humanity.
""")

def show_instructions():
    print("""
Instructions:
- [D]ownload: Buy digital programs.
- [U]pload: Sell your stock.
- [W]eapons: Purchase weapons, ammo, health, armor.
- [J]ack In: Travel (0.5 cycle).
- [N]ext Cycle: Advance time.
- [Q]uit: Exit simulation.
Gather perks to become Elite Operator!
""")

def show_acknowledgments():
    print("""
Acknowledgments:
- Yellow Tail Tech
- Boot.dev Python course
- Sophos Cohort
- John E. Dell (BASIC pioneer)
- All beta testers & supporters
- The Matrix universe & cyberpunk legends
""")

if __name__ == '__main__':
    main_menu()
