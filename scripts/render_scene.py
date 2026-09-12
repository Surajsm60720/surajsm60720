#!/usr/bin/env python3
"""Render a pixel-art scene for the current time in Asia/Kolkata."""
import math, random, sys
from datetime import datetime, timezone, timedelta

CELL, COLS, ROWS = 6, 150, 52
W, H = COLS*CELL, ROWS*CELL
IST = timezone(timedelta(hours=5, minutes=30))

BANDS = [
    # name        hours        sky top    sky bottom  land      accent(sun/moon) stars lit
    ("deep night", range(0,5),  "#0b1026", "#1b2450", "#080b18", "#c9d4f0", 0.95, 0.85),
    ("dawn",       range(5,7),  "#2b2350", "#f2a071", "#161428", "#ffd9a0", 0.35, 0.45),
    ("morning",    range(7,11), "#4a9fd8", "#bfe4f5", "#1d3040", "#fff3c4", 0.00, 0.05),
    ("midday",     range(11,16),"#2e86c8", "#a8dcf0", "#22384a", "#fff8d8", 0.00, 0.00),
    ("golden",     range(16,19),"#3d3a6b", "#f08a5d", "#1a1730", "#ffc078", 0.10, 0.30),
    ("night",      range(19,24),"#0d1330", "#24305e", "#0a0e1c", "#dbe4ff", 0.85, 0.80),
]
BAYER = [[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]]

def band_for(hour):
    for b in BANDS:
        if hour in b[1]: return b
    return BANDS[-1]

def lerp(a,b,t):
    A=[int(a[i:i+2],16) for i in (1,3,5)]; B=[int(b[i:i+2],16) for i in (1,3,5)]
    return "#%02x%02x%02x" % tuple(round(A[i]+(B[i]-A[i])*t) for i in range(3))

def sky_grid(top, bot):
    """Vertical gradient, ordered-dithered between two neighbouring steps."""
    STEPS=7
    ramp=[lerp(top,bot,i/(STEPS-1)) for i in range(STEPS)]
    g=[]
    for r in range(ROWS):
        row=[]
        t=(r/(ROWS-1))*(STEPS-1)
        lo=int(t); frac=t-lo; hi=min(lo+1,STEPS-1)
        for c in range(COLS):
            row.append(ramp[hi] if frac*16 > BAYER[r%4][c%4] else ramp[lo])
        g.append(row)
    return g

def put(g,c,r,col):
    if 0<=r<ROWS and 0<=c<COLS: g[r][c]=col

def disc(g,cx,cy,rad,col):
    for r in range(int(cy-rad)-1,int(cy+rad)+2):
        for c in range(int(cx-rad)-1,int(cx+rad)+2):
            if (c-cx)**2+(r-cy)**2 <= rad*rad: put(g,c,r,col)

def crescent(g,cx,cy,rad,col,sky):
    disc(g,cx,cy,rad,col)
    disc(g,cx+rad*0.55,cy-rad*0.35,rad*0.92,sky)

def skyline(g,land,lit_col,lit_p,rnd,base=None):
    base=(ROWS-1) if base is None else base
    c=0
    lights=[]
    while c < COLS:
        bw=rnd.randint(6,13); bh=rnd.randint(5,17)
        top=base-bh
        for x in range(c,min(c+bw,COLS)):
            for y in range(top,ROWS): put(g,x,y,land)
        for wy in range(top+2, base, 3):
            for wx in range(c+2, min(c+bw,COLS)-1, 3):
                if rnd.random() < lit_p:
                    lights.append((wx,wy))
        c += bw + rnd.randint(0,2)
    return lights

def stars(g, density, rnd, maxrow):
    pts=[]
    n=int(COLS*maxrow*0.020*density)
    for _ in range(n):
        c=rnd.randrange(COLS); r=rnd.randrange(maxrow)
        pts.append((c,r))
    return pts

