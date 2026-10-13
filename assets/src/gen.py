"""Generate the ink-style profile header / stack / footer SVGs (dark + light).

Usage (from the repo root, needs Pillow only for ink.py):
    python3 assets/src/ink.py koi.webp assets/src   # source image -> koi-white.png / koi-black.png
    python3 assets/src/gen.py assets/src assets     # -> assets/{header,about,stack,footer}-*.svg
"""
import base64
import json
import math
import random
import sys
from pathlib import Path

BUILD = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

SERIF = "'Iowan Old Style','Palatino Linotype',Palatino,'Book Antiqua',Georgia,'Noto Serif',serif"
MONO = "ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
CJK = "'Hiragino Mincho ProN','Yu Mincho','YuMincho','Noto Serif CJK JP','Noto Serif JP','Source Han Serif',serif"

THEMES = {
    "dark": dict(ink="#eef1f4", text="#e6edf3", muted="#8b949e", seal="#e2483b", koi="koi-white.png"),
    "light": dict(ink="#141414", text="#1f2328", muted="#59636e", seal="#c8342a", koi="koi-black.png"),
}


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def poly(points):
    return "M" + " L".join(f"{f(x)} {f(y)}" for x, y in points) + " Z"


def enso(cx, cy, R, theta0, sweep, seed=7):
    """Brush circle: solid body + dry-brush bristle tail, as one path."""
    rnd = random.Random(seed)
    N = 260

    def radius(t):
        return R + 3.5 * math.sin(2 * math.pi * 1.4 * t + 0.6) + 8 * t

    def width(t):
        press = 26 - 11 * math.exp(-t / 0.022)
        return press * (1 - 0.42 * t) + 2.2 * math.sin(7 * math.pi * t + 0.3) + 0.9 * math.sin(19 * math.pi * t)

    def pt(t, off):
        a = math.radians(theta0 + sweep * t)
        r = radius(t) + off
        return cx + r * math.cos(a), cy + r * math.sin(a)

    paths = []
    # solid body, with a rounded "press" at the start
    t_body = 0.36
    ts = [t_body * i / N for i in range(N + 1)]
    outer = [pt(t, width(t) / 2) for t in ts]
    inner = [pt(t, -width(t) / 2) for t in reversed(ts)]
    a0 = math.radians(theta0)
    w0 = width(0) / 2
    r0 = radius(0)
    cap = []
    for k in range(1, 12):
        phi = math.pi * k / 12  # half circle behind the start point
        off = w0 * math.cos(phi)
        back = w0 * 0.9 * math.sin(phi)
        x = cx + (r0 + off) * math.cos(a0) + back * math.sin(a0)
        y = cy + (r0 + off) * math.sin(a0) - back * math.cos(a0)
        cap.append((x, y))
    paths.append(poly(outer + inner + list(reversed(cap))))

    # dry-brush tail: the brush splits into bristles that separate gradually
    # and run out of ink at different points
    cuts = sorted(rnd.uniform(0.02, 0.98) for _ in range(12))
    edges = [0.0] + cuts + [1.0]
    for i in range(len(edges) - 1):
        lo0, hi0 = edges[i], edges[i + 1]
        mid = (lo0 + hi0) / 2
        keep = rnd.uniform(0.45, 0.9)  # share of the band that still carries ink once split
        split = rnd.uniform(0.40, 0.62)  # where this bristle starts to separate
        edge_band = lo0 < 0.12 or hi0 > 0.88
        t_end = rnd.uniform(0.62, 0.84) if edge_band else rnd.uniform(0.78, 1.0)
        s0 = t_body - 0.02
        gaps = sorted(rnd.uniform(split, t_end - 0.05) for _ in range(rnd.choice((0, 1, 1, 2))))
        segs, cur = [], s0
        for g in gaps:
            if g - cur > 0.02:
                segs.append((cur, g))
            cur = g + rnd.uniform(0.008, 0.04)
        segs.append((cur, t_end))
        for s, e in segs:
            if e - s < 0.012:
                continue
            m = max(8, int(N * (e - s)))
            tt = [s + (e - s) * j / m for j in range(m + 1)]

            def edge(t, frac, s=s, e=e, lo0=lo0, hi0=hi0, mid=mid, keep=keep, split=split):
                sep = min(1.0, max(0.0, (t - split) / 0.14))
                k = 1 - (1 - keep) * sep  # band narrows as it separates
                taper = min(1.0, (e - t) / 0.03)
                if s != s0:
                    taper = min(taper, (t - s) / 0.012)
                pad = 0.006 * (1 - sep)  # overlap neighbours until they split (no seams)
                fr = mid + (frac - mid) * k * max(taper, 0.0) + (pad if frac > mid else -pad)
                w = width(t)
                return pt(t, -w / 2 + w * fr)

            paths.append(poly([edge(t, hi0) for t in tt] + [edge(t, lo0) for t in reversed(tt)]))
    return " ".join(paths)


