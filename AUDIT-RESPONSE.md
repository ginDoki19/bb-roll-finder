# Audit response — 12 Nov 2026

Covers every finding in the external audit of the live site and the
`bb-notice.zip` snapshot. The audit's own snapshot stamp
(`generated 2026-11-12T03:24:54Z`) matched this tree exactly, so every line
number and quotation in it was current.

**39 actioned · 4 rejected as incorrect · 5 declined with reasons · 7 confirmed
no-ops.** Three further bugs were found while implementing and fixed; they were
not in the audit.

Verification: `selftest` ALL PASS · `uitest` 139/139 · `test_fetch` 9/9 ·
12 fired-then-restored negative tests · real print-to-PDF render reviewed.

---

## 1. Rejected — the audit is wrong or it was already fixed

Each was checked against the code before being set aside.

| # | Audit claim | Verified reality |
|---|---|---|
| **6.2** | `20261017_bb_81` has no `closing`, so it sits "Open" forever | It has `closing: "13/11/2026"`. No bug. |
| **5.5** | `o.steps` is still computed and would render even when `details` exists | `results.js:53` already returns `{…, steps:null}` whenever a headline is present. Already defensive. |
| **7.5** | "Show all" does not clear the saved job preference | The button is `data-job=""`; `app.js:28` calls `localStorage.removeItem("bb-job")`. Already clears. |
| **§3.1** | The placeholder roll `১০৫৪৩২` is fake; use `১০০০০১` | `105432` is **real** — it resolves through the centre ranges of notices 86/2026 and 357/2026 to a genuine seat card, which is why `uitest` asserts `মোল্লা` appears for it. The proposed replacement `100001` lands in the *same two* centre ranges, so the change is a no-op that would also break that assertion. Placeholder kept. |

Confirmed no-ops, agreeing with the audit's own conclusion: **7.9**
(reduced-motion guard works), **7.10** (`lang` set synchronously), **8.4**
(JSON roll arrays fine), **8.7** (no orphan fonts), **8.8** (minification not
worth it), **P3-10** (documentation only), **5.7** (`ocrProv` ≠ `manualProv`
must stay distinct — preserved).

## 2. Declined, with reasons

| # | Proposal | Why not |
|---|---|---|
| **P3-2a** | Drop `lang` from the manifest | `lang` declares the language of the manifest's *own* strings (`name`, `short_name`, `description`) — all English. It is not the UI language. `"lang": "en"` is correct and stays. |
| **P3-2b** | Drop `theme_color` from the manifest | The audit says `<meta name="theme-color">` covers it. It does not: manifest `theme_color` drives the Android splash screen and task-switcher chrome, which the meta tag never reaches. Stays. |
| **5.2** | Unify `নোটিশ` / `বিজ্ঞপ্তি` sitewide | Not synonyms here. `নোটিশ` is any posting; `বিজ্ঞপ্তি` is specifically a recruitment circular, which is why it is the `circular` badge. BB uses both this way. Unifying would destroy a real distinction. |
| **6.1** | Backfill the 4 missing `noticeNo` values | Not derivable and not safe to guess. The id number is **not** the notice number — `20260929_bscs_1` carries `319/2026`, so deriving from the id would be wrong ~11% of the time. The four PDFs are scans whose text layer is mojibake or absent. An official notice number is a citable identifier; publishing a guessed one is worse than publishing none. |
| **§3** | `লাইট`/`ডার্ক` → `হালকা`/`গাঢ়` | The audit itself concludes the transliterations are right. Android, iOS and Facebook Bengali all use them. |

## 3. Shipped

### Safety — the one finding with real-world consequences

**P1-1 · OCR low-confidence rolls were served as confirmed matches.**
`ocrChecks.lowConfidence` was read by *zero* lines of JavaScript. A candidate
searching `221034`, `221077` or `201246` got a full green "you passed" card —
venue, time, next steps — with nothing saying the scan was unclear at exactly
their number. Notice `20261109_bb_419` is the stark case: `agreeing: 1` of
`total: 2`.

Those rolls stay in `rolls[]` deliberately (a candidate searching a number the
notice really contains must not be told it is absent), so the disclosure is a
render-time panel instead: `.prov.warn` above `provenance(n)`, tinted with the
same `--md-tertiary-container` as `.det.warn`, with a dark left rule. It
survives to print with a border.