def clouds(rnd, n):
    out=[]
    for _ in range(n):
        cx=rnd.uniform(0,COLS); cy=rnd.uniform(2,11)
        puffs=[(cx+dx, cy+rnd.uniform(-0.6,0.6), rnd.uniform(1.6,3.4))
               for dx in (-3.2,-1.0,1.2,3.0)]
        out.append((puffs, rnd.uniform(0.35,1.0)))
    return out

def runs(g):
    """Merge equal horizontal neighbours into single rects."""
    out=[]
    for r,row in enumerate(g):
        c=0
        while c<COLS:
            col=row[c]; s=c
            while c+1<COLS and row[c+1]==col: c+=1
            out.append((s, r, c-s+1, col)); c+=1
    return out


LINES = ["Building Saizen, an anime streaming app for iOS",
         "Shipping Next.js and TypeScript on the web",
         "Automating Linux with Python and Bash"]

def dialogue(ink, edge, W, H):
    """A JRPG-style text box: chunky double border, translucent fill."""
    bx, bw = 42, W-84
    bh, by = 124, H-124-14
    B = 6                                    # border thickness, one cell
    hold, fade = 3.4, 0.6
    slot = hold+fade; total = slot*len(LINES)
    a, b, c = fade/total*100, (fade+hold)/total*100, (fade+hold+fade*.5)/total*100
    o=[f'<g>']
    o.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="#0b1026" opacity=".82"/>')
    o.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{B}" fill="{edge}"/>')
    o.append(f'<rect x="{bx}" y="{by+bh-B}" width="{bw}" height="{B}" fill="{edge}"/>')
    o.append(f'<rect x="{bx}" y="{by}" width="{B}" height="{bh}" fill="{edge}"/>')
    o.append(f'<rect x="{bx+bw-B}" y="{by}" width="{B}" height="{bh}" fill="{edge}"/>')
    # inner hairline, the classic doubled frame
    o.append(f'<rect x="{bx+B*2}" y="{by+B*2}" width="{bw-B*4}" height="{bh-B*4}" '
             f'fill="none" stroke="{edge}" stroke-width="2" opacity=".45"/>')
    tx = bx+B*4
    o.append(f'<text x="{tx}" y="{by+50}" class="nm">SURAJ MENON</text>')
    o.append(f'<text x="{tx}" y="{by+76}" class="rl">iOS &amp; web developer \u00b7 Bengaluru, India</text>')
    o.append(f'<g class="cyc">')
    for i,l in enumerate(LINES):
        o.append(f'<g class="ln" style="animation-delay:{i*slot:.2f}s">'
                 f'<text x="{tx}" y="{by+106}" class="st">&#9656; {l}</text></g>')
    o.append('</g>')
    o.append(f'<text x="{bx+bw-B*4}" y="{by+bh-16}" class="ar" text-anchor="end">&#9662;</text>')
    o.append('</g>')
    css=(f'.nm{{font:700 30px ui-monospace,SFMono-Regular,Menlo,monospace;fill:#ffffff;letter-spacing:2px}}'
         f'.rl{{font:400 14px ui-monospace,SFMono-Regular,Menlo,monospace;fill:#aab4d4}}'
         f'.st{{font:500 14px ui-monospace,SFMono-Regular,Menlo,monospace;fill:{ink}}}'
         f'.ar{{font:700 15px ui-monospace,monospace;fill:{edge};animation:ar 1.1s steps(2,end) infinite}}'
         f'.ln{{opacity:0;animation:cy {total:.1f}s infinite}}'
         f'@keyframes cy{{0%{{opacity:0}}{a:.2f}%{{opacity:1}}{b:.2f}%{{opacity:1}}{c:.2f}%{{opacity:0}}100%{{opacity:0}}}}'
         f'@keyframes ar{{0%,50%{{opacity:1}}51%,100%{{opacity:0}}}}'
         f'@media (prefers-reduced-motion:reduce){{.ln{{animation:none;opacity:0}}'
         f'.ln:first-of-type{{opacity:1}}.ar{{animation:none}}}}')
    return "".join(o), css

