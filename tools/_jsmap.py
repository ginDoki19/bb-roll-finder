#!/usr/bin/env python3
"""
_jsmap.py — analyse the main <script> in app.template.html before splitting it.

Scratch/diagnostic tool for the Phase-4 refactor. It answers two questions:

  1. What top-level names does the script declare, and in which banner section
     does each one live?  -> tells me which file each binding belongs in.
  2. Which of those names are referenced at module-evaluation time (as opposed
     to inside a function body)?  -> tells me whether concatenation order can
     break anything.

That second question is the whole risk of this phase. `const` and `let` are
subject to the temporal dead zone: if file A runs `const X = f(Y)` at the top
level and Y is declared in file B which is concatenated later, the page throws
on load. References from *inside* a function body are safe, because the
function is not called until boot() runs at the very end.

    python3 tools/_jsmap.py
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, "app.template.html")


def main_script(text):
    """Return (body, first_line_number) for the last <script> block."""
    starts = [m.end() for m in re.finditer(r"<script>\n", text)]
    ends = [m.start() for m in re.finditer(r"\n</script>", text)]
    s, e = starts[-1], ends[-1]
    return text[s:e], text[:s].count("\n") + 1


def strip_noise(src):
    """Blank out string/template/regex/comment content, preserving offsets.

    Keeps the character count identical so line numbers stay accurate, but
    stops a word inside a Bengali string literal from being mistaken for an
    identifier reference.
    """
    out = list(src)
    i, n = 0, len(src)
    stack = []  # template-literal nesting
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "*":
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            for k in range(i, j):
                if out[k] != "\n":
                    out[k] = " "
            i = j
            continue
        if c == "/" and nxt == "/":
            j = src.find("\n", i)
            j = n if j < 0 else j
            for k in range(i, j):
                out[k] = " "
            i = j
            continue
        if c in "'\"":
            q = c
            j = i + 1
            while j < n and src[j] != q:
                if src[j] == "\\":
                    j += 1
                if src[j : j + 1] == "\n":
                    break
                j += 1
            for k in range(i, min(j + 1, n)):
                if out[k] != "\n":
                    out[k] = " "
            i = min(j + 1, n)
            continue
        if c == "`":
            # walk the template literal, leaving ${...} expressions intact
            j = i + 1
            out[i] = " "
            while j < n:
                if src[j] == "\\":
                    out[j] = " "
                    if j + 1 < n and out[j + 1] != "\n":
                        out[j + 1] = " "
                    j += 2
                    continue
                if src[j] == "`":
                    out[j] = " "
                    j += 1
                    break
                if src[j] == "$" and src[j + 1 : j + 2] == "{":
                    depth = 1
                    j += 2
                    while j < n and depth:
                        if src[j] == "{":
                            depth += 1
                        elif src[j] == "}":
                            depth -= 1
                        elif src[j] == "`":
                            # nested template literal: recurse crudely
                            k = j + 1
                            while k < n and src[k] != "`":
                                if src[k] == "\\":
                                    k += 1
                                k += 1
                            for z in range(j, min(k + 1, n)):
                                if out[z] != "\n":
                                    out[z] = " "
                            j = k
                        j += 1
                    continue
                if out[j] != "\n":
                    out[j] = " "
                j += 1
            i = j
            continue
        i += 1
    return "".join(out)


DECL = re.compile(r"^(const|let|var|function|class)\s+([A-Za-z_$][\w$]*)", re.M)
BANNER = re.compile(r"^/\* -+ ?([a-z ]+?) ?-*\*?/?\s*$", re.M)


def main():
    text = open(TPL, encoding="utf-8").read()
    body, base = main_script(text)
    clean = strip_noise(body)
    lines = clean.split("\n")
    raw_lines = body.split("\n")

    # section banners
    sections = []
    for i, ln in enumerate(raw_lines):
        m = re.match(r"^/\* -{3,}\s*(.+?)\s*-*\*?/?\s*$", ln)
        if m and not ln.strip().startswith("/* ---- "):
            name = m.group(1).rstrip("-").strip()
            if name and len(name) < 30:
                sections.append((i, name))

    def section_of(i):
        cur = "preamble"
        for si, nm in sections:
            if si <= i:
                cur = nm
            else:
                break
        return cur

    # top-level declarations (column 0 only)
    decls = []
    for i, ln in enumerate(lines):
        m = DECL.match(ln)
        if m:
            decls.append((i, m.group(1), m.group(2), section_of(i)))

    names = {d[2] for d in decls}

    print(f"main <script> body: lines {base}–{base + len(raw_lines) - 1} "
          f"({len(raw_lines)} lines)")
    print(f"top-level declarations: {len(decls)}\n")

    bysec = {}
    for i, kind, name, sec in decls:
        bysec.setdefault(sec, []).append((i + base, kind, name))
    for sec in bysec:
        print(f"  [{sec}]")
        for ln, kind, name in bysec[sec]:
            print(f"      {ln:>5}  {kind:<8} {name}")
    print()

    # --- the part that matters: top-level (depth-0) references ---
    # Walk the cleaned source tracking brace depth. A reference to a top-level
    # name while depth == 0 and not inside a function body is evaluated
    # immediately, so whatever it names must already exist.
    risky = []
    for i, kind, name, sec in decls:
        ln = lines[i]
        # the initialiser text on the declaration line
        eq = ln.find("=")
        if eq < 0:
            continue
        init = ln[eq + 1 :]
        # does the initialiser start a function? then body refs are deferred
        is_fn = bool(re.match(r"\s*(\(|[A-Za-z_$][\w$]*\s*=>|function|async)", init))
        arrow = "=>" in init
        for other in names:
            if other == name:
                continue
            if re.search(r"\b%s\b" % re.escape(other), init):
                # a reference inside an arrow/function body is deferred
                deferred = is_fn or arrow
                if not deferred:
                    risky.append((i + base, name, other))

    print("immediate (non-deferred) top-level cross-references:")
    if not risky:
        print("  none — every top-level initialiser is a literal or a function")
    else:
        for ln, a, b in risky:
            print(f"  line {ln}: {a} evaluates {b} at load time  -> {b} MUST come first")
    print()

    # statements executed at top level that are not declarations
    print("top-level executable statements (run at load time):")
    found = False
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s or s.startswith("/*") or s.startswith("*") or s.startswith("//"):
            continue
        if DECL.match(ln):
            continue
        if re.match(r"^[A-Za-z_$][\w$]*\s*\(", ln) or ln.startswith("document.") \
           or ln.startswith("window.") or ln.startswith("if(") or ln.startswith("if ("):
            print(f"  {i + base:>5}  {raw_lines[i].strip()[:90]}")
            found = True
    if not found:
        print("  none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
