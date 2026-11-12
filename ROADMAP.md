# Full repo audit — findings and what to build next

> ## ✅ Audit response SHIPPED — 12 Nov 2026
> External audit of the live site + the zip snapshot. 39 findings actioned,
> 4 rejected as incorrect, 5 declined with reasons. Highlights: OCR
> low-confidence rolls are now disclosed on the result card (they were being
> served as confirmed matches), multi-job Job IDs collapse to `280 + 7`, 19
> Bengali strings rewritten, the service-worker cache name is derived from a
> hash of the bundle, the app icon was rebuilt on-brand and full-bleed
> (262 KB → 6.5 KB), and the JSON-LD below finally exists.
> Verified: selftest **ALL PASS**, uitest **139/139**, test_fetch **9/9**,
> 12 fired-then-restored negative tests. Full write-up: `AUDIT-RESPONSE.md`.
>
> ## ✅ Items 1–8 SHIPPED — 11 Nov 2026
> Bengali numerals, network-first service worker, exam countdown, ISO dates +
> status badges + archive, both scanned notices transcribed (28 rolls), LICENSE,
> robots/sitemap, `/*` security headers. Verified: selftest **ALL PASS**,
> test_fetch **7/7**, browser regression clean, no JS errors.
> Still open: **item 9** (`ocr_assist.py` with Gemini) — only pays off when the
> next image-only scan appears.

Audited 11 Nov 2026 against the live site at <https://bb-roll-finder.pages.dev>.
Everything below was verified by running it, not by reading code.

---

## Scorecard

| Area | State |
|---|---|
| Parsing / data pipeline | ✅ solid — delta-encoded rolls, 80 KB page, selftest covers integrity |
| Hosting | ✅ done — Cloudflare Pages, 0.30 s, 20.6 KB over the wire, offline works |
| Fetch reliability | ⚠️ manual by design; CAPTCHA re-solve every ~2 weeks (accepted) |
| **Bengali numeral input** | 🔴 **broken — see P0-1** |
| Freshness for repeat visitors | 🟠 stale-by-one-visit — see P0-2 |
| Scanned notices | 🟠 2 notices, 28 rolls, currently unsearchable — see P1-1 |
| Date awareness | 🟠 none at all — see P1-2 |
| Licence / legal | 🟡 no LICENSE, no disclaimer in repo |
| Discoverability | 🟡 no robots.txt, no sitemap, no structured data |

