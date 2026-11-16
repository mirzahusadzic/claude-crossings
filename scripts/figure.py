"""The README's figure, Crossings across a cut, drawn by hand in light and dark from one source.

    python3 scripts/figure.py      writes docs/images/crossings-light.svg and docs/images/crossings-dark.svg

The type is set as frame-loop's figure sets it: 25 bold for the two sides and the layers, 22 for a name, 19 for
every other line that is read, and 15 for what is only drawn. At the README's 830 pixels no word is smaller than
13. The grains are placed by a seeded draw, so both themes, and every run, lay them in the same places.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

W, H = 1200, 1092

PALETTES = {
    "light": {
        "bg": "#ffffff",
        "text": "#1f2328",
        "dim": "#59636e",
        "warm": "#7f4c00",
        "cool": "#1a63c4",
        "ink": "#1b1206",
        "rail": "#c4cbd2",
        "blue": "#2b7de0",
        "blue2": "#1f6fd0",
        "amber": "#f0960a",
        "amber2": "#dd8e0b",
        "band": "#eef5fe",
        "band2": "#e3eefc",
        "wave": "#2b7de0",
        "you": "#f0a43a",
        "claude": "#6aa5ee",
        "glyph": "#8c959f",
        "sum": "#d8dee4",
        "sumline": "#8c959f",
        "mesh": "#59636e",
        "door": "#eef5fe",
        "doorline": "#1f6fd0",
        "home0": "#f5f3ef",
        "home1": "#f2ebde",
        "home2": "#ecdcc0",
        "homeline": "#8c959f",
        "layer": "#dcc9a6",
        "earth": "#5a4525",
        "gyou": "#e59a35",
        "gclaude": "#5b93d8",
        "card": "#ffffff",
        "cardline": "#59636e",
        "post": "#8c959f",
        "lattice": "#a7b0ba",
        "halo": "#f3ede2",
        "deep": "#ece0c9",
        "rise0": "#b77005",
        "rise1": "#dd8e0b",
        "feed": "#dd8e0b",
    },
    "dark": {
        "bg": "#0d1117",
        "text": "#e6edf3",
        "dim": "#9aa4ae",
        "warm": "#fbbc5d",
        "cool": "#7fb6f5",
        "ink": "#1b1206",
        "rail": "#30363d",
        "blue": "#7fb6f5",
        "blue2": "#5aa1f2",
        "amber": "#f99d12",
        "amber2": "#fbbc5d",
        "band": "#16233b",
        "band2": "#132036",
        "wave": "#7fb6f5",
        "you": "#e8962a",
        "claude": "#3f7fcf",
        "glyph": "#6e7681",
        "sum": "#2d333b",
        "sumline": "#6e7681",
        "mesh": "#9aa4ae",
        "door": "#16233b",
        "doorline": "#5aa1f2",
        "home0": "#16181c",
        "home1": "#1d1a15",
        "home2": "#2c2112",
        "homeline": "#6e7681",
        "layer": "#4d3a22",
        "earth": "#d6c4a4",
        "gyou": "#d98f2a",
        "gclaude": "#4a86d0",
        "card": "#161b22",
        "cardline": "#8b949e",
        "post": "#6e7681",
        "lattice": "#4a525c",
        "halo": "#1c1915",
        "deep": "#2a2014",
        "rise0": "#b77005",
        "rise1": "#fbbc5d",
        "feed": "#fbbc5d",
    },
}

DESC = (
    "A cross-section. Claude stands on the left and you on the right. At the top the session, a current of "
    "messages, yours and Claude's, cut twice: after each cut a summary takes the conversation's place, the later "
    "one retelling the one before, and a small frame crosses beside it. Below, what is said goes down through a "
    "mesh that lets words alone pass, into the home: plain files, with no model and no network. There the archive "
    "is laid down as sediment, every word under its id, never retold; labels stand in it as stakes, each one "
    "sentence of what you tell and ask, never of how you seem, resting on the messages it is about, and one "
    "resting on two others as a stack; a gap where Crossings was off holds nothing, and a struck message is gone. "
    "Beneath lies the index, a scaffold made from the files. Between the session and the home stands the door, "
    "the tools the session reaches through. From the labels and a few of your own words a frame rises and "
    "crosses each cut."
)


def svg(theme: str) -> str:
    p = PALETTES[theme]
    rnd = random.Random(7)  # the same grains in both themes
    out: list[str] = []
    add = out.append

    add(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W * 3 // 2}" height="{H * 3 // 2}" '
        'role="img" aria-labelledby="t d">'
    )
    add('  <title id="t">Crossings, across a cut: what is kept, and what crosses</title>')
    add(f'  <desc id="d">{DESC}</desc>')

    # --- definitions ---------------------------------------------------------------------------
    add("  <defs>")
    add(
        '    <pattern id="meshgrey" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<path d="M0 0H8M0 0V8" stroke="{p["mesh"]}" stroke-width="1" fill="none"/></pattern>'
    )
    add(
        '    <pattern id="meshsmall" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<path d="M0 0H5M0 0V5" stroke="{p["sumline"]}" stroke-width="0.8" fill="none"/></pattern>'
    )
    add(
        f'    <linearGradient id="rise" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{p["rise0"]}"/>'
        f'<stop offset="1" stop-color="{p["rise1"]}"/></linearGradient>'
    )
    add(
        f'    <linearGradient id="current" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{p["band2"]}"/>'
        f'<stop offset="1" stop-color="{p["band"]}"/></linearGradient>'
    )
    add(
        '    <linearGradient id="earth" gradientUnits="userSpaceOnUse" x1="0" y1="456" x2="0" y2="1016">'
        f'<stop offset="0" stop-color="{p["home0"]}"/><stop offset=".3" stop-color="{p["home0"]}"/>'
        f'<stop offset=".7" stop-color="{p["home1"]}"/><stop offset="1" stop-color="{p["home2"]}"/></linearGradient>'
    )
    add('    <clipPath id="session"><rect x="150" y="76" width="900" height="200" rx="14"/></clipPath>')
    add('    <clipPath id="home"><rect x="150" y="456" width="900" height="560" rx="14"/></clipPath>')
    add("  </defs>")
    add("  <style>")
    add(
        '    text { font-family: "Latin Modern Roman", "CMU Serif", "Computer Modern", "Times New Roman", Georgia, '
        f"serif; font-size: 22px; fill: {p['text']}; }}"
    )
    add(
        "    .b { font-weight: 700; } .i { font-style: italic; } .s { font-size: 19px; } "
        ".h { font-size: 25px; font-weight: 700; }"
    )
    add(
        f"    .dim {{ fill: {p['dim']}; }} .warm {{ fill: {p['warm']}; }} .cool {{ fill: {p['cool']}; }} "
        f".earth {{ fill: {p['earth']}; }}"
    )
    add('    .mono { font-family: "SF Mono", Menlo, Consolas, monospace; }')
    add(f"    .halo {{ paint-order: stroke; stroke: {p['halo']}; stroke-width: 6px; stroke-linejoin: round; }}")
    add(f"    .deep {{ paint-order: stroke; stroke: {p['deep']}; stroke-width: 7px; stroke-linejoin: round; }}")
    add("  </style>")
    add(f'  <rect width="{W}" height="{H}" fill="{p["bg"]}"/>')

    # --- the two who stand at the sides ----------------------------------------------------------
    add("\n  <!-- the two who stand at the sides: their words go into the session from either side -->")
    add('  <text x="78" y="52" text-anchor="middle" class="h">Claude</text>')
    add('  <text x="1122" y="52" text-anchor="middle" class="h">You</text>')
    add(f'  <path d="M78 66 V1020 M1122 66 V1020" stroke="{p["rail"]}" stroke-width="2"/>')
    add(
        f'  <path d="M84 168 H140" stroke="{p["blue"]}" stroke-width="3"/><path d="M150 168 l-14 -8 v16 z" '
        f'fill="{p["blue"]}"/>'
    )
    add(
        f'  <path d="M1116 168 H1060" stroke="{p["amber"]}" stroke-width="3"/>'
        f'<path d="M1050 168 l14 -8 v16 z" fill="{p["amber"]}"/>'
    )

    # --- the session: a current, cut ------------------------------------------------------------
    add("\n  <!-- the session: a current of messages, yours and Claude's, that the harness cuts; after a cut a")
    add("       summary stands in the conversation's place, the later one retelling the one before, and the")
    add("       frame crosses beside it -->")
    add(
        f'  <rect x="150" y="76" width="900" height="200" rx="14" fill="url(#current)" stroke="{p["blue2"]}" '
        'stroke-width="1.6"/>'
    )
    add('  <g clip-path="url(#session)">')
    for y in (126, 152, 178, 204, 230, 256):
        add(
            f'    <path d="M150 {y} q75 -3 150 0 t150 0 t150 0 t150 0 t150 0 t150 0" stroke="{p["wave"]}" '
            'stroke-width="1" opacity=".13" fill="none"/>'
        )
    add("  </g>")
    add(
        '  <text x="172" y="112" class="h cool">The session<tspan dx="12" class="s i" '
        'font-weight="400">current</tspan></text>'
    )

    rows = (142, 166, 190, 214)

    def stream(x0: float, x1: float, row: float, seq: list) -> None:
        """Messages along one row: yours (y), Claude's (c), reasoning (r) and tool traffic (t), clipped at x1."""
        x = x0
        for kind, w in seq:
            if x >= x1 - 6:
                break
            if kind == "r":
                add(f'  <text x="{x + 1:.1f}" y="{row + 5:.1f}" style="font-size:15px; fill:{p["glyph"]}">∴</text>')
                x += 18
                continue
            if kind == "t":
                add(
                    f'  <text x="{x:.1f}" y="{row + 5:.1f}" class="mono" style="font-size:15px; '
                    f'fill:{p["glyph"]}">{{ }}</text>'
                )
                x += 32
                continue
            w = min(w, x1 - x)
            colour = p["you"] if kind == "y" else p["claude"]
            add(f'  <rect x="{x:.1f}" y="{row - 6:.1f}" width="{w:.1f}" height="12" rx="6" fill="{colour}"/>')
            x += w + 6

    first = [
        [("y", 44), ("c", 118), ("r", 0), ("c", 70), ("y", 26)],
        [("y", 70), ("t", 0), ("c", 96), ("y", 34), ("c", 80)],
        [("c", 52), ("r", 0), ("t", 0), ("c", 110), ("y", 58), ("c", 40)],
        [("y", 30), ("c", 142), ("y", 64), ("t", 0), ("c", 60)],
    ]
    for row, seq in zip(rows, first):
        stream(172, 468, row, seq)

    def summary(x: float, y: float, w: float, h: float, retold: float = 0) -> None:
        add(
            f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{p["sum"]}" stroke="{p["sumline"]}" '
            'stroke-width="1"/>'
        )
        lx = x + 6
        if retold:
            add(
                f'  <rect x="{x + 5}" y="{y + 6}" width="{retold}" height="{h - 12}" rx="4" fill="url(#meshsmall)" '
                f'stroke="{p["sumline"]}" stroke-width=".8"/>'
            )
            lx = x + retold + 11
        for n, ly in enumerate(range(int(y) + 12, int(y + h) - 6, 11)):
            short = (n * 7) % 13
            add(
                f'  <path d="M{lx} {ly} H{x + w - 7 - short}" stroke="{p["sumline"]}" stroke-width="2" '
                'stroke-linecap="round"/>'
            )

    def frame_card(x: float, y: float) -> None:
        add(f'  <rect x="{x}" y="{y}" width="28" height="68" rx="5" fill="{p["amber"]}"/>')
        for n, ly in enumerate((y + 13, y + 26, y + 39, y + 52)):
            add(
                f'  <path d="M{x + 6} {ly} H{x + 22 - (n % 2) * 6}" stroke="{p["ink"]}" stroke-opacity=".5" '
                'stroke-width="2" stroke-linecap="round"/>'
            )

    # after cut 1
    summary(504, 132, 66, 92)
    frame_card(578, 144)
    second = [
        [("c", 64), ("y", 30), ("c", 90)],
        [("y", 52), ("r", 0), ("c", 120)],
        [("c", 44), ("t", 0), ("y", 40), ("c", 70)],
        [("y", 24), ("c", 96), ("y", 48)],
    ]
    for row, seq in zip(rows, second):
        stream(616, 822, row, seq)
    add('  <text x="533" y="254" text-anchor="middle" class="s dim">summary</text>')
    add('  <text x="604" y="254" text-anchor="middle" class="s warm">frame</text>')

    # after cut 2: a longer summary, which holds the one before it, retold
    summary(856, 128, 84, 100, retold=44)
    add('  <text x="883" y="254" text-anchor="middle" class="s i dim">retold</text>')
    frame_card(948, 144)
    third = [[("c", 40)], [("y", 30), ("c", 10)], [("c", 46)], [("y", 18), ("c", 22)]]
    for row, seq in zip(rows, third):
        stream(986, 1034, row, seq)

    # the cuts: the band is cut through
    for cx in (486, 838):

        def teeth(side: int, order, cx: int = cx) -> str:
            return " ".join(f"L{cx + side + (4 if k % 2 else -1)} {122 + k * 8}" for k in order)

        add(f'  <path d="M{cx - 10} 122 {teeth(-9, range(15))} {teeth(9, range(14, -1, -1))} Z" fill="{p["bg"]}"/>')
        for side in (-9, 9):
            add(
                f'  <path d="M{cx + side - 1} 122 {teeth(side, range(15))}" fill="none" stroke="{p["blue2"]}" '
                'stroke-width="1.1" stroke-linejoin="round"/>'
            )
    add('  <text x="486" y="112" text-anchor="middle" class="s i cool">cut 1</text>')
    add('  <text x="838" y="112" text-anchor="middle" class="s i cool">cut 2</text>')

    # --- between: what goes down, the door, what crosses -----------------------------------------
    add("\n  <!-- what goes down: words of either voice pass; reasoning and tool traffic stay above the mesh -->")
    add(
        f'  <rect x="172" y="298" width="330" height="11" rx="5" fill="url(#meshgrey)" stroke="{p["mesh"]}" '
        'stroke-width="1"/>'
    )
    for x, g in (
        (186, "∴"),
        (220, "{ }"),
        (262, "∴"),
        (300, "{ }"),
        (350, "∴"),
        (392, "{ }"),
        (440, "∴"),
        (470, "{ }"),
    ):
        if g == "∴":
            add(f'  <text x="{x}" y="295" style="font-size:15px; fill:{p["glyph"]}">∴</text>')
        else:
            add(f'  <text x="{x}" y="294" class="mono" style="font-size:15px; fill:{p["glyph"]}">{{ }}</text>')
    for k in range(13):  # what passes, falling into the home
        x = 488 + rnd.uniform(-10, 26)
        y = 320 + k * 10 + rnd.uniform(-3, 3)
        w = rnd.uniform(6, 14)
        colour = p["you"] if rnd.random() < 0.45 else p["claude"]
        add(
            f'  <rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="5" rx="2.5" fill="{colour}" '
            f'opacity="{0.95 - k * 0.03:.2f}" transform="rotate(62 {x:.1f} {y:.1f})"/>'
        )
    add('  <text x="172" y="348" class="b">Kept by itself</text>')
    add('  <text x="172" y="374" class="s dim">words alone pass:</text>')
    add('  <text x="172" y="398" class="s dim">no reasoning, no tool traffic</text>')

    add("\n  <!-- the door: what the session reaches through, between its context and the home -->")
    add(
        f'  <path d="M540 456 V318 C540 302 600 290 670 290 C740 290 800 302 800 318 V456" fill="{p["door"]}" '
        f'stroke="{p["doorline"]}" stroke-width="1.6"/>'
    )
    add(
        '  <path d="M550 456 V322 C550 309 606 300 670 300 C734 300 790 309 790 322 V456" fill="none" '
        f'stroke="{p["doorline"]}" stroke-width=".9" opacity=".6"/>'
    )
    add('  <text x="670" y="336" text-anchor="middle" class="h cool">The door</text>')
    add('  <text x="670" y="368" text-anchor="middle" class="s">look · labels · find</text>')
    add('  <text x="670" y="394" text-anchor="middle" class="s">thread · status</text>')
    add('  <text x="670" y="420" text-anchor="middle" class="s cool">mark · leave</text>')

    add("\n  <!-- what crosses: a small frame, fed from the labels and a few of your own words -->")
    add('  <text x="820" y="348" class="b warm">▲ a frame crosses</text>')
    add('  <text x="820" y="374" class="s warm">about 9,000 characters</text>')

    # --- the home ---------------------------------------------------------------------------------
    add("\n  <!-- the home: plain files. The archive is laid down as sediment and never retold; labels are")
    add("       stakes driven into it; the index is a scaffold beneath, made from the files -->")
    add('  <rect x="150" y="456" width="900" height="560" rx="14" fill="url(#earth)"/>')
    add('  <g clip-path="url(#home)">')
    tops = (628, 690, 752, 818, 882)  # the layers, newest on top; the index lies beneath the last
    for y in tops:
        add(
            f'    <path d="M150 {y} q112 6 225 0 t225 0 t225 0 t225 0" stroke="{p["layer"]}" stroke-width="1.2" '
            'fill="none"/>'
        )
    # off the record: a gap in an older layer; struck: one message taken out. Each with its words
    # cut into the sediment, where no grain is laid
    gap = (962, 1012, 758, 812)  # x0, x1, y0, y1
    struck_at = (996, 852)
    clear = [(676, 770, 930, 802), (838, 836, 956, 866)]
    anchors_wanted = {"R2": (500, 668), "R3": (680, 722), "N3": (759, 676), "W14a": (880, 660)}
    words_at = (1000, 654)  # a message of yours that W14 rests on: the frame quotes it
    # Each anchor rests on a message of its own, laid where the post ends: yours (amber) or Claude's (blue).
    rested = {"R2": "gyou", "R3": "gyou", "N3": "gclaude", "W14a": "gclaude"}
    held = [(x, y) for x, y in anchors_wanted.values()] + [words_at, struck_at]
    for n, (top, bottom) in enumerate(zip(tops, tops[1:])):
        left = 480 if n < 2 else 172
        for ry in range(int(top) + 12, int(bottom) - 6, 13):  # half as many grains as there were: room to read
            x = left + rnd.uniform(0, 14)
            while x < 1030:
                w = rnd.uniform(5, 17)
                y = ry + 3 * math.sin((x - 150) / 225 * math.pi)
                hit = [
                    x1
                    for (x0, y0, x1, y1) in clear + [(gap[0] - 3, gap[2], gap[1] + 3, gap[3])]
                    if x0 - 2 < x + w and x < x1 + 2 and y0 - 4 < y < y1 + 4
                ]
                if hit:
                    x = max(hit) + 4
                    continue
                near = [(hx, hy) for hx, hy in held if hx - 18 < x + w and x < hx + 18 and abs(y - hy) < 8]
                if near:
                    x = near[0][0] + 20
                    continue
                colour = p["gyou"] if rnd.random() < 0.42 else p["gclaude"]
                add(
                    f'    <rect x="{x:.1f}" y="{y - 2.2:.1f}" width="{min(w, 1030 - x):.1f}" height="4.4" rx="2.2" '
                    f'fill="{colour}" opacity="{0.72 - n * 0.09:.2f}"/>'
                )
                x += w + rnd.uniform(9, 21)
    for key, (ax, ay) in anchors_wanted.items():
        add(f'    <rect x="{ax - 8}" y="{ay - 2.2}" width="16" height="4.4" rx="2.2" fill="{p[rested[key]]}"/>')
    # the index: the bottom layer, a scaffold across the whole home, tied to the sediment it is made from
    add(f'    <rect x="150" y="890" width="900" height="126" fill="{p["lattice"]}" opacity=".14"/>')
    for x in range(162, 1050, 26):
        add(f'    <path d="M{x} 890 V1016" stroke="{p["lattice"]}" stroke-width="1" stroke-dasharray="3 4"/>')
    for y in range(890, 1017, 22):
        add(f'    <path d="M150 {y} H1050" stroke="{p["lattice"]}" stroke-width="1" stroke-dasharray="3 4"/>')
    for x in range(162, 1050, 52):
        for y in range(890, 1017, 44):
            add(f'    <rect x="{x - 2}" y="{y - 2}" width="4" height="4" fill="{p["lattice"]}"/>')
    for x in range(214, 1050, 104):  # each tie ends on a grain of the layer above: made from these files
        top = 856 + rnd.uniform(-6, 6)
        add(
            f'    <path d="M{x} 888 L{x + rnd.uniform(-6, 6):.1f} {top:.1f}" stroke="{p["lattice"]}" '
            'stroke-width="1.2" stroke-dasharray="1.5 2.5"/>'
        )
    add("  </g>")
    add(
        '  <path d="M550 456 H164 Q150 456 150 470 V1002 Q150 1016 164 1016 H1036 Q1050 1016 1050 1002 V470 '
        f'Q1050 456 1036 456 H790" fill="none" stroke="{p["homeline"]}" stroke-width="1.4"/>'
    )
    add('  <text x="172" y="492" class="h earth">The home</text>')
    add('  <text x="306" y="492" class="s dim">plain files · no model, no network</text>')

    gx0, gx1, gy0, gy1 = gap
    add(
        f'  <path d="M{gx0} {gy0} V{gy1} M{gx1} {gy0} V{gy1}" stroke="{p["amber2"]}" stroke-width="1.4" '
        'stroke-dasharray="4 4"/>'
    )
    sx, sy = struck_at
    add(
        f'  <rect x="{sx - 9}" y="{sy - 3}" width="18" height="6" rx="3" fill="none" stroke="{p["amber2"]}" '
        'stroke-width="1.3" stroke-dasharray="2 2"/>'
    )
    # your own hand, from your side: the switch and the strike
    gy = (gy0 + gy1) // 2
    add(
        f'  <path d="M1116 {gy} H{gx1 + 6} M1116 {sy} H{sx + 14}" stroke="{p["amber"]}" stroke-width="2" '
        'stroke-dasharray="2 6" stroke-linecap="round"/>'
    )
    add(
        f'  <circle cx="1122" cy="{gy}" r="3.5" fill="{p["amber"]}"/><circle cx="1122" cy="{sy}" r="3.5" '
        f'fill="{p["amber"]}"/>'
    )
    add(f'  <text x="926" y="{gy + 6}" text-anchor="end" class="s warm">/crossings off: nothing kept</text>')
    add(f'  <text x="950" y="{sy + 6}" text-anchor="end" class="s warm">struck: gone</text>')

    # the labels: stakes, each on the ids it rests on; R5 a stack on R2 and R3
    cards = {
        "R5": (430, 510, 268, "R5 · plain words, tests first"),
        "N3": (740, 510, 226, "N3 · next: run the suite"),
        "R2": (410, 558, 156, "R2 · plain words"),
        "R3": (574, 558, 156, "R3 · tests first"),
        "W14": (790, 558, 226, "W14 · second run decides"),
    }
    posts = [("R2", "R2"), ("R3", "R3"), ("N3", "N3"), ("W14", "W14a")]
    wx, wy = words_at
    for card, target in posts:
        ax, ay = anchors_wanted[target]
        add(f'  <path d="M{ax} {cards[card][1] + 32} V{ay - 4}" stroke="{p["post"]}" stroke-width="1.2"/>')
        add(f'  <circle cx="{ax}" cy="{ay}" r="4" fill="none" stroke="{p["text"]}" stroke-width="1.3"/>')
    add(f'  <path d="M{wx} 590 V{wy - 8}" stroke="{p["post"]}" stroke-width="1.2"/>')  # W14's other anchor: your words
    add(f'  <path d="M480 542 V558 M650 542 V558" stroke="{p["cardline"]}" stroke-width="2.4"/>')
    for x, y, w, words in cards.values():
        add(
            f'  <rect x="{x}" y="{y}" width="{w}" height="32" rx="5" fill="{p["card"]}" stroke="{p["cardline"]}" '
            'stroke-width="1.1"/>'
        )
        add(f'  <text x="{x + 9}" y="{y + 23}" class="s">{words}</text>')
    add(
        '  <text x="172" y="536" class="b earth">Labels<tspan dx="12" class="s i dim" '
        'font-weight="400">stakes</tspan></text>'
    )
    add("  <!-- what a label holds, and what it never holds: it crosses every cut as standing -->")
    add('  <text x="172" y="564" class="s warm">what you tell and ask,</text>')
    add('  <text x="172" y="588" class="s warm">never how you seem</text>')

    add(
        '  <text x="172" y="668" class="b earth">The archive<tspan dx="12" class="s i dim" '
        'font-weight="400">sediment</tspan></text>'
    )
    # the two lines stand inside the second layer, clear of the line that parts it from the first: a layer's
    # line drawn through a line of words reads as words struck out. None of these words is drawn with a halo:
    # a stroke painted under a text is a second text to whatever reads the words out of a PDF made from this
    add('  <text x="172" y="712" class="s dim">every word, under its id;</text>')
    add('  <text x="172" y="736" class="s dim">never retold</text>')

    # a clearing in the scaffold for its own words: the lattice's dashes drawn through them made them hard to read
    add(f'  <rect x="162" y="913" width="204" height="84" rx="8" fill="{p["deep"]}"/>')
    add(
        '  <text x="172" y="934" class="b earth">The index<tspan dx="12" class="s i dim" '
        'font-weight="400">scaffold</tspan></text>'
    )
    add('  <text x="172" y="960" class="s dim">made from these files;</text>')
    add('  <text x="172" y="984" class="s dim">may be deleted</text>')

    # what rises: the frame, fed from the standing stack, the line at the door, the work and your words
    add(f'  <rect x="{wx - 9}" y="{wy - 2.2}" width="18" height="4.4" rx="2.2" fill="{p["gyou"]}"/>')
    add(f'  <circle cx="{wx}" cy="{wy}" r="7" fill="none" stroke="{p["feed"]}" stroke-width="1.4"/>')
    add(
        '  <path d="M698 526 C722 526 726 500 754 500 H1016 C1030 500 1036 494 1038 482 '
        "M966 526 C1000 526 1030 530 1036 546 M1016 574 C1027 574 1034 581 1037 593 "
        f'M{wx + 7} {wy} C1022 {wy} 1033 {wy - 8} 1037 {wy - 22}" fill="none" '
        f'stroke="{p["feed"]}" stroke-width="2.6" stroke-linecap="round" opacity=".9"/>'
    )
    add(
        '  <path d="M1038 640 V330 C1038 310 1026 298 1006 298 H990 C972 298 962 290 962 276 V226" fill="none" '
        'stroke="url(#rise)" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'
    )
    add(f'  <path d="M962 214 l-8 14 h16 z" fill="{p["amber2"]}"/>')

    # --- the two directions -------------------------------------------------------------------------
    add("\n  <!-- the loop: down as what was said, up as a small frame across each cut -->")
    add(
        f'  <path d="M150 236 H66 C52 236 44 244 44 258 V1010 C44 1032 58 1044 84 1044 H592" stroke="{p["blue2"]}" '
        'stroke-width="2.4" fill="none" stroke-linecap="round"/>'
    )
    add(f'  <path d="M604 1044 l-14 -8 v16 z" fill="{p["blue2"]}"/>')
    add(
        f'  <path d="M610 1044 H1116 C1142 1044 1156 1032 1156 1010 V258 C1156 244 1148 236 1134 236 H1064" '
        f'stroke="{p["amber"]}" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
    )
    add(f'  <path d="M1051 236 l14 -8 v16 z" fill="{p["amber"]}"/>')
    add(
        '  <text transform="translate(22 640) rotate(-90)" text-anchor="middle" class="s cool">down: what is '
        "said, word for word</text>"
    )
    add(
        '  <text transform="translate(1178 640) rotate(90)" text-anchor="middle" class="s warm">up: a small '
        "frame, across each cut</text>"
    )
    add(
        '  <text x="600" y="1078" text-anchor="middle" class="s i dim">down as what was said; up as a small '
        "frame, across each cut</text>"
    )
    add("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    folder = Path(__file__).resolve().parent.parent / "docs" / "images"
    folder.mkdir(parents=True, exist_ok=True)
    for theme in PALETTES:
        (folder / f"crossings-{theme}.svg").write_text(svg(theme), encoding="utf-8")
