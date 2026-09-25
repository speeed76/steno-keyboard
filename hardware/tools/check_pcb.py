#!/usr/bin/env python3
"""Sanity checks and a preview image for the Ergogen-generated PCB.

    python3 hardware/tools/check_pcb.py hardware/ergogen/output/pcbs/steno_qwerty.kicad_pcb [--png out.png]

This does not replace KiCad's DRC. It is a quick placement check that runs
without KiCad installed: every pad sits inside the board outline, pads of
different footprints keep clear of each other, and switch bodies, keycaps, the
Pico and the mode switch do not collide.
"""

import argparse
import math
import re
import sys

NUM = r"(-?[\d.]+(?:e-?\d+)?)"


def parse(path):
    text = open(path).read()
    modules = []
    for chunk in text.split("(module ")[1:]:
        name = chunk.split()[0]
        at = re.search(r"\(at %s %s(?: %s)?\)" % (NUM, NUM, NUM), chunk)
        mx, my, mr = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
        ref = re.search(r'fp_text reference "([^"]*)"', chunk).group(1)
        pads = []
        for m in re.finditer(
            r"\(pad (\S+) (\S+) (\S+) \(at %s %s(?: %s)?\) \(size %s %s\)(.*)" % (NUM, NUM, NUM, NUM, NUM), chunk
        ):
            px, py = float(m.group(4)), float(m.group(5))
            w, h = float(m.group(7)), float(m.group(8))
            net = re.search(r'\(net \d+ "([^"]*)"\)', m.group(9))
            a = math.radians(mr)
            wx = mx + px * math.cos(a) + py * math.sin(a)
            wy = my - px * math.sin(a) + py * math.cos(a)
            pads.append({"x": wx, "y": wy, "r": max(w, h) / 2, "net": net.group(1) if net else None,
                         "kind": m.group(2), "layers": m.group(9)})
        modules.append({"name": name, "ref": ref, "x": mx, "y": my, "rot": mr, "pads": pads})

    edges = []
    for m in re.finditer(r"\(gr_line \(start %s %s\) \(end %s %s\)(?: \(angle %s\))? \(layer Edge.Cuts\)" % (NUM, NUM, NUM, NUM, NUM), text):
        edges.append(tuple(float(g) for g in m.groups()[:4]))
    for m in re.finditer(r"\(gr_arc \(start %s %s\) \(end %s %s\) \(angle %s\) \(layer Edge.Cuts\)" % ((NUM,) * 5), text):
        cx, cy, sx, sy, ang = (float(g) for g in m.groups())
        a = math.radians(ang)
        ex = cx + (sx - cx) * math.cos(a) - (sy - cy) * math.sin(a)
        ey = cy + (sx - cx) * math.sin(a) + (sy - cy) * math.cos(a)
        edges.append((sx, sy, ex, ey))
    return modules, edges


def inside(x, y, edges):
    crossings = 0
    for x1, y1, x2, y2 in edges:
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                crossings += 1
    return crossings % 2 == 1


def seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(px - x1 - t * dx, py - y1 - t * dy)


def box(m, w, h, dx=0, dy=0):
    """Corners of a w x h rectangle centred at (dx, dy) in footprint coordinates."""
    a = math.radians(m["rot"])
    out = []
    for cx, cy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        cx += dx
        cy += dy
        out.append((m["x"] + cx * math.cos(a) + cy * math.sin(a), m["y"] - cx * math.sin(a) + cy * math.cos(a)))
    return out


def polys_overlap(p, q):
    """Separating axis test for two convex polygons."""
    for poly in (p, q):
        for i in range(len(poly)):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % len(poly)]
            nx, ny = y2 - y1, x1 - x2
            a = [nx * x + ny * y for x, y in p]
            b = [nx * x + ny * y for x, y in q]
            if max(a) <= min(b) or max(b) <= min(a):
                return False
    return True


BODIES = {
    # footprint name: list of (label, width, height, dx, dy) keep-out boxes
    "MX": [("switch", 14.0, 14.0, 0, 0), ("keycap", 18.0, 18.0, 0, 0)],
    "RPi_Pico": [("pico", 21.0, 51.0, 0, 0)],
    "E73:SPDT_C128955": [("slider", 6.6, 2.85, 0, 0.075)],
}
# which bodies may not overlap which (keycaps float above the Pico and diodes)
CLASH = {("switch", "switch"), ("keycap", "keycap"), ("switch", "pico"), ("switch", "slider"),
         ("pico", "slider")}


