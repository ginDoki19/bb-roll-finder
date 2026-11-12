#!/usr/bin/env python3
"""Deterministic screenshot set used to prove a refactor changed nothing visually.

    python3 tools/_shotset.py <outdir>
"""
import functools, http.server, os, socketserver, sys, threading
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
from playwright.sync_api import sync_playwright

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Q, directory=ROOT))
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    URL = f"http://127.0.0.1:{port}/index.html"

    SHOTS = [
        # name,             scheme,  lang, roll,     w,    h,   expand, print
        ("home-dark-en",    "dark",  "en", None,     1120, 1000, False, False),
        ("home-light-en",   "light", "en", None,     1120, 1000, False, False),
        ("home-dark-bn",    "dark",  "bn", None,     1120, 1000, False, False),
        ("home-light-bn",   "light", "bn", None,     1120, 1000, False, False),
        ("disambig-dark-en","dark",  "en", "100001", 1120, 1400, False, False),
        ("disambig-light-bn","light","bn", "100001", 1120, 1400, False, False),
        ("congrats-light-bn","light","bn", "501991", 1120, 1100, False, False),
        ("written-dark-bn", "dark",  "bn", "213880", 1120, 1200, False, False),
        ("notfound-light-en","light","en", "999999", 1120,  800, False, False),
        ("rollgrid-dark-en","dark",  "en", None,     1120, 1500, True,  False),
        ("mobile-dark-bn",  "dark",  "bn", "100001",  390, 1400, False, False),
        ("print-light-en",  "light", "en", "105432", 1120, 1200, False, True),
    ]
    with sync_playwright() as p:
        b = p.chromium.launch()
        for name, scheme, lang, roll, w, h, expand, pr in SHOTS:
            c = b.new_context(color_scheme=scheme, viewport={"width": w, "height": h})
            pg = c.new_page()
            pg.goto(URL, wait_until="networkidle")
            if lang != "en":
                pg.click(f"[data-lang-set='{lang}']"); pg.wait_for_timeout(300)
            if roll:
                pg.fill("#roll", roll); pg.wait_for_timeout(500)
            if expand:
                pg.evaluate("""()=>{const d=[...document.querySelectorAll('details')]
                    .find(x=>x.querySelector('.rollwrap')); if(d){d.open=true;d.scrollIntoView({block:'center'});}}""")
                pg.wait_for_timeout(800)
            if pr:
                pg.emulate_media(media="print")
            pg.wait_for_timeout(700)          # let the .card pop animation finish
            pg.screenshot(path=os.path.join(outdir, name + ".png"))
            c.close()
            print("  shot", name)
        b.close()
    srv.shutdown()

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "shots")