Verified **not** broken (checked, don't worry about these): notice sort order is
correct (`build_data.py` splits DD/MM/YYYY into a `(yy,mm,dd)` tuple — not a string
compare); no secrets in the repo; PDFs serve fine; `_headers` is applied.

---

# 🔴 P0-1 · Bengali numerals silently return nothing

**The bug.** `app.template.html` line 300:

```js
const raw = $("#roll").value.replace(/\D/g, "");
```

`\D` strips everything that is not an **ASCII** digit. Bengali digits `০১২৩৪৫৬৭৮৯`
are not ASCII, so they are all stripped and the search runs on an empty string.

**Reproduced live just now:**

| Typed | Result |
|---|---|
| `105432` | ✅ মোল্লা কলেজ |
| `১০৫৪৩২` | ❌ **nothing** |
| `৫০০০০৬` | ❌ **nothing** |

**Why this matters more than it looks.** Your own UI renders every number in Bengali
(`const BN = s => ...` on line 173), and the official PDFs print roll numbers in
Bengali too — notice 83/2026 lists `৫০১৯৯১, ৫০৪০৫২, ৫০০৪১৯ …`. So a candidate reading
the PDF, or copying a number off your own page, types Bengali digits and gets a blank
box. It does not say "not found" — it just does nothing, which reads as "my roll
isn't listed."

**Fix** — normalise before stripping (also covers Arabic-Indic, and full-width digits
from some Android keyboards):

```js
const DIGITS = { "০":"0","১":"1","২":"2","৩":"3","৪":"4",
                 "৫":"5","৬":"6","৭":"7","৮":"8","৯":"9" };
const toAscii = s => String(s).replace(/[০-৯]/g, d => DIGITS[d]);
const raw = toAscii($("#roll").value).replace(/\D/g, "");
```

Three lines. Highest value-per-byte change in the whole repo.

---

# 🟠 P0-2 · Returning visitors see yesterday's data once

`sw.js` is cache-first. On a repeat visit the browser paints the cached page, *then*
fetches the update in the background. So the visit after you publish a new notice
shows the **old** page; the one after that is correct.

For an exam site that is a real failure: someone checks the morning a seat plan drops,
gets "not found", and concludes they aren't listed.

**Fix** — network-first for the HTML only, cache as fallback:

```js
// in sw.js fetch handler, for navigation/HTML requests:
e.respondWith(
  fetch(e.request)
    .then(r => { caches.open(CACHE).then(c => c.put(e.request, r.clone())); return r; })
    .catch(() => caches.match(e.request).then(r => r || caches.match("./index.html")))
);
```

Online users always get fresh data. Offline users still get the cached copy — the
airplane-mode behaviour you tested is preserved. Bump `CACHE` to `bb-roll-v2` when
you ship it.

---

# 🟠 P1-1 · The two scanned notices

## What they actually contain

I rendered both PDFs at 300 DPI and read them.

**`20261102_bb_83_1793613569.pdf`** — Offer Letter, Assistant Director (Eng-Electrical),
Job ID 269. Contains **11 roll numbers, in Bengali digits**:

```
৫০১৯৯১  ৫০৪০৫২  ৫০০৪১৯  ৫০৩৯৩৬  ৫০২৮৮৩  ৫০২৫৪৬
৫০১৪৪৩  ৫০৪১০৫  ৫০৩৩৮৭  ৫০০০০৪  ৫০০৯০৪        = মোট ১১ জন
```

**`20261029_bb_372_1793248807.pdf`** — Primarily selected candidates, SPCBL, 10 post
categories. Contains **17 roll numbers, in ASCII digits**, grouped by post:

| Post | Rolls |
|---|---|
| সহকারী ব্যবস্থাপক (উৎপাদন) | 3104 |
| সহকারী ব্যবস্থাপক (জেনারেল) | 104171 |
| টেকনিশিয়ান (মেকানিক্যাল) | 479 |
| জুনিয়র টেকনিশিয়ান (অরিজিনেশন) | 801 |
| জুনিয়র টেকনিশিয়ান (উৎপাদন) | 1354, 1833 |
| জুনিয়র টেকনিশিয়ান (গবেষণা ও মান নিয়ন্ত্রণ) | 924 |
| জুনিয়র টেকনিশিয়ান (মেকানিক্যাল) | 3067 |
| জুনিয়র কেয়ারটেকার (পিয়ন) | 8339 |
| জুনিয়র কেয়ারটেকার (ক্লিনার) | 9721, 9702, 9422, 8861, 8348, 8076 |
| জুনিয়র কেয়ারটেকার (মালি) | 9552, 9274 |

## Why the existing text layer is useless

Both PDFs **do** carry a text layer — 834 and 1,305 characters. It is garbage:

```
\ / <ft,ailC~-1 ~~ / (~ <UT~~ i5f<I" <ft~~)
fi {rifa3falB fart3` anoiTmF (anemtFrty) ffi8
```

The producer string on the second one is **`EPSON Scan`**. Someone scanned a Bengali
document and the scanner ran *English* OCR over it, emitting Latin gibberish in
WinAnsiEncoding with no ToUnicode map. It can never be decoded — the Bengali was
thrown away at scan time. Your `_looks_scanned()` heuristic correctly refuses to trust
it. Nothing to salvage; it must be re-OCR'd from the image.

## The number that should drive the decision

**28 roll numbers. Total. Across both notices.**

That reframes everything. Here is the honest comparison:

| Approach | Setup burden | Accuracy here | Cost | Verdict |
|---|---|---|---|---|
| **Type them into `overrides.json`** | none, 5 minutes | **100 %** | free | ✅ **do this now** |
| Tesseract locally + `ben` traineddata | install on Windows, ~250 MB | digits ~97 %, Bengali text ~85 % | free | heavy for 28 numbers |
| OCR.space API | API key, no card | ✗ Bengali is **not** in its language list; measured 11.2 % character error rate on Bengali [¹] | 25k/mo free | rejected |
| Google Cloud Vision | GCP project + **billing enabled** | 98–99 % | 1,000/mo free | card required, rejected |
| **Gemini Flash (AI Studio)** | API key, **no card** | excellent on Bengali + digits | ~500–1,500 req/day free | ✅ best automated option |

[¹] fastocr.org comparison, Nov 2026; OCR.space's own language table omits Bengali.

## Recommended design — three tiers, human in the loop

**Tier A — ship today.** Extend `meta/overrides.json` to accept a roll list. The file
already overrides titles, venues and centres; teach `build_data.py` to also read:

```jsonc
"20261102_bb_83_1793613569.pdf": {
  "kind": "selected",
  "rollSource": "manual",
  "verified": "2026-11-11",
  "groups": [
    { "post": "সহকারী পরিচালক (প্রকৌশল-তড়িৎ)",
      "rolls": [501991, 504052, 500419, 503936, 502883,
                502546, 501443, 504105, 503387, 500004, 500904] }
  ]
}
```

That makes both notices searchable immediately, with zero new dependencies and no
chance of a transcription engine inventing a digit.

**Tier B — optional helper.** `tools/ocr_assist.py`: renders the PDF page with
`pypdfium2` (already a dependency — no new install), sends it to Gemini Flash with a
strict prompt, and writes a **draft** block into `meta/overrides.draft.json`. It never
writes to the live file. You eyeball 11 numbers against the PDF, paste, done. Turns a
10-minute typing job into a 30-second check.

**Tier C — the rule.** *Never auto-publish unreviewed OCR.* One wrong digit here means
a candidate who was selected reads "not found", or vice versa. There is no error rate
low enough to justify that unattended. The `verified` date in the override is the audit
trail.

Also needed either way: mark these notices `"ocr": "manual"` so the UI can show
*"typed from a scanned notice — confirm against the official PDF"* next to the result.
Honesty here costs nothing and protects you.

---

# 🟠 P1-2 · No date intelligence anywhere

Every notice already carries `published`, `closing` and `examDate`. The client **never
compares them to today** — it only prints them as strings (lines 248, 399, 400). No
status, no countdown, no archiving.

Your screenshot of the portal shows exactly why this matters: the Close Date column is
rendered in red because it is the operative field.

## Don't delete expired notices

You suggested GitHub or the site could remove them after the close date. Three reasons
not to:

1. **Deleting from git does not reclaim anything.** The blob stays in history forever.
   The repo keeps growing either way.
2. **People look backwards.** "Which centre was I assigned?", "what was the viva date?"
   — these get asked after the fact, during appeals and document checks.
3. **For a seat plan, `closing` *is* the exam date.** Notice 86/2026 closes 13/11/2026,
   the day of the exam. Deleting on the close date removes it exactly when traffic peaks.

**Growth maths, so you can stop worrying:** 9 notices, 2.9 MB, averaging 326 KB, over
roughly 6 months → ≈5 notices and 1.6 MB per month → **~20 MB/year**. Cloudflare Pages
allows 20,000 files and 25 MB *per file*. You have years of headroom. Archiving is a
**UI** problem, not a storage problem.

## Build this instead — status computed in the browser

Add ISO fields at build time (`build_data.py`), because `"13/11/2026"` can't be
compared in JS:

```python
def iso(d):                      # "13/11/2026" -> "2026-11-13"
    if not d: return None
    dd, mm, yy = d.split("/")
    return f"{yy}-{mm}-{dd}"

notice["examDateISO"] = iso(parsed.get("examDate"))
notice["closingISO"]  = iso(row.get("closing"))
```

Then derive status client-side from `new Date()`:

| Condition | Badge | Treatment |
|---|---|---|
| exam date is today | 🔴 **আজ পরীক্ষা** | pinned to top, red |
| exam within 7 days | 🟡 **২ দিন বাকি** | highlighted |
| future | 🟢 আসন্ন | normal |
| past `closing` | ⚪ সম্পন্ন | dimmed, moved to a collapsed **Archive** section, **still searchable** |

**The key property: this costs zero maintenance.** Because it is computed from the
device clock at page load, the site re-sorts itself every single day with no fetch, no
rebuild, no deploy. That is the "live stat" you were describing, and it is about 25
lines of JS.

## The single highest-value addition

A countdown on the **result card**, not just the notice list:

> **আপনার পরীক্ষা আগামীকাল** — ১৩/১১/২০২৬, সকাল ১০:০০
> কেন্দ্রে পৌঁছান ৯:০০ টার মধ্যে · আর ১৮ ঘণ্টা বাকি

Someone searching their roll wants one thing: *when and where, and am I late?* You
already have `examDate`, `examWindow` and the report-by time parsed. This is pure
presentation of data you hold.

---

# 🟡 P2 · Smaller items, roughly in value order

**Add a `LICENSE` + disclaimer.** No licence file exists. MIT is fine. Add to the
README: *unofficial, not affiliated with Bangladesh Bank, every result links to the
official PDF, verify before acting.* The footer already says this; the repo should too.

**`robots.txt` + `sitemap.xml` + JSON-LD.** People will Google "বাংলাদেশ ব্যাংক সিট প্ল্যান
রোল". Right now nothing helps them find you. A 10-line sitemap and a `WebSite`
structured-data block is the cheapest reach you will ever buy.

**Security headers are only on `/index.html`.** Move `X-Content-Type-Options` and
`Referrer-Policy` to a `/*` block so the PDFs and JSON get them too. Consider a strict
`Content-Security-Policy` — the site has no external dependencies at all, so
`default-src 'self'; img-src 'self' data:` would hold, with `'unsafe-inline'` for the
inlined styles/script.

**Non-site files are published.** `parser/*.py`, `tools/*.py`, `app.template.html` and
all the `.md` files are served at public URLs (~200 KB). Harmless — the repo is public
and I verified there are no secrets — but untidy. Only fixable by moving the site into
a `public/` folder and pointing Pages at it, which costs a build step. **Low priority;
I'd leave it.**

**`icon-512.png` is 256 KB** for a 512 px icon. Running it through `oxipng`/`pngquant`
would cut it ~80 %. Cosmetic.

**A "last updated" line in the footer.** `data/notices.json` already has `generated`.
Surfacing "তথ্য হালনাগাদ: ১১/১১/২০২৬" builds trust and tells people when you last ran
the fetch — useful precisely because the fetch is manual.

---

# Don't bother with these

- **Framework migration (Astro/Next).** Already settled in `AUDIT.md`. The page is
  20.6 KB over the wire with zero JS dependencies. A framework makes it bigger.
- **A database.** 9 notices.
- **Cloud-scheduled fetching.** Settled: datacenter IPs are blocked on reputation by
  the F5 WAF before behaviour matters.
- **Pruning old PDFs.** ~20 MB/year against a 20,000-file allowance.

---

# Suggested order

| # | Item | Effort | Impact |
|---|---|---|---|
| 1 | ✅ Bengali numeral input (P0-1) | done | 🔥 fixes silent failure for Bengali typists |
| 2 | ✅ Service worker network-first (P0-2) | ~10 lines | 🔥 removes the stale-data window |
| 3 | ✅ Exam countdown on result card (P1-2) | ~30 lines | 🔥 the thing users actually came for |
| 4 | ✅ ISO dates + status badges + archive | ~40 lines | high, self-updating daily |
| 5 | ✅ Roll lists for the 2 scanned notices (Tier A) | 15 min typing | makes 28 people findable |
| 6 | ✅ LICENSE + disclaimer | 5 min | legal hygiene |
| 7 | ✅ robots/sitemap · ✅ JSON-LD *(robots + sitemap shipped 11 Nov; the JSON-LD half of this row was marked done but never written — caught by the 12 Nov audit and shipped then)* | 20 min | discoverability |
| 8 | ✅ `/*` security headers | 5 min | hygiene |
| 9 | `ocr_assist.py` with Gemini (Tier B) | ~1 h | saves time on *future* scans |

Items 1–4 are all edits to `app.template.html`, `sw.js` and `build_data.py` — one
rebuild, one `run.bat`, done.
