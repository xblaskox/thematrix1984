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

# === Game Data & Modifiers ===
CYCLES = 30.0
NODES = {
    "The Trainstation":     0.9,
    "The Construct":        1.0,
    "Nebuchadnezzar":       1.2,
    "Oracle's Apartment":   1.1,
    "Merovingian's Chateau":1.3
}
WAREZ = {
    "RootKit":   (15000, 28000),
    "BlackICE":  (2000,  10000),
    "Datashard": (300,   1000),
    "Trojan":    (1000,  4200),
    "Worm":      (18,    75)
}
WEAPONS = {
    "Beretta 92FS":   {"price":2000, "acc":0.70, "dmg":15, "ammo":"Beretta Ammo", "mag":18},
    "HK MP5K SMG":    {"price":5000, "acc":0.50, "dmg":20, "ammo":"MP5K Ammo",    "mag":40},
    "M4 Carbine":     {"price":8000, "acc":0.60, "dmg":25, "ammo":"M4 Ammo",       "mag":30}
}
AMMO_PRICES = {
    "Beretta Ammo": 5,
    "MP5K Ammo":    3,
    "M4 Ammo":      7
}

# === Player State ===
credits     = 2000
life        = 100
inventory   = {w:0 for w in WAREZ}
weapons_inv = {}
ammo_inv    = {k:0 for k in AMMO_PRICES}
location    = random.choice(list(NODES))

# === Helpers ===
def clamp_life():
    global life
    life = max(0, min(100, life))

def get_prices():
    mod = NODES[location]
    return {w:int(random.randint(*rng)*mod) for w,rng in WAREZ.items()}

# === Curses Simulation ===
def curses_sim(stdscr):
    global credits, life, location

    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # normal text
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)  # header
    stdscr.bkgd(' ', curses.color_pair(1))
    stdscr.clear()

    cycle = 1.0
    while cycle <= CYCLES and life>0:
        prices = get_prices()

        # Agent scan
        stdscr.addstr(1,2, f"[Cycle {cycle:.1f}/{CYCLES}] Scanning for Agents... ")
        stdscr.refresh(); curses.napms(300)
        ev,val = random_event()
        if ev=="trace":
            battle_screen(stdscr, trace_amt=val)
        elif ev=="ambush":
            battle_screen(stdscr, trace_amt=None)

        clamp_life()
        draw_screen(stdscr, cycle, prices)

        # Player actions (cost cycle)
        ch = stdscr.getkey().upper()
        if ch=='D':
            handle_download(stdscr, prices)
        elif ch=='U':
            handle_upload(stdscr, prices)
        elif ch=='W':
            handle_buy_armory(stdscr)
        elif ch=='J':
            # Jack In costs 0.5 cycle
            location = random.choice(list(NODES))
            cycle += 0.5
        elif ch=='N':
            cycle += 1.0
        elif ch=='Q':
            return
        # redraw HUD
        clamp_life()
        draw_screen(stdscr, cycle, prices)

    # End summary
    stdscr.clear()
    stdscr.addstr(5,5, "=== SIMULATION COMPLETE ===", curses.A_BOLD)
    stdscr.addstr(7,5, f"Final Credits: {credits}")
    stdscr.addstr(8,5, f"Final Life:    {life}%")
    stdscr.addstr(10,5, "Press any key to return to menu.")
    stdscr.refresh()
    stdscr.getkey()

def draw_screen(stdscr, cycle, prices):
    stdscr.clear()
    h,w = stdscr.getmaxyx()
    # Header
    hdr = f" MATRIX WARS  |  Cyc {cycle:.1f}/{CYCLES}  |  Life {life}%  |  {location} "
    stdscr.addstr(0,0, hdr.ljust(w), curses.color_pair(2))
    # STASH
    stdscr.addstr(2,2, "STASH")
    for i,wname in enumerate(WAREZ, start=1):
        stdscr.addstr(2+i,4, f"{wname:<10}{inventory[wname]:>4}")
    # ARMORY
    ax = w//3
    stdscr.addstr(2,ax,"ARMORY")
    for i,(wpn,qty) in enumerate(weapons_inv.items(),start=1):
        stdscr.addstr(2+i, ax+2, f"{wpn[:12]:<12} x{qty}")
    # AMMO
    ay = 3+len(weapons_inv)
    stdscr.addstr(ay, ax, "AMMO")
    for j,(am,qty) in enumerate(ammo_inv.items(),start=1):
        stdscr.addstr(ay+j, ax+2, f"{am[:12]:<12} x{qty}")
    # MARKET
    mx = 2*w//3
    stdscr.addstr(2,mx,"MARKET")
    for i,(wname,price) in enumerate(prices.items(),start=1):
        stdscr.addstr(2+i, mx+2, f"{wname:<10}{price:>6}cr")
    # Footer
    stdscr.addstr(h-3,2,f"Credits: {credits} cr".ljust(30))
    stdscr.addstr(h-2,2,"[D]ownload [U]pload [W]eapons [J]ack In [N]ext [Q]uit")
    stdscr.refresh()