def arc(cx, cy, r, a_from, a_to):
    a1, a2 = math.radians(a_from), math.radians(a_to)
    large = 1 if (a_to - a_from) % 360 > 180 else 0
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    x2, y2 = cx + r * math.cos(a2), cy + r * math.sin(a2)
    return f"M{f(x1)} {f(y1)} A{f(r)} {f(r)} 0 {large} 1 {f(x2)} {f(y2)}"


def header(theme):
    c = THEMES[theme]
    koi = base64.b64encode((BUILD / c["koi"]).read_bytes()).decode()
    W, H = 1200, 420
    cx, cy, R = 300, 210, 168
    theta0, sweep = 112, 322
    brush = enso(cx, cy, R, theta0, sweep)
    mask_arc = arc(cx, cy, R + 4, theta0 - 8, theta0 + sweep + 2)
    mask_len = math.radians(sweep + 10) * (R + 4) + 20

    # pond ripples inside the circle, behind the fish
    ripples = "".join(
        f'<circle cx="{cx}" cy="{cy}" r="60" fill="none" stroke="{c["ink"]}" stroke-width="1.2" opacity="0">'
        f'<animate attributeName="r" values="58;152" dur="9s" begin="{1.5 + i * 3:.1f}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="0;.2;0" keyTimes="0;.25;1" dur="9s" begin="{1.5 + i * 3:.1f}s" repeatCount="indefinite"/>'
        f"</circle>"
        for i in range(3)
    )

    sx, sy, S = 490, 346, 52  # seal centre + size
    tx = 616
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Oleg Rune — fullstack developer">
<defs>
  <filter id="rough" x="-5%" y="-5%" width="110%" height="110%">
    <feTurbulence type="fractalNoise" baseFrequency="0.045" numOctaves="2" seed="3"/>
    <feDisplacementMap in="SourceGraphic" scale="3.2"/>
  </filter>
  <filter id="stamp" x="-10%" y="-10%" width="120%" height="120%">
    <feTurbulence type="fractalNoise" baseFrequency="1.3" numOctaves="1" seed="8" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -7 4.9" result="holes"/>
    <feComposite in="SourceGraphic" in2="holes" operator="in" result="speckled"/>
    <feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="1" seed="5" result="w"/>
    <feDisplacementMap in="speckled" in2="w" scale="1.6"/>
  </filter>
  <mask id="paint" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">
    <path d="{mask_arc}" fill="none" stroke="#fff" stroke-width="56" stroke-dasharray="{f(mask_len)}" stroke-dashoffset="{f(mask_len)}">
      <animate attributeName="stroke-dashoffset" values="{f(mask_len)};0" dur="2.4s" begin="0.2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".45 .05 .25 1"/>
    </path>
  </mask>
</defs>

<g>{ripples}</g>

<g mask="url(#paint)" filter="url(#rough)">
  <path d="{brush}" fill="{c['ink']}" fill-opacity=".93"/>
</g>

<g transform="translate({cx} {cy})">
  <g>
    <animateTransform attributeName="transform" type="rotate" from="0" to="-360" dur="140s" repeatCount="indefinite"/>
    <image href="data:image/png;base64,{koi}" x="-146" y="-146" width="292" height="292"/>
  </g>
</g>

<g transform="translate({sx} {sy})">
  <g opacity="1">
    <animate attributeName="opacity" values="0;0;1" keyTimes="0;.93;1" dur="2.9s" fill="freeze"/>
    <animateTransform attributeName="transform" type="scale" values="1.35;1.35;1" keyTimes="0;.93;1" dur="2.9s" fill="freeze" calcMode="spline" keySplines="0 0 1 1;.3 1.4 .5 1"/>
    <g transform="rotate(-3)">
      <g filter="url(#stamp)">
        <rect x="{-S / 2}" y="{-S / 2}" width="{S}" height="{S}" rx="5" fill="{c['seal']}"/>
        <rect x="{-S / 2 + 4}" y="{-S / 2 + 4}" width="{S - 8}" height="{S - 8}" rx="2.5" fill="none" stroke="#fff" stroke-opacity=".9" stroke-width="1.6"/>
      </g>
      <text x="0" y="12" text-anchor="middle" font-family="{CJK}" font-size="33" font-weight="600" fill="#fff" fill-opacity=".96" filter="url(#rough)">鯉</text>
    </g>
  </g>
