#!/usr/bin/env python3
"""
bijoy2unicode.py — convert legacy Bijoy/SutonnyMJ ANSI text to Unicode Bengali.

Why this exists
---------------
Every Bangladesh Bank / BSCS notice PDF embeds a legacy 8-bit Bengali font with
no ToUnicode map, so pdfplumber returns the raw byte-for-byte ANSI string:
"evsjv‡`k e¨vsK" instead of "বাংলাদেশ ব্যাংক". Digits and Latin survive (which is
why roll ranges were always readable); the Bangla needs real conversion.

What makes it non-trivial — three ordering rules, not a flat lookup:
  1. ি (i-kar) is stored BEFORE its consonant:  "wgicyi" = w g ... but renders
     "মিরপুর", i.e. the sign moves after the consonant cluster.
  2. ে (e-kar) is also pre-base, and ে + া collapses into ো:  "†ivW" = "রোড".
  3. © is a reph: it is written after the consonant but encoded before it in
     Unicode, so "Kvh©" = "কার্য" swaps the pair:  য + র্  ->  র্ + য.
  4. ্র (Ö), ্য (¨) and the hasanta ligatures are post-base and map in order.

Usage
    python3 bijoy2unicode.py "evsjv‡`k e¨vsK"
    python3 bijoy2unicode.py --file notice.txt
    from bijoy2unicode import convert
"""

from __future__ import annotations

import re

import sys

# --------------------------------------------------------------------- tables
# Single characters. Order does not matter; longest-match is handled below.
CONSONANTS = {
    "K": "ক", "L": "খ", "M": "গ", "G": "ঘ", "Ng": "ঙ",
    "P": "চ", "C": "ছ", "R": "জ", "J": "ঝ", "\\N": "ঞ",
    "U": "ট", "V": "ঠ", "W": "ড", "X": "ঢ", "N": "ণ",
    "Z": "ত", "\\^": "থ", "`": "দ", "a": "ধ", "b": "ন",
    "c": "প", "d": "ফ", "e": "ব", "f": "ভ", "g": "ম",
    "h": "য", "i": "র", "j": "ল", "k": "শ", "l": "ল",
    "m": "স", "n": "হ", "o": "ড়", "p": "প", "q": "য়", "r": "র",
    "s": "ং", "t": "ট", "u": "ু", "v": "া", "w": "ি", "x": "ী",
    "y": "ু", "z": "ু",
}
INDEPENDENT = {
    "A": "অ", "B": "ই", "D": "উ", "E": "ঈ", "F": "উ", "H": "ঊ",
    "I": "ঋ", "O": "এ", "S": "ষ", "T": "থ", "Q": "ছ",
}
SIGNS = {
    "v": "া", "w": "ি", "x": "ী", "y": "ু", "u": "ু", "z": "ু",
    "…": "ৃ", "ƒ": "ৃ", "‚": "ূ", "„": "ৃ",
}
LIGATURES = {
    "Ö": "\u09CD\u09B0",   # ্র  (ra-phala)
    "¨": "\u09CD\u09AF",   # ্য  (ya-phala)
    "©": "\u09B0\u09CD",   # র্  (reph, needs reordering)
    "‡": "\u09C7",         # ে  (pre-base)
    "†": "\u09C7",         # ে  (pre-base, before ḍa/ga/ja etc.)
    "Æ": "\u09CD\u09AC",   # ্ব
    "Ç": "\u09CD\u09B0",   # ্র
    "À": "\u09CD\u09B2",   # ্ল
    "Ø": "\u09C7\u09A8\u09CD\u09A6\u09CD\u09B0",  # েন্দ্র
    "ð": "\u09C7\u09A8\u09CD\u09A6\u09CD\u09B0",
    # conjunct glyphs that ship as one ANSI byte
    "Á": "\u099C\u09CD\u099E",          # জ্ঞ
    "ß": "\u09AA\u09CD\u09A4",           # প্ত
    "ô": "\u09B7\u09CD\u09A0",          # ষ্ঠ
    "Î": "\u09A4\u09CD\u09B0",          # ত্র
    "µ": "\u0995\u09CD\u09B0",          # ক্র
    "š": "\u09A8\u09CD\u09A4",          # ন্ত
    "Í": "\u09A4",                      # ত (after ন্ত)
    "¢": "\u09A8\u09CD\u09A8",          # ন্ন
    "£": "\u09B7\u09CD\u09A0",          # ষ্ঠ
    "¤": "\u09B7\u09CD\u09A3",          # ষ্ণ
    "¤^": "\u09AE\u09CD\u09AC",         # ম্ব
    "\u201d": "\u099A\u09CD",            # চ্  (D”P = উচ্চ)
    "\u203a": "\u09A8\u09CD",           # ন্  (‡g›U = মেন্ট)
    "\u00f7": "\u09B8\u09CD\u099F",         # স্ট  (Bbw÷wUDU = ইনস্টিটিউট)
    "¥": "\u09B2\u09CD\u09B2",          # ল্ল
    "§": "\u09B9\u09CD\u09AF",          # হ্য
    "¡": "\u0999\u09CD\u0997",          # ঙ্গ
    "£": "\u09B7\u09CD\u09A0",
    "ø": "\u09CD\u09B2",               # ্ল  (j+ø = ল্ল)
    "™": "\u099F\u09CD\u09AF",          # ট্য
    "•": "\u09A8\u09CD\u09A6",          # ন্দ
    "¿": "\u0995\u09CD\u09B7",          # ক্ষ
    "¾": "\u0995\u09CD\u09B7",
}
PUNCT = {
    "|": "।", "\\|": "।", "&": "ও", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "—", "\u00a0": " ",
}
DIGITS = {chr(0x30 + i): "০১২৩৪৫৬৭৮৯"[i] for i in range(10)}