Guarded four ways: the rolls must stay in `rolls[]`; the front-end must read
the field (word-boundary match, so renaming it to `lowConfidenceX` fails); the
block must be *called* from the card, not merely defined; and `uitest` asserts
the warning appears for `221034` and does **not** appear for `200983` in the
same notice.

### Correctness

| # | Fix |
|---|---|
| **P1-2** | `JOB_LABEL()` collapses a multi-job notice to `280 + 7`, full list in `title=`. Four call sites. |
| **P2-1** | `clock()` now returns `BN(out)`, so a malformed time still localises its digits instead of printing ASCII mid-sentence. |
| **P2-2** | `parse_centres_text` can no longer emit a centre with an empty name; `BN_INSTITUTION` gained `ভবন ‑ হল ‑ ক্যাম্পাস ‑ প্রতিষ্ঠান ‑ মিলনায়তন ‑ অডিটোরিয়াম ‑ বিশ্ববিদ্যালয় ‑ মাদ্রাসা`. |
| **P2-3** | `dayDiff()` uses UTC epoch days, so the gap between two calendar dates is never 23 or 25 hours. |
| **P4-1** | `_tkey()` normalises a clock label before sittings are compared — `"10:00 AM"` and `"10:00AM"` no longer start two batches. |
| **P4-2** | `safeHref()` rejects a protocol-relative `//evil.example/x.pdf`. |
| **P4-3** | `#srstatus` re-announces in the new language instead of holding the old sentence until the next keystroke. |
| **P3-7** | `parse_listing` checks outcome words before exam-type words, so "Selected Candidate List of the MCQ Examination" is no longer filed as MCQ. |
| **P3-8** | `অরিজিনেশন` → `অরিগেশন`. |
| **5.1** | `noteBn` time ranges match the structured rows' spaced en-dash form. |
| **5.4** | The sitting panel's eyebrow is now `yourSitting`, distinct from the `reportingTime` cell below it; the cell also runs through `clock()`. |

### Bengali — 19 strings, then a second fluency pass

Idiom (`ocrProv`, `manualProv`, `scannedWarn`, `tooShort`, `notFoundTitle`,
`notFoundBody`, `nextViva[1]`, `congratsOffer`, `congratsGeneric`,
`disambigWhy`, `nextPrimary[0]`, `nextSeat[3]`, `pastNotices`), word order
(`srFound`, `srAmbig`, `cdToday`, `cdTomorrow`, `cdDays`, `cdPast` — Bengali
puts the time adverb first), register (`completed` `শেষ হয়েছে` → `সম্পন্ন`, so
status badges are all noun phrases), and `hideMap`, `statRolls`, plus
`KIND.viva.labBn` `মৌখিক` → `ভাইভা` and `KIND.scanned.labBn` `স্ক্যান` →
`স্ক্যান করা`.

The biggest win is the three provenance strings — the calque
`কম্পিউটার দিয়ে পড়া` became `স্বয়ংক্রিয়ভাবে`, the filler `আসলে` is gone, and the
run-on sentences are split. That block is where a candidate decides whether to
trust the result enough to travel.

**A second pass followed**, because the first one still read as translated.
The diagnosis and the full before/after table are in `BENGALI-REWRITE.md`.
Short version: participle-style headline fragments were given finite verbs,
তৎসম register was dropped for everyday words, run-ons were split, and the
OCR count became concrete ("নোটিশে লেখা আছে মোট ৩৩৪টি রোল, আমরাও ততগুলোই
পেয়েছি") instead of an abstract "total number". One audit instruction was
reverted: it told me to replace `কম্পিউটার দিয়ে পড়া` with `স্বয়ংক্রিয়ভাবে`,
which made the register *more* bureaucratic, not less.

**A third pass then rewrote the Bengali against a corpus** — Prothom Alo,
Daily Star Bangla and Amar Desh, including eight Prothom Alo চাকরি stories
about Bangladesh Bank's own notices. That pass found the real offender was
not copy but two formatters: every Bengali date printed as `১৬/১১/২০২৬` and
every time as `সকাল ১০:০০`. Both now follow the papers (`১৬ নভেম্বর ২০২৬`,
`সকাল ১০টা`, `দেড়টা` for 1:30). It also reversed my own earlier
over-correction: `রয়েছে`, `কমপক্ষে`, `সম্পন্ন`, `তালিকাভুক্ত` and `আসন্ন` are
normal journalism, and banning them was wrong. Full record in
`BENGALI-REWRITE.md`.

### Discovery

JSON-LD `WebSite` + `SearchAction` (**`ROADMAP.md` claimed this had shipped on
11 Nov when only robots+sitemap had — the row is now corrected and the claim is
true**), `canonical`, `og:url`/`og:image`/`og:locale`, `twitter:card`,
`apple-mobile-web-app-title`, `/career` dropped from `sitemap.xml`,
`Disallow: /meta/ /data/ /career` in `robots.txt` with `/notices/` left
crawlable on purpose.

### Performance and build

| # | Fix |
|---|---|
| **8.2** | The two Bengali 600-weight faces are preloaded. Needed in *both* locales — centre and post names in the data are Bengali even when the interface is English. |
| **8.1** | `icon-512.png` **261,933 B → 6,483 B** (see §4). |
| **8.6** | CSP in `_headers`. `'unsafe-inline'` is unavoidable for inlined CSS/JS, but `default-src 'self'` denies every third-party origin and `frame-src` pins the embed to Google Maps. |
| **P3-4** | The service-worker cache name is a SHA-1 of the inlined CSS+JS. Impossible to forget, impossible to bump spuriously. The selftest guard now asserts the name matches the shipped bundle — strictly stronger than checking a hand-typed string moved. |
| **P3-5** | `generated` is rounded to the day, so two builds of identical data are byte-identical. |
| **8.3** | The roll filter is debounced 60 ms; a 1,037-chip grid no longer rebuilds on every keystroke. |
| **8.5** | The footer shows `12 November 2026`, not `২০২৬-১১-১২T০৩:২৪:৫৪Z`. |

### UX

`/` focuses the search (and autofocus is gated on `(hover: hover) and
(pointer: fine)`, so a phone keyboard never covers the page); the map toggle
carries `aria-expanded`/`aria-controls` and the region is labelled; an offline
map shows an explanation instead of a blank grey rectangle; the matched roll
chip is tinted and scrolled into view — it had a `.hit` style that **never
applied**, because every caller passed `hit=null`; the confirm-before-you-travel
line is a callout beside the search instead of the third grey line of the
footer; and result cards have a Share button.

Print was reviewed as a real PDF, not a screenshot. The printed card now
carries the PDF's absolute URL (resolved at render time, not in a
`beforeprint` handler that programmatic printing never fires), the masthead no
longer eats an entire first sheet, and the low-confidence warning keeps a
border on paper.

## 4. Found while implementing — not in the audit

**A. The `jobId` of `20261029_bb_372` was truncated.** The listing's job column
is a narrow cell that cuts off: it held `280, 282, 289, 294, 295, 296,` — six
ids and a dangling comma — while the notice's own title spells out
`(Job Id -280, 282, 289, 294, 295, 296, 299 & 300)`. Two jobs were missing.
Candidates holding 299 or 300 would never have seen their job on the card, and
the disambiguation picker keys on exactly this field. `parse_listing` now takes
whichever source names more jobs.

**B. The app icon was off-brand and mis-shaped.** It was cyan `#0098ec` on navy
while the site's brand is green `#00694b`, and it was a rounded-square badge
floating on a dark field — yet the manifest declares `purpose: "any maskable"`.
Android would have applied its own mask and produced a rounded square inside a
circle. The set was redrawn full-bleed in the brand green with the glyph inside
the maskable safe zone (max radius 74% of half-canvas, against the 80% limit).
As a side effect it solved 8.1 far past target: **262 KB → 6.5 KB**.
`og-card.png` was drawn to match, using the project's own Noto faces.

**C. Bengali sentences ended in a Latin full stop.** `provenance()` hardcoded
`</a>.`, so every Bengali provenance note closed with `.` instead of `।`. Now a
`stop` dictionary key. (The first draft of the new warning also repeated the
link text in its own body sentence — caught on visual review and fixed.)

## 5. Still open

Three notices have rolled off the BB portal and exist in no local snapshot:
`20260505_bscs_159`, `20260506_bscs_163`, `20260621_bscs_217`. Their URLs are
recorded; fetching them is a separate decision.