</g>

<g font-family="{MONO}" font-size="17" letter-spacing="5" fill="{c['muted']}">
  <text x="{tx + 4}" y="158">FULLSTACK DEVELOPER</text>
</g>
<g font-family="{SERIF}" font-size="96" letter-spacing="-1" fill="{c['text']}">
  <text x="{tx}" y="250">Oleg Rune</text>
</g>
<rect x="{tx + 4}" y="283" width="56" height="2.5" fill="{c['seal']}">
  <animate attributeName="width" values="0;0;56" keyTimes="0;.55;1" dur="2.2s" fill="freeze" calcMode="spline" keySplines="0 0 1 1;.2 .7 .3 1"/>
</rect>
</svg>
"""


def footer(theme):
    c = THEMES[theme]
    W, H = 1200, 80
    x0, x1, yc = 380, 820, 40
    N = 220
    top, bot = [], []
    for i in range(N + 1):
        t = i / N
        x = x0 + (x1 - x0) * t
        env = math.sin(math.pi * t)
        y = yc + 7 * math.sin(2 * math.pi * 2.5 * t) * env
        w = 0.6 + 5.2 * env ** 1.6 * (1 - 0.35 * t)
        top.append((x, y - w / 2))
        bot.append((x, y + w / 2))
    d = poly(top + list(reversed(bot)))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="">
<defs>
  <filter id="rough" x="-5%" y="-50%" width="110%" height="200%">
    <feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="2" seed="4"/>
    <feDisplacementMap in="SourceGraphic" scale="2.4"/>
  </filter>
  <clipPath id="draw"><rect x="{x0 - 10}" y="0" width="0" height="{H}">
    <animate attributeName="width" values="0;{x1 - x0 + 20}" dur="2.2s" begin="0.3s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".45 .05 .25 1"/>
  </rect></clipPath>
</defs>
<g clip-path="url(#draw)" filter="url(#rough)"><path d="{d}" fill="{c['ink']}" fill-opacity=".85"/></g>
<circle cx="{(x0 + x1) / 2}" cy="{yc - 22}" r="5" fill="{c['seal']}" opacity="1">
  <animate attributeName="opacity" values="0;0;1" keyTimes="0;.9;1" dur="2.8s" fill="freeze"/>
</circle>
</svg>
"""


ABOUT = [
    ("SCHEMA", "PostgreSQL", "modelled in Prisma"),
    ("API", "Python", "or Bun + Elysia"),
    ("INTERFACE", "Vue & React", "with Vite & Tailwind"),
]


def brush_line(x0, x1, yc, amp=4.0, waves=1.0, wmax=4.2, n=120):
    """Tapered ink stroke along a gentle wave; returns (filled outline, centre line)."""
    top, bot, mid = [], [], []
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = yc + amp * math.sin(2 * math.pi * waves * t) * math.sin(math.pi * t)
        w = 0.5 + wmax * math.sin(math.pi * t) ** 0.8 * (1 - 0.55 * t)
        top.append((x, y - w / 2))
        bot.append((x, y + w / 2))
        mid.append((x, y))
    centre = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in mid)
    return poly(top + list(reversed(bot))), centre


def about(theme):
    """'End to end' strip: schema -> API -> interface, with a red dot running along the ink."""
    c = THEMES[theme]
    W, H = 1200, 330
    cols = [200, 600, 1000]
    half = [118, 92, 118]  # rough half-width of each value, keeps the strokes clear of the text
    y_label, y_value, y_sub = 128, 182, 214
    parts = []
    for (label, value, sub), x, i in zip(ABOUT, cols, range(3)):
        parts.append(
            f'<text x="{x}" y="{y_label}" text-anchor="middle" font-family="{MONO}" font-size="14" letter-spacing="4" fill="{c["muted"]}">'
            f'<tspan fill="{c["seal"]}">0{i + 1}</tspan> — {label}</text>'
            f'<text x="{x}" y="{y_value}" text-anchor="middle" font-family="{SERIF}" font-size="40" fill="{c["text"]}">{value.replace("&", "&amp;")}</text>'
            f'<text x="{x}" y="{y_sub}" text-anchor="middle" font-family="{SERIF}" font-style="italic" font-size="19" fill="{c["muted"]}">{sub.replace("&", "&amp;")}</text>'
        )
    strokes, route = [], []
    for k in range(2):
        a, b = cols[k] + half[k] + 22, cols[k + 1] - half[k + 1] - 22
        d, centre = brush_line(a, b, y_value - 13, amp=5, waves=1 + 0.5 * k)
        strokes.append(f'<path d="{d}" fill="{c["ink"]}" fill-opacity=".8"/>')
        route.append(centre)
    route = " ".join(route)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="I build web apps end to end: PostgreSQL schema, Python or Bun + Elysia API, Vue and React interface.">
