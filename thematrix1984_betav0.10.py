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
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
1984

by b145k0 2025
"""

SAVEFILE = 'matrix_1984_save.json'

# === Game Data ===
CYCLES = 30.0
NODES = {
    'Trainstation': 0.9,
    'Construct':     1.0,
    'Nebuchadnezzar':1.2,
    'Oracle':        1.1,
    'Chateau':       1.3
}
WAREZ = {
    'RootKit':   (15000, 28000),
    'BlackICE':  (2000,  10000),
    'Datashard': (300,    1000),
    'Trojan':    (1000,   4200),
    'Worm':      (18,     75)
}
WEAPONS = {
    'Beretta 92FS': {'price':2000,'acc':0.70,'dmg':15,'ammo':'Beretta Ammo','mag':18},
    'MP5K SMG':    {'price':5000,'acc':0.50,'dmg':20,'ammo':'MP5K Ammo','mag':40},
    'M4 Carbine':  {'price':8000,'acc':0.60,'dmg':25,'ammo':'M4 Ammo','mag':30}
}
AMMO_PRICES = {'Beretta Ammo':5, 'MP5K Ammo':3, 'M4 Ammo':7}
USEABLES    = {'Health Pack':50, 'Armor Kit':100}
PERK_INFO   = {
    'Heavily Armed':  '20% crit headshot chance',
    'Edge Runner':    '70% escape chance',
    'Data Broker':    '10% trade bonus',
    'Elite Operator': 'Kung Fu crit & bonuses'
}

# === Player State ===
state = {
    'credits':2000,
    'life':   100,
    'armor':  0,
    'inventory':{w:0 for w in WAREZ},
    'weapons':  {},
    'ammo':     {k:0 for k in AMMO_PRICES},
    'useables': {u:0 for u in USEABLES},
    'location': random.choice(list(NODES)),
    'cycle':    1.0,
    'escapes':  0,
    'profit_start':2000,
    'people_freed':0,
    'perks':    []
}

# === Helpers ===
def clamp(v, lo, hi): return max(lo, min(hi, v))

def save_game():
    with open(SAVEFILE,'w') as f:
        json.dump(state,f)

def load_game():
    if os.path.exists(SAVEFILE):
        with open(SAVEFILE) as f:
            state.update(json.load(f))
    return update_perks()

# === Perks Logic ===
def update_perks():
    p = state['perks']
    new = []
    if len(state['weapons']) == len(WEAPONS) and 'Heavily Armed' not in p:
        p.append('Heavily Armed'); new.append('Heavily Armed')
    if state['escapes'] >= 2 and 'Edge Runner' not in p:
        p.append('Edge Runner'); new.append('Edge Runner')
    if state['credits'] > state['profit_start'] * 1.6 and 'Data Broker' not in p:
        p.append('Data Broker'); new.append('Data Broker')
    base = ['Heavily Armed','Edge Runner','Data Broker']
    if all(b in p for b in base) and 'Elite Operator' not in p:
        p.append('Elite Operator'); new.append('Elite Operator')
    return new

# === Draw HUD ===
def draw_screen(stdscr, prices):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    # Header
    hdr = f" MATRIX WARS | Cyc {state['cycle']:.1f}/{CYCLES} | Life {state['life']}% | Armor {state['armor']}% | {state['location']} "
    stdscr.addstr(0,0, hdr.ljust(w))
    # WAREZ Inventory
    stdscr.addstr(2,2, 'WAREZ')
    for i,(k,v) in enumerate(state['inventory'].items(), start=3):
        stdscr.addstr(i,4, f"{k:<12} x{v}")
    # Health/Armor
    hy = 4 + len(state['inventory'])
    stdscr.addstr(hy,2, 'HEALTH / ARMOR')
    stdscr.addstr(hy+1,4, f"HPacks: {state['useables']['Health Pack']}")
    stdscr.addstr(hy+2,4, f"AKits:  {state['useables']['Armor Kit']}")
    # Perks
    py = hy + 4
    stdscr.addstr(py, 2, 'PERKS')
    for idx,pk in enumerate(state['perks'], start=py+1):
        stdscr.addstr(idx,4, f"{pk}: {PERK_INFO[pk]}")
    # Minds Freed
    stdscr.addstr(py+len(state['perks'])+2, 2, f"Minds Freed: {state['people_freed']}")
    # Market
    mx = w//3
    stdscr.addstr(2, mx, 'MARKET')
    for i,(k,pr) in enumerate(prices.items(), start=3):
        stdscr.addstr(i, mx+4, f"{k:<12}{pr}cr")
    # Weapons & Ammo
    wx = 2*w//3
    stdscr.addstr(2, wx, 'WEAPONS')
    for i,(wp,cnt) in enumerate(state['weapons'].items(), start=3):
        ammo_cnt = state['ammo'][WEAPONS[wp]['ammo']]
        stdscr.addstr(i, wx+2, f"{wp:<12} x{cnt} Ammo:{ammo_cnt}")
    # Footer
    stdscr.addstr(h-2, 2, '[D]ownload [U]pload [W]eapons [E]quip [J]ack In [N]ext [Q]uit')
    stdscr.addstr(h-1, 2, f"Credits:{state['credits']} cr")
    stdscr.refresh()

# === Handlers ===
def handle_download(stdscr, prices):
    curses.echo()
    y0 = 5
    stdscr.clear()
    stdscr.addstr(y0, 2, 'Warez Market: Choose item by number')
    idx = 1
    for w in WAREZ:
        p = prices[w]
        inv = state['inventory'][w]
        stdscr.addstr(y0+idx, 4, f"{idx}. {w} - {p} cr (You have: {inv})")
        idx += 1
    stdscr.addstr(y0+idx, 4, 'Q) Quit')
    stdscr.refresh()
    sel = stdscr.getstr(y0+idx+1, 4).decode().strip()
    curses.noecho()
    if sel.upper() == 'Q':
        return
    try:
        choice = int(sel)
    except ValueError:
        return
    if choice < 1 or choice > len(WAREZ):
        return
    key = list(WAREZ)[choice-1]
    p = prices[key]
    maxq = state['credits'] // p if p>0 else 0
    if maxq < 1:
        stdscr.addstr(y0+idx+2, 4, 'Not enough credits. Press any key...')
        stdscr.refresh()
        stdscr.getkey()
        return
    stdscr.addstr(y0+idx+2, 4, f'Qty? (1-{maxq}): ')
    curses.echo()
    q = stdscr.getstr(y0+idx+3, 4).decode().strip()
    curses.noecho()
    try:
        qty = max(1, min(maxq, int(q)))
        state['credits'] -= p * qty
        state['inventory'][key] += qty
        state['cycle'] += 0.25
        stdscr.addstr(y0+idx+4, 4, 'Download complete. Press any key...')
        stdscr.refresh()
        stdscr.getkey()
    except ValueError:
        pass

def handle_upload(stdscr, prices):
    curses.echo(); stdscr.addstr(12,2,'Upload which? ')
    key = stdscr.getstr().decode().strip().lower(); curses.noecho()
    item = next((k for k in WAREZ if k.lower()==key), None)
    if not item or state['inventory'][item]==0: return
    maxq = state['inventory'][item]
    curses.echo(); stdscr.addstr(13,2, f'Qty? (1-{maxq}): ')
    q = stdscr.getstr().decode(); curses.noecho()
    try:
        qty = max(1, min(maxq, int(q)))
        state['credits'] += prices[item]*qty
        state['inventory'][item] -= qty
        state['cycle'] += 0.25
    except ValueError:
        pass
def handle_buy_armory(stdscr):
    curses.echo()
    y0 = 12
    stdscr.clear()
    stdscr.addstr(y0, 2, 'Armory: Choose item by number')
    idx = 1
    for wp, inf in WEAPONS.items():
        stdscr.addstr(y0+idx, 4, f"{idx}. {wp} - {inf['price']} cr")
        idx += 1
    for u, pr in USEABLES.items():
        stdscr.addstr(y0+idx, 4, f"{idx}. {u} - {pr} cr")
        idx += 1
    for a, pr in AMMO_PRICES.items():
        stdscr.addstr(y0+idx, 4, f"{idx}. {a} Ammo Pack - {pr} cr")
        idx += 1
    stdscr.addstr(y0+idx, 4, 'Q) Quit')
    stdscr.refresh()
    sel = stdscr.getstr(y0+idx+1, 4).decode().strip()
    curses.noecho()
    if sel.upper() == 'Q':
        return
    try:
        choice = int(sel)
    except ValueError:
        return
    total_items = len(WEAPONS) + len(USEABLES) + len(AMMO_PRICES)
    if choice < 1 or choice > total_items:
        return
    # Process purchase
    if choice <= len(WEAPONS):
        key = list(WEAPONS)[choice-1]
        info = WEAPONS[key]
        if state['credits'] >= info['price']:
            state['credits'] -= info['price']
            state['weapons'][key] = state['weapons'].get(key, 0) + 1
            state['ammo'][info['ammo']] += info['mag']
    elif choice <= len(WEAPONS) + len(USEABLES):
        idx2 = choice - len(WEAPONS) - 1
        ukey = list(USEABLES)[idx2]
        price = USEABLES[ukey]
        if state['credits'] >= price:
            state['credits'] -= price
            state['useables'][ukey] += 1
    else:
        idx3 = choice - len(WEAPONS) - len(USEABLES) - 1
        akey = list(AMMO_PRICES)[idx3]
        price = AMMO_PRICES[akey]
        if state['credits'] >= price:
            state['credits'] -= price
            state['ammo'][akey] += 5
    state['cycle'] += 0.25
    stdscr.addstr(y0+idx+2, 4, 'Purchase complete. Press any key...')
    stdscr.refresh()
    stdscr.getkey()

def handle_equip(stdscr):
    curses.echo()
    y0 = 5
    stdscr.clear()
    stdscr.addstr(y0, 2, 'Equip: Choose item by number')
    idx = 1
    for u in USEABLES:
        owned = state['useables'][u]
        stdscr.addstr(y0+idx, 4, f"{idx}. {u} (Owned: {owned})")
        idx += 1
    stdscr.addstr(y0+idx, 4, 'Q) Quit')
    stdscr.refresh()
    sel = stdscr.getstr(y0+idx+1, 4).decode().strip()
    curses.noecho()
    if sel.upper() == 'Q':
        return
    try:
        choice = int(sel)
    except ValueError:
        return
    if choice < 1 or choice > len(USEABLES):
        return
    key = list(USEABLES)[choice-1]
    if state['useables'][key] > 0:
        state['useables'][key] -= 1
        if key == 'Health Pack':
            state['life'] = clamp(state['life'] + 15, 0, 100)
        elif key == 'Armor Kit':
            state['armor'] = clamp(state['armor'] + 20, 0, 100)
        state['cycle'] += 0.25
        stdscr.addstr(y0+idx+2, 4, 'Equipped. Press any key...')
        stdscr.refresh()
        stdscr.getkey()

def battle_screen(stdscr, trace_amt=None, smith=False):
    curses.curs_set(0)
    stdscr.clear()
    stdscr.refresh()
    if trace_amt is not None:
        state['credits'] -= trace_amt
        stdscr.addstr(5,5, f"⚠️ AGENT TRACE! -{trace_amt}cr")
        stdscr.addstr(7,5, 'Press any key...')
        stdscr.refresh()
        stdscr.getkey()
        return
    hp = 100 if smith else 50
    dodge = 0.15 if smith else 0.0
    while True:
        stdscr.clear()
        label = 'SMITH' if smith else 'AGENT'
        stdscr.addstr(1,2, f"{label} AMBUSH! Life:{state['life']}% HP:{hp}")
        stdscr.addstr(3,2, "[F]ight [R]un")
        stdscr.refresh()
        ch = stdscr.getkey().upper()
        if ch == 'R':
            state['escapes'] += 1
            stdscr.addstr(5,2,'Escaped safely!')
            stdscr.addstr(7,2,'Press any key...')
            stdscr.refresh()
            stdscr.getkey()
            return
        opts = list(state['weapons'].keys())
        if 'Elite Operator' in state['perks']:
            opts.append('Kung Fu')
        for i,name in enumerate(opts, start=1):
            stdscr.addstr(5+i,2, f"{i}. {name}")
        stdscr.refresh()
        curses.echo()
        sel = stdscr.getstr(6+len(opts),2,2).decode()
        curses.noecho()
        try:
            choice = opts[int(sel)-1]
        except:
            continue
        if choice == 'Kung Fu':
            dmg = 20
            hp -= dmg
            stdscr.addstr(7+len(opts),2, f"Kung Fu! -{dmg} HP")
        else:
            info=WEAPONS[choice]
            ak=info['ammo']
            if state['ammo'][ak] < 1:
                stdscr.addstr(7+len(opts),2,'No ammo!')
                stdscr.refresh()
                stdscr.getkey()
                continue
            state['ammo'][ak] -= 1
            if random.random() < info['acc']:
                hp -= info['dmg']
                stdscr.addstr(7+len(opts),2, f"Hit! -{info['dmg']} HP")
            else:
                stdscr.addstr(7+len(opts),2, 'Miss!')
        stdscr.refresh(); curses.napms(300)
        if hp <= 0:
            stdscr.addstr(9+len(opts),2,'Opponent down!')
            drop = random.choice(list(WAREZ.keys()) + list(WEAPONS.keys()) + list(AMMO_PRICES.keys()))
            if drop in WAREZ:
                state['inventory'][drop] += 1
            elif drop in WEAPONS:
                state['weapons'][drop] = state['weapons'].get(drop,0) + 1
            else:
                state['ammo'][drop] = state['ammo'].get(drop,0) + 1
            gain = random.randint(50,200)
            state['credits'] += gain
            stdscr.addstr(10+len(opts),2, f"Found {drop}, +{gain}cr")
            stdscr.addstr(12+len(opts),2,'Press any key...')
            stdscr.refresh(); stdscr.getkey()
            return
        stdscr.addstr(9+len(opts),2,'Opponent fires...')
        stdscr.refresh(); curses.napms(300)
        if random.random() > dodge:
            dmg=random.randint(5,15)
            state['life'] -= dmg
            clamp(state['life'],0,100)
            stdscr.addstr(11+len(opts),2, f"Hit! -{dmg}% life")
        else:
            stdscr.addstr(11+len(opts),2,'Dodged!')
        stdscr.addstr(13+len(opts),2,'Press any key...')
        stdscr.refresh(); stdscr.getkey()
        if state['life'] <= 0:
            return

# === Field Medic ===
def field_medic(stdscr):
    if random.random() < 0.01:
        heal=random.randint(10,15)
        if random.random() < 0.05:
            heal=25
        state['life']=clamp(state['life']+heal,0,100)
        update_perks()
        stdscr.clear(); stdscr.addstr(5,5,f'Blasko heals +{heal}% life')
        stdscr.addstr(7,5,'Press any key...'); stdscr.refresh(); stdscr.getkey()

# === Free Civilian ===
def free_civilian(stdscr):
    curse=random.randint(1,10)
    curses.echo()
    y0 = 5
    stdscr.clear()
    stdscr.addstr(y0, 2, 'Pick a number 1-10: ')
    stdscr.refresh()
    try:
        guess = int(stdscr.getstr(y0, 24).decode().strip())
    except ValueError:
        curses.noecho()
        return
    curses.noecho()
    if abs(guess - curse) <= 2:
        state['people_freed'] += 1
        stdscr.addstr(y0+2, 2, 'Red pill! Mind freed.')
    else:
        stdscr.addstr(y0+2, 2, 'Blue pill! Becomes Agent.')
        stdscr.refresh()
        curses.napms(500)
        battle_screen(stdscr, trace_amt=None, smith=True)
    stdscr.addstr(y0+4, 2, 'Press any key...')
    stdscr.refresh()
    stdscr.getkey()

# === Simulation ===
def curses_sim(stdscr):
    load_game(); curses.curs_set(0); curses.start_color(); curses.init_pair(1,curses.COLOR_GREEN,curses.COLOR_BLACK)
    stdscr.bkgd(' ',curses.color_pair(1)); stdscr.clear()
    while state['cycle']<=CYCLES and state['life']>0:
        prices={w:int(random.randint(*rng)*NODES[state['location']]) for w,rng in WAREZ.items()}
        ev=random.random()
        if ev<0.30: battle_screen(stdscr)
        elif ev<0.31: battle_screen(stdscr, smith=True)
        elif ev<0.32: field_medic(stdscr)
        elif ev<0.33: free_civilian(stdscr)
        draw_screen(stdscr,prices)
        ch=stdscr.getkey().upper()
        if ch=='D': handle_download(stdscr,prices)
        elif ch=='U': handle_upload(stdscr,prices)
        elif ch=='W': handle_buy_armory(stdscr)
        elif ch=='E': handle_equip(stdscr)
        elif ch=='J': state['location']=random.choice(list(NODES)); state['cycle']+=0.5
        elif ch=='N': state['cycle']+=1.0
        elif ch=='Q': break
        save_game()
    stdscr.clear(); stdscr.addstr(5,5,'=== SIMULATION COMPLETE ===',curses.A_BOLD)
    stdscr.addstr(7,5,f"Credits:{state['credits']}")
    stdscr.addstr(8,5,f"Life:{state['life']}% Armor:{state['armor']}% Freed:{state['people_freed']}")
    stdscr.addstr(10,5,'Press any key...'); stdscr.refresh(); stdscr.getkey()

# === Menus ===
def show_story():
    print("""
