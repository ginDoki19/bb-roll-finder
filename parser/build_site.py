#!/usr/bin/env python3
"""
build_site.py — inline data/notices.json into app.template.html -> index.html

Inlining (rather than fetch()) means the page works from file://, offline on a
phone, and inside sandboxed iframes with no network — which is how most people
will actually open this on exam day.

    python3 parser/build_site.py
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def main():
    tpl = os.path.join(ROOT, "app.template.html")
    dat = os.path.join(ROOT, "data", "notices.json")
    out = os.path.join(ROOT, "index.html")

    html = open(tpl, encoding="utf-8").read()
    data = open(dat, encoding="utf-8").read().strip()

    if "/*__DATA__*/" not in html:
        sys.exit("template is missing the /*__DATA__*/ placeholder")

    html = html.replace("/*__DATA__*/", data)
    open(out, "w", encoding="utf-8").write(html)
    print(f"wrote {out}  ({os.path.getsize(out)//1024} KB, {len(json.loads(data)['notices'])} notices inlined)")

if __name__ == "__main__":
    main()