<defs>
  <filter id="rough" x="-5%" y="-60%" width="110%" height="220%">
    <feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="2" seed="6"/>
    <feDisplacementMap in="SourceGraphic" scale="2.2"/>
  </filter>
</defs>
<text x="{W / 2}" y="48" text-anchor="middle" font-family="{SERIF}" font-size="30" fill="{c['text']}">I build web apps <tspan font-style="italic">end to end</tspan></text>
<g filter="url(#rough)">{"".join(strokes)}</g>
<circle r="4.5" fill="{c['seal']}" opacity="0">
  <animateMotion path="{route}" dur="4.2s" repeatCount="indefinite" keyPoints="0;1;1" keyTimes="0;.72;1" calcMode="linear"/>
  <animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.04;.68;.72;1" dur="4.2s" repeatCount="indefinite"/>
</circle>
{"".join(parts)}
<text x="{W / 2}" y="292" text-anchor="middle" font-family="{SERIF}" font-style="italic" font-size="23" fill="{c['muted']}">soft spot for Three.js, smooth motion and calm, well-made UI.</text>
</svg>
"""


STACK = [
    ("FRONTEND", [("typescript", "TypeScript"), ("javascript", "JavaScript"), ("vuedotjs", "Vue"), ("react", "React"),
                  ("astro", "Astro"), ("tailwindcss", "Tailwind"), ("threedotjs", "Three.js"), ("gsap", "GSAP"), ("vite", "Vite")]),
    ("BACKEND", [("python", "Python"), ("bun", "Bun"), ("prisma", "Prisma"), ("postgresql", "PostgreSQL"), ("graphql", "GraphQL"),
                 ("docker", "Docker"), ("mqtt", "MQTT")]),
    ("ALSO", [("flutter", "Flutter"), ("dart", "Dart"), ("openjdk", "Java"), ("git", "Git")]),
]


def stack(theme):
    """Tech stack as monochrome Simple Icons (CC0), one row per area."""
    c = THEMES[theme]
    icons = json.loads((BUILD / "icons.json").read_text())
    W, H = 1200, 384
    lx, ix, step, size, row_h, top = 72, 300, 100, 38, 124, 34
    rows = []
    for i, (label, items) in enumerate(STACK):
        y = top + i * row_h
        rows.append(f'<circle cx="{lx - 14}" cy="{y + size / 2 - 1}" r="3" fill="{c["seal"]}"/>')
        rows.append(f'<text x="{lx}" y="{y + size / 2 + 5}" font-family="{MONO}" font-size="15" letter-spacing="5" fill="{c["muted"]}">{label}</text>')
        for j, (slug, name) in enumerate(items):
            cx = ix + j * step
            rows.append(
                f'<path transform="translate({cx - size / 2} {y}) scale({f(size / 24)})" d="{icons[slug]}" fill="{c["text"]}" fill-opacity=".92"/>'
                f'<text x="{cx}" y="{y + size + 28}" text-anchor="middle" font-family="{MONO}" font-size="14" fill="{c["muted"]}">{name}</text>'
            )
        if i < len(STACK) - 1:
            rows.append(f'<line x1="{lx - 14}" x2="{W - lx}" y1="{y + row_h - 20}" y2="{y + row_h - 20}" stroke="{c["ink"]}" stroke-opacity=".12"/>')
    alt = "; ".join(f"{label.lower()}: " + ", ".join(n for _, n in items) for label, items in STACK)
    body = "\n".join(rows)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Stack — {alt}">
{body}
</svg>
"""


for theme in THEMES:
    (OUT / f"header-{theme}.svg").write_text(header(theme))
    (OUT / f"about-{theme}.svg").write_text(about(theme))
    (OUT / f"stack-{theme}.svg").write_text(stack(theme))
    (OUT / f"footer-{theme}.svg").write_text(footer(theme))
    print(theme, *(f"{n}:{(OUT / f'{n}-{theme}.svg').stat().st_size}" for n in ("header", "about", "stack", "footer")))