def build(now=None):
    now = now or datetime.now(IST)
    hour = now.hour
    name, hours, top, bot, land, accent, star_d, lit_p = band_for(hour)
    rnd = random.Random(20260912)          # fixed seed: layout is stable across renders
    g = sky_grid(top, bot)

    # celestial arc: rises ~05:30, sets ~18:30; moon takes the opposite half
    day_t = (hour + now.minute/60 - 5.5)/13.0
    if 0.0 <= day_t <= 1.0:
        cx = 8 + day_t*(COLS-16); cy = 19 - math.sin(day_t*math.pi)*15
        disc(g, cx, cy, 3.4, accent); body=("sun", cx, cy)
    else:
        nt = ((hour + now.minute/60 - 18.5) % 24)/11.0
        cx = 8 + nt*(COLS-16); cy = 18 - math.sin(nt*math.pi)*14
        crescent(g, cx, cy, 3.2, accent, g[int(cy)][int(cx)]); body=("moon", cx, cy)

    star_pts = stars(g, star_d, rnd, int(ROWS*0.42)) if star_d>0.02 else []
    cl = clouds(rnd, 3 if star_d < 0.3 else 0)
    BOX_TOP_ROW = ROWS-23
    for r in range(BOX_TOP_ROW, ROWS):          # ground plate: no sky between buildings
        for c in range(COLS): g[r][c] = land
    lights = skyline(g, land, accent, lit_p, rnd, base=BOX_TOP_ROW)

    px=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'shape-rendering="crispEdges" role="img" '
        f'aria-label="Pixel art scene of Bengaluru at {name}, {now:%H:%M} IST.">']
    px.append('<style>'
      '.tw{animation:tw 3.4s steps(2,end) infinite}'
      '.tw:nth-of-type(3n){animation-delay:1.1s}.tw:nth-of-type(3n+1){animation-delay:2.2s}'
      '.lt{animation:lt 6s steps(2,end) infinite}.lt:nth-of-type(4n){animation-delay:2.5s}'
      '.cl{animation:cl 60s linear infinite}'
      '@keyframes tw{0%,60%{opacity:1}61%,100%{opacity:.25}}'
      '@keyframes lt{0%,80%{opacity:1}81%,100%{opacity:.45}}'
      f'@keyframes cl{{from{{transform:translateX(0)}}to{{transform:translateX({W}px)}}}}'
      '@media (prefers-reduced-motion:reduce){.tw,.lt,.cl{animation:none}}'
      '</style>')
    for x,y,w,col in runs(g):
        px.append(f'<rect x="{x*CELL}" y="{y*CELL}" width="{w*CELL}" height="{CELL}" fill="{col}"/>')
    hero_svg, hero_css = dialogue(accent, accent, W, H)
    for puffs,op in cl:
        px.append(f'<g class="cl" opacity="{op:.2f}">')
        for off in (-W, 0):
            px.append(f'<g transform="translate({off},0)">')
            for cx,cy,rr in puffs:
                px.append(f'<rect x="{round((cx-rr)*CELL)}" y="{round(cy*CELL)}" '
                          f'width="{round(rr*2*CELL)}" height="{round(CELL*1.6)}" fill="#ffffff" opacity=".5"/>')
            px.append('</g>')
        px.append('</g>')
    for c,r in star_pts:
        px.append(f'<rect class="tw" x="{c*CELL}" y="{r*CELL}" width="{CELL}" height="{CELL}" fill="{accent}"/>')
    for c,r in lights:
        px.append(f'<rect class="lt" x="{c*CELL}" y="{r*CELL}" width="{CELL}" height="{CELL}" fill="{accent}" opacity=".9"/>')
    px.append(hero_svg)
    px.append(f'<style>{hero_css}</style>')
    px.append('</svg>')
    return "\n".join(px), name, now

if __name__=="__main__":
    svg,name,now = build()
    out = sys.argv[1] if len(sys.argv)>1 else "assets/scene.svg"
    open(out,"w").write(svg)
    print(f"{name} @ {now:%H:%M} IST -> {out}")