In a world enslaved by the Matrix, you are a rogue operator.
Your mission: infiltrate nodes, trade digital contraband,
evade Agents, and amass credits to free humanity.
""")

def show_instructions():
    print("""
Instructions:
- [D]ownload: buy programs.
- [U]pload: sell contraband.
- [W]eapons: purchase arms.
- [J]ack In: travel (0.5 cycle).
- [N]ext: advance cycle.
- [Q]uit: return to menu.
""")

def show_acknowledgments():
    print("""
Acknowledgments:
- Yellow Tail Tech
- Boot.dev Python
- Sophos Cohort
- John E. Dell
- Beta Testers
- The Matrix.
""")

def game_start_menu():
    load_game()
    while True:
        print("\n=== MATRIX WARS START ===")
        print("1) New Game")
        print("2) Continue")
        if state['cycle']>CYCLES and 'Elite Operator' not in state['perks'] and state['life']>0:
            print("3) New Game+ (keep your inventory)")
            print("4) Back to Main Menu")
            choice=input('Select: ').strip()
            if choice=='1': reset_full(); curses.wrapper(curses_sim); return
            elif choice=='2': curses.wrapper(curses_sim); return
            elif choice=='3': state['cycle']=1.0; state['profit_start']=state['credits']; save_game(); curses.wrapper(curses_sim); return
            elif choice=='4': return
        else:
            print("3) Back to Main Menu")
            choice=input('Select: ').strip()
            if choice=='1': reset_full(); curses.wrapper(curses_sim); return
            elif choice=='2': curses.wrapper(curses_sim); return
            elif choice=='3': return


def reset_full():
    if os.path.exists(SAVEFILE): os.remove(SAVEFILE)
    state.update({
        'credits':2000,'life':100,'armor':0,
        'inventory':{w:0 for w in WAREZ},
        'weapons':{},'ammo':{k:0 for k in AMMO_PRICES},
        'location':random.choice(list(NODES)),'cycle':1.0,
        'escapes':0,'profit_start':2000,'people_freed':0,'perks':[]
    })
    save_game()


def main_menu():
    while True:
        print(TITLE)
        print('1) Enter the Matrix')
        print('2) View Story')
        print('3) How to Play')
        print('4) Acknowledgments')
        print('5) Exit')
        c=input('Select: ')
        if c=='1': game_start_menu()
        elif c=='2': show_story(); input('\nPress Enter...')
        elif c=='3': show_instructions(); input('\nPress Enter...')
        elif c=='4': show_acknowledgments(); input('\nPress Enter...')
        elif c=='5': sys.exit(0)
        else: print('Invalid selection.')

if __name__=='__main__':
    main_menu()