def outline_loops(edges):
    """Number of separate closed outlines (a manufacturable board has exactly one)."""
    parent = {}

    def find(k):
        while parent.setdefault(k, k) != k:
            k = parent[k]
        return k

    for x1, y1, x2, y2 in edges:
        a, b = (round(x1, 2), round(y1, 2)), (round(x2, 2), round(y2, 2))
        parent[find(a)] = find(b)
    return len({find(k) for k in list(parent)})


def check(modules, edges, clearance=0.2, edge_clearance=0.5):
    problems = []
    loops = outline_loops(edges)
    if loops != 1:
        problems.append("board outline has %d separate pieces (expected 1)" % loops)
    for m in modules:
        for p in m["pads"]:
            if not inside(p["x"], p["y"], edges):
                problems.append("%s pad at (%.2f, %.2f) is outside the board" % (m["ref"], p["x"], p["y"]))
                continue
            d = min(seg_dist(p["x"], p["y"], *e) for e in edges) - p["r"]
            if d < edge_clearance and m["name"] != "E73:SPDT_C128955":
                problems.append("%s pad at (%.2f, %.2f) is %.2f mm from the board edge" % (m["ref"], p["x"], p["y"], d))

    def copper_layers(pad):
        layers = pad["layers"]
        if "*.Cu" in layers:
            return {"F", "B"}
        return {s for s in ("F", "B") if s + ".Cu" in layers}

    for i, a in enumerate(modules):
        for b in modules[i + 1:]:
            if math.hypot(a["x"] - b["x"], a["y"] - b["y"]) > 40:
                continue
            for pa in a["pads"]:
                for pb in b["pads"]:
                    if pa["net"] and pa["net"] == pb["net"]:
                        continue
                    holes = pa["kind"] == "np_thru_hole" or pb["kind"] == "np_thru_hole"
                    if not holes and not (copper_layers(pa) & copper_layers(pb)):
                        continue
                    gap = math.hypot(pa["x"] - pb["x"], pa["y"] - pb["y"]) - pa["r"] - pb["r"]
                    if gap < clearance:
                        problems.append("%s and %s pads are %.2f mm apart at (%.1f, %.1f)"
                                        % (a["ref"], b["ref"], gap, pa["x"], pa["y"]))

    bodies = []
    for m in modules:
        for label, w, h, dx, dy in BODIES.get(m["name"], []):
            bodies.append((m["ref"], label, box(m, w, h, dx, dy)))
    for i, (ra, la, pa) in enumerate(bodies):
        for rb, lb, pb in bodies[i + 1:]:
            if ra != rb and ((la, lb) in CLASH or (lb, la) in CLASH) and polys_overlap(pa, pb):
                problems.append("%s %s overlaps %s %s" % (ra, la, rb, lb))
    return problems


def render(modules, edges, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Polygon

    fig, ax = plt.subplots(figsize=(16, 9))
    for x1, y1, x2, y2 in edges:
        ax.plot([x1, x2], [-y1, -y2], color="black", lw=1)
    colors = {"MX": "#4a7fd6", "RPi_Pico": "#2e9e5b", "E73:SPDT_C128955": "#d0822a", "ComboDiode": "#b04ab0"}
    for m in modules:
        c = colors.get(m["name"], "gray")
        for label, w, h, dx, dy in BODIES.get(m["name"], []):
            pts = [(x, -y) for x, y in box(m, w, h, dx, dy)]
            ax.add_patch(Polygon(pts, fill=False, ec=c, lw=0.6, ls="--" if label == "keycap" else "-"))
        for p in m["pads"]:
            ax.add_patch(Circle((p["x"], -p["y"]), p["r"], color=c, alpha=0.6, lw=0))
    ax.set_aspect("equal")
    ax.autoscale_view()
    ax.set_title("Placement preview: keycaps dashed, switch bodies solid, pads filled")
    fig.savefig(path, dpi=110, bbox_inches="tight")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pcb")
    ap.add_argument("--png", help="write a placement preview image")
    args = ap.parse_args()
    modules, edges = parse(args.pcb)
    if args.png:
        render(modules, edges, args.png)
    problems = check(modules, edges)
    print("%d footprints, %d pads, %d edge segments" % (
        len(modules), sum(len(m["pads"]) for m in modules), len(edges)))
    for p in problems:
        print("PROBLEM:", p)
    print("OK" if not problems else "%d problem(s)" % len(problems))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