# === Input Handlers ===
def handle_download(stdscr, prices):
    global credits
    stdscr.addstr(12,2,"DOWNLOAD what? ".ljust(60))
    curses.echo()
    c = stdscr.getstr(12,17,15).decode().title()
    curses.noecho()
    if c not in WAREZ: return
    p = prices[c]; maxq=credits//p
    if maxq<1: return
    stdscr.addstr(13,2,f"Qty? (1-{maxq}): ".ljust(60)); curses.echo()
    q=stdscr.getstr(13,16,5).decode(); curses.noecho()
    try:
        qty = max(1,min(maxq,int(q)))
        credits -= p*qty
        inventory[c] += qty
    except: pass

def handle_upload(stdscr, prices):
    global credits
    stdscr.addstr(12,2,"UPLOAD what?   ".ljust(60))
    curses.echo()
    c = stdscr.getstr(12,17,15).decode().title()
    curses.noecho()
    if c not in WAREZ or inventory[c]==0: return
    maxq=inventory[c]
    stdscr.addstr(13,2,f"Qty? (1-{maxq}): ".ljust(60)); curses.echo()
    q=stdscr.getstr(13,16,5).decode(); curses.noecho()
    try:
        qty = max(1,min(maxq,int(q)))
        credits += prices[c]*qty
        inventory[c] -= qty
    except: pass

def handle_buy_armory(stdscr):
    global credits
    y0=12
    stdscr.addstr(y0,2,"ARMORY: Choose #".ljust(60))
    # list weapons
    for i,(wpn,info) in enumerate(WEAPONS.items(),start=1):
        stdscr.addstr(y0+i,2,f"{i}. {wpn[:20]:<20}{info['price']}cr")
    off=len(WEAPONS)
    # list ammo
    for j,(am,pr) in enumerate(AMMO_PRICES.items(),start=1):
        stdscr.addstr(y0+off+j,2,f"{off+j}. {am[:20]:<20}{pr}cr")
    stdscr.addstr(y0+off+len(AMMO_PRICES)+1,2,"# or [Q]: ".ljust(60))
    stdscr.refresh()
    curses.echo()
    sel=stdscr.getstr(y0+off+len(AMMO_PRICES)+1,12,3).decode()
    curses.noecho()
    if sel.upper()=='Q': return
    try:
        idx=int(sel)-1
        if idx<len(WEAPONS):
            key=list(WEAPONS)[idx]
            pr=WEAPONS[key]['price']; ammo_key=WEAPONS[key]['ammo']; mag=WEAPONS[key]['mag']
            inv=weapons_inv
        else:
            key=list(AMMO_PRICES)[idx-len(WEAPONS)]
            pr=AMMO_PRICES[key]; ammo_key=key; mag=1
            inv=ammo_inv
        maxq=credits//pr
        if maxq<1: return
        stdscr.addstr(y0+off+len(AMMO_PRICES)+3,2,f"Qty? (1-{maxq}): ".ljust(60))
        curses.echo()
        q=stdscr.getstr(y0+off+len(AMMO_PRICES)+3,16,5).decode()
        curses.noecho()
        qty=max(1,min(maxq,int(q)))
        credits -= pr*qty
        inv[key]=inv.get(key,0)+qty
        # magazine bonus on weapon purchase
        if idx<len(WEAPONS):
            ammo_inv[ammo_key] += mag*qty
    except:
        pass