PREBASE = {"\u09C7", "\u09BF"}          # ে and ি
HASANTA = "\u09CD"
VOWEL_SIGNS_ALL = set("ািীুূৃৢৣোৌ") | {"\u09C7", "\u09BF"}


def _tokens(s: str) -> list[str]:
    """Greedy longest-match tokenisation into Unicode fragments."""
    keys = sorted(set(list(CONSONANTS) + list(INDEPENDENT) + list(SIGNS) +
                      list(LIGATURES) + list(PUNCT) + list(DIGITS)),
                  key=len, reverse=True)
    out, i = [], 0
    while i < len(s):
        for k in keys:
            if s.startswith(k, i):
                out.append(
                    CONSONANTS.get(k) or INDEPENDENT.get(k) or SIGNS.get(k)
                    or LIGATURES.get(k) or PUNCT.get(k) or DIGITS.get(k) or k
                )
                i += len(k)
                break
        else:
            out.append(s[i])
            i += 1
    return out


LATIN_RUN = re.compile(r"[A-Za-z0-9]+(?:[.@/_][A-Za-z0-9]+)+")
VOWEL_START = "ািীুূৃৢৣোৌ"


def convert(s: str) -> str:
    """
    Convert one line of Bijoy ANSI text to Unicode Bengali.

    Latin runs that look like an email, URL or web address are shielded first:
    the byte range overlaps, so "info.bscs@bb.org.bd" would otherwise be mangled
    into plausible-looking Bangla ("বরবপরুরটসবহট...").
    """
    if not s:
        return ""
    shielded: list[str] = []

    def _stash(m):
        shielded.append(m.group(0))
        return chr(0xE000 + len(shielded) - 1)

    work = LATIN_RUN.sub(_stash, undouble(s))
    toks = _tokens(work)
    out: list[str] = []
    i = 0
    while i < len(toks):
        t = toks[i]

        # ---- rule 1+2: pre-base vowel signs move after the consonant cluster
        if t in PREBASE:
            j = i + 1
            cluster = ""
            # consonant [+ hasanta + consonant]* , plus post-base ্র / ্য
            if j < len(toks) and toks[j].strip() == "" and j + 1 < len(toks) and _is_consonant(toks[j + 1]):
                j += 1                      # skip the stray space, keep the cluster
            while j < len(toks):
                if _is_consonant(toks[j]):
                    cluster += toks[j]
                    j += 1
                    if j < len(toks) and toks[j] == HASANTA and j + 1 < len(toks) and _is_consonant(toks[j + 1]):
                        cluster += HASANTA
                        j += 1
                        continue
                elif toks[j] in ("\u09CD\u09B0", "\u09CD\u09AF") and cluster:
                    cluster += toks[j]
                    j += 1
                break
            if cluster:
                # ে + া  ->  ো   (also ে + ৗ -> ৌ)
                if t == "\u09C7" and j < len(toks) and toks[j] == "\u09BE":
                    out.append(cluster + "\u09CB")
                    i = j + 1
                elif t == "\u09C7" and j < len(toks) and toks[j] == "\u09D7":
                    out.append(cluster + "\u09CC")
                    i = j + 1
                else:
                    out.append(cluster + t)
                    i = j
                continue
            out.append(t)
            i += 1
            continue

        # ---- rule 3: reph.  <consonant> + র্  ->  র্ + <consonant>
        if t == "\u09B0\u09CD" and out and _is_consonant(out[-1]):
            cons = out.pop()
            out.append("\u09B0\u09CD" + cons)
            i += 1
            continue

        out.append(t)
        i += 1

    res = "".join(out)
    # Bijoy writes independent vowels as base+sign pairs; Unicode has single glyphs
    for a, b in (("\u0985\u09BE", "\u0986"),   # অ + া  -> আ
                 ("\u0987\u09BF", "\u0988"),   # ই + ি  -> ঈ
                 ("\u0989\u09C1", "\u098A"),   # উ + ু  -> ঊ
                 ("\u098B\u09C3", "\u098B"),   # ঋ + ৃ  -> ঋ
                 ("\u098F\u09C7", "\u098F")):  # এ + ে  -> এ
        res = res.replace(a, b)
    res = res.replace(HASANTA + HASANTA, HASANTA)
    # extraction sometimes splits a cluster from its vowel sign: "পধ্র ান"
    for vs in VOWEL_START:
        res = res.replace(" " + vs, vs)

    for i, original in enumerate(shielded):
        res = res.replace(chr(0xE000 + i), original)
    return undouble(res)


def _is_consonant(tok: str) -> bool:
    return bool(tok) and tok[0] in "কখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়ৎংঃঁ"


def undouble(s: str) -> str:
    """
    Collapse glyph-duplicated bold runs produced by the PDF's text layer.

    "মমাাততুয়ুয়াাইইলল" -> "মাটুয়াইল". Only runs of 2+ consecutive doubled
    characters are collapsed, so ordinary Latin double letters ("College",
    "Committee") survive untouched.
    """
    out, i = [], 0
    while i < len(s):
        j, pairs = i, 0
        while j + 1 < len(s) and s[j] == s[j + 1]:
            j += 2
            pairs += 1
        if pairs >= 2:
            out.append(s[i:j:2])
            i = j
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def to_bengali_digits(s: str) -> str:
    return "".join(DIGITS.get(c, c) for c in s)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--file":
        for line in open(sys.argv[2], encoding="utf-8", errors="replace"):
            print(convert(line.rstrip("\n")))
    elif len(sys.argv) > 1:
        print(convert(" ".join(sys.argv[1:])))
    else:
        print(__doc__)
