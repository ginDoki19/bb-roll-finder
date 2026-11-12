#!/usr/bin/env python3
"""Pixel-compare two screenshot sets.  python3 tools/_shotdiff.py <a> <b>"""
import os, sys
from PIL import Image, ImageChops

def main(a, b):
    names = sorted(f for f in os.listdir(a) if f.endswith(".png"))
    worst, bad = 0.0, 0
    for n in names:
        pa, pb = os.path.join(a, n), os.path.join(b, n)
        if not os.path.exists(pb):
            print(f"  MISSING  {n}"); bad += 1; continue
        ia, ib = Image.open(pa).convert("RGB"), Image.open(pb).convert("RGB")
        if ia.size != ib.size:
            print(f"  SIZE     {n}  {ia.size} -> {ib.size}"); bad += 1; continue
        diff = ImageChops.difference(ia, ib)
        box = diff.getbbox()
        if box is None:
            print(f"  identical {n}")
            continue
        px = sum(1 for p in diff.getdata() if p != (0, 0, 0))
        pct = 100.0 * px / (ia.size[0] * ia.size[1])
        worst = max(worst, pct)
        bad += 1
        print(f"  DIFFER   {n}  {px} px ({pct:.3f}%) bbox={box}")
        diff.save(os.path.join(b, n.replace(".png", "") + ".diff.png"))
    print(f"\n{len(names)} compared · {bad} differing · worst {worst:.3f}%")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