# === Events & Battle ===
def random_event():
    if random.random()<0.25:
        if random.random()<0.5:
            loss=int(credits*0.2)
            return("trace",loss)
        else:
            return("ambush",None)
    return(None,None)

def battle_screen(stdscr, trace_amt=None):
    global credits, life
    stdscr.clear(); stdscr.refresh()
    if trace_amt is not None:
        credits -= trace_amt
        stdscr.addstr(5,5,f"⚠️  AGENT TRACE! -{trace_amt}cr")
        stdscr.addstr(7,5,"Press any key..."); stdscr.refresh(); stdscr.getkey(); return

    agent_hp=50
    while True:
        stdscr.clear()
        stdscr.addstr(1,2,f"💥 AGENT AMBUSH! Your Life: {life}%  Agent HP: {agent_hp}")
        stdscr.addstr(3,2,"[F]ight   [R]un"); stdscr.refresh()
        ch=stdscr.getkey().upper()
        if ch=='R':
            if random.random()<0.5:
                loss=int(credits*0.1); credits-=loss
                stdscr.addstr(5,2,f"Escaped! -{loss}cr")
            else:
                life-=15; clamp_life()
                stdscr.addstr(5,2,"Failed to run! -15% life")
            stdscr.addstr(7,2,"Press any key..."); stdscr.refresh(); stdscr.getkey(); return

        # fight turn
        stdscr.addstr(5,2,"Choose weapon #:")
        for i,(wp,qty) in enumerate(weapons_inv.items(),start=1):
            stdscr.addstr(6+i,2,f"{i}. {wp} x{qty} ammo:{ammo_inv[WEAPONS[wp]['ammo']]}")
        stdscr.refresh(); curses.echo()
        sel=stdscr.getstr(7+len(weapons_inv),2,2).decode(); curses.noecho()
        try:
            wpn=list(weapons_inv)[int(sel)-1]
            ak=WEAPONS[wpn]['ammo']; acc=WEAPONS[wpn]['acc']; dmg=WEAPONS[wpn]['dmg']
            if ammo_inv[ak]<1:
                stdscr.addstr(9+len(weapons_inv),2,"No ammo!"); stdscr.refresh(); stdscr.getkey(); continue
            ammo_inv[ak]-=1
            if random.random()<acc:
                agent_hp-=dmg
                stdscr.addstr(9+len(weapons_inv),2,f"Hit! -{dmg} HP")
            else:
                stdscr.addstr(9+len(weapons_inv),2,"Miss!")
            stdscr.refresh(); curses.napms(300)
        except:
            continue

        if agent_hp<=0:
            gain=random.randint(50,200); credits+=gain
            stdscr.addstr(11+len(weapons_inv),2,f"Agent down! +{gain}cr")
            stdscr.addstr(13+len(weapons_inv),2,"Press any key..."); stdscr.refresh(); stdscr.getkey(); return

        # agent fires
        stdscr.addstr(11+len(weapons_inv),2,"Agent firing...")
        stdscr.refresh(); curses.napms(300)
        if random.random()<0.5:
            dmg=random.randint(5,15); life-=dmg; clamp_life()
            stdscr.addstr(13+len(weapons_inv),2,f"Hit! -{dmg}% life")
        else:
            stdscr.addstr(13+len(weapons_inv),2,"Miss!")
        stdscr.addstr(15+len(weapons_inv),2,"Press any key..."); stdscr.refresh(); stdscr.getkey()
        if life<=0: return

# === Menu Screens ===
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
- [J]ack In: Travel (costs 0.5 cycle).
- [N]ext Cycle: Advance 1 cycle.
- [Q]uit: Abandon sim.
Life starts at 100%. Hit 0% and you die.
""")

def show_acknowledgments():
    print(r"""
Acknowledgments:
- Yellow Tail Tech
- Boot.dev Python
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
        if choice=='1':
            curses.wrapper(curses_sim)
        elif choice=='2':
            show_story();        input("Press Enter to return...")
        elif choice=='3':
            show_instructions(); input("Press Enter to return...")
        elif choice=='4':
            show_acknowledgments(); input("Press Enter to return...")
        elif choice=='5':
            print("Good luck, Operator."); sys.exit(0)
        else:
            print("Invalid selection.")

if __name__=="__main__":
    main_menu()