# UI Renovation — investigation and plan

Written 2026-11-12. No code yet. This document decides *what* we build and *why*,
so the build itself is mechanical.

---

## 1. What I actually measured

Before designing anything I pulled the numbers out of the live `data/notices.json`
(13 notices) rather than guessing.

| Measurement | Value |
|---|---|
| Notices | 13 — 5 selected, 4 circular, 2 seat plan, 2 viva |
| Total roll numbers rendered into the page | **1,401** |
| Largest single list | **1,037 rolls** (319/2026, Job 25101) |
| Second largest | 334 rolls (Job 303) |
| `index.html` | 105,871 bytes raw / 25,954 gzipped |
| Font declarations in the CSS | **zero** |
| Theme | dark only, 11 hard-coded hex values in `:root` |

Two of those numbers changed my plan.

**The overflow is worse than the screenshot shows.** You spotted it on the
334-roll notice. The 1,037-roll notice is three times longer and renders the same
way. The cause is one line — the roll list is emitted as a single comma-joined
text node inside a `<td>`, and table cells do not wrap long unbroken content, so
the cell widens until the whole *page* scrolls sideways.

**There is also an inconsistency I had not noticed:** the archive view truncates
at 60 rolls and appends "…", while the search-result view prints all of them.
Same data, two different behaviours, neither one chosen deliberately.

---

## 2. The Job ID problem is real, systematic, and the most important thing here

You are right, and it is worse than "sometimes ambiguous". I tested actual rolls
against all 13 notices:

| Roll | Matches | Which |
|---|---|---|
| 100001 | **2** | 86/2026 Job 307 (seat plan) · 357/2026 Job 26101 (seat plan) |
| 105432 | **2** | 86/2026 Job 307 · 357/2026 Job 26101 |
| 200096 | **2** | Job 303 (selected) · 357/2026 Job 26101 (seat plan) |
| 213880 | **2** | Job 303 (selected) · 357/2026 Job 26101 (seat plan) |

The reason is structural, not accidental: **every circular restarts its roll
numbering** at 100001 or 200001. So roll numbers are only unique *within a job*.
As more notices accumulate, collisions increase — this gets worse over time, not
better.

### What this means

`roll` is not a key. **`(roll, jobId)` is the key.** The current UI treats roll as
the key and shows whatever matches, which produces your screenshot 2: two
identical-looking "আপনার পরীক্ষা আগামীকাল" cards, both claiming to be the user's
exam, at two different centres, with no way to tell them apart at a glance.

That is not a cosmetic bug. A candidate could go to the wrong exam hall.

Worth noting: the official portals have the same problem and solve it the same
way — `educationboardresults.gov.bd` will not accept a roll alone, it demands
exam + year + board + roll + registration before it returns anything
[2](https://educationboardresults.com.bd/). They scope the roll. We must too.

### The fix, in order of preference

1. **Make the post and job the headline of every card.** Right now the centre
   name is the biggest text and the Job ID is a small grey pill. That is exactly
   inverted. The candidate knows which post they applied for; they do not know
   their centre — that is what they came to find out.
2. **When a search matches more than one notice, say so before showing results.**
   A short disambiguation strip: "Roll 100001 appears in 2 notices — which post
   did you apply for?" with the two posts as large tap targets. One tap filters.
3. **Remember the choice.** Store the chosen job in `localStorage`; next visit,
   that job's results sort first with a "your post" marker.
4. **Never show two cards of the same kind without a visible differentiator**
   in the first line of each.

---

## 3. Typography

There is currently **no `font-family` anywhere in the stylesheet**. Every visitor
gets their browser default, which for Bengali means Nirmala UI on Windows, Noto
Sans Bengali on Android, Bangla Sangam MN on iOS — three different typefaces with
different metrics, so the layout shifts per platform and none of it was designed.

### Options considered

| Option | Weight | Pros | Cons |
|---|---|---|---|
| **A. System stack** | 0 KB | instant, no download, works offline forever | inconsistent across platforms; Windows' Nirmala UI is weak at small sizes |
| **B. Self-hosted subset** | ~90–120 KB woff2 | identical everywhere, offline after first load, no third party | one-time download; needs subsetting |
| **C. Google Fonts CDN** | ~90 KB + DNS/TLS | easy | breaks offline PWA, third-party request, extra round trip, blocked in our own preview sandbox |

**Recommendation: B, with A as the fallback chain.**

Noto Sans Bengali is the strongest candidate — it is Google's Bengali face, the
Android system font, OFL-licensed, and covers Bengali digits ০–৯ plus Latin in one
family, which matters because our pages mix `213880` and `২১৩৮৮০` in the same line
[1](https://artbit.studio/resources/bangla-fonts)
[4](https://banglaconvertertool.com/bangla-fonts-complete-guide-to-bijoy-unicode-fonts/).
Hind Siliguri is the usual alternative and is also recommended for mixed
Bengali–Latin UI [2](https://capsai.co/blog/best-fonts-for-bengali-subtitles).

The variable font is 453 KB as TTF [10](https://fontsource.org/fonts/noto-sans-bengali/about),
but we do not need all of it. Subset to Bengali + Basic Latin + the punctuation we
use and it drops to roughly 90–120 KB in woff2 — a one-time cost, then the service
worker caches it and it never downloads again. Option C is disqualified outright:
this site is explicitly offline-capable, and a CDN font breaks that.

**Numerals need a separate decision.** Roll numbers must be scannable. I want
tabular (fixed-width) figures so columns of numbers align, and I want Latin digits
and Bengali digits to share a baseline. This is a reason to prefer one family that
does both rather than pairing two.

---

## 4. Dark mode and light mode

Current state: a single hard-coded dark palette, no `color-scheme` declaration, no
toggle, no respect for the OS setting.

### The approach

The settled 2026 pattern, consistent across every source I checked:

1. Every colour becomes a **semantic token** — `--surface-0`, `--surface-1`,
   `--text-primary`, `--text-muted`, `--border`, `--accent` — never a raw hex in a
   component rule [3](https://sivadesigner.in/blog/dark-mode-evolution-modern-web-design/).
2. Light values on `:root`, dark values under both `[data-theme="dark"]` **and**
   `@media (prefers-color-scheme: dark)`, so the OS setting is the default and an
   explicit choice overrides it.
3. `color-scheme: light dark` on the root so native controls, scrollbars and form
   fields follow the theme.
4. **A tiny blocking script in `<head>`, before the styles**, that reads
   `localStorage` and sets the attribute. Without this you get a white flash
   before the dark theme applies — the single most common implementation mistake
   [1](https://www.sitepoint.com/dark-mode-css-variables-light-dark/)
   [8](https://goilerplate.com/blog/dark-mode-without-flash).
5. A three-state toggle: **system → light → dark**, not a binary switch, so
   "follow my phone" stays reachable.

### Colour rules I will hold the design to

- **Dark surface is `#121212`-class, never pure black.** White on black is 21:1,
  which triggers halation — a glow that blurs letterforms and tires the eyes
  [1](https://superdesign.dev/styles/dark-mode).
- **Elevation by lightness, not shadow.** Cards lighter than page, overlays
  lighter than cards [5](https://m2.material.io/design/color/dark-theme.html).
- **Desaturate accents in dark mode.** Our current `--acc:#22d3ee` is a saturated
  cyan that vibrates on dark backgrounds.
- **Contrast targets:** body text ≥ 4.5:1, aiming at 7:1 in dark mode because of
  halation; non-text (borders, focus rings, badge outlines) ≥ 3:1. Critically,
  test text against the **lightest surface it can appear on**, not the page
  background [4](https://www.colorcontrast.org/blog/dark-mode-contrast-accessibility-guide/).
- **Light mode is not an inversion.** It needs its own hand-picked values.

This matters more than usual for us: a candidate checks their seat plan at 11pm
the night before an exam, on a phone, probably in bed. Dark mode is the primary
experience, not the alternate one.

---

## 5. The long-list problem

1,037 numbers cannot simply be printed. The relevant principle is progressive
disclosure — show the few things that matter first, reveal the rest on request,
and get the split right [NN/g](https://www.nngroup.com/articles/progressive-disclosure/).

For a roll list, what matters first is almost never the list. It is **"is my
number in it?"** — and the user already told us their number in the search box.

### Proposed treatment

**In a search result** — do not print the list at all. The answer is a single
statement: *"Yes — roll 213880 is on this list."* Then the context: post, job,
what happens next, when, where. The other 333 numbers are noise to this user.

**In the archive / browse view** — a collapsed summary line (`৩৩৪ roll numbers`)
that expands to:

- a **wrapping grid of chips**, not a comma string — `grid-template-columns: repeat(auto-fill, minmax(…))`
  so it reflows at any width and can never cause horizontal page scroll
  [3](https://www.tutorialspoint.com/article/how-to-display-a-list-in-n-columns-format)
  [10](https://css-tricks.com/grouping-selection-list-items-together-with-css-grid/)
- a **capped height with internal scrolling** — the list scrolls inside its own
  box, the page never does
- a **"find in this list" filter** for the long ones
- a **copy-all** button, because people paste these into messages to friends
- the matched roll **highlighted** when arriving from a search

I will avoid CSS multi-column (`column-count`) for this. It reads top-to-bottom
per column, which is wrong for a list people scan for one value, and its column
widths are not directly controllable [9](https://denisdefreyne.com/articles/2021-horizontal-layout/).
A wrapping grid reads left-to-right like the printed notice does.

**Rendering cost:** 1,401 chips as DOM nodes is fine on a modern phone, but I will
only build the chips for a list when it is actually expanded, not at page load.

---

## 6. Emotional register — the selected-candidate card

Your point stands and I think it is the difference between a utility and
something people remember. Right now a life-changing result renders as a grey
card with the same visual weight as a PDF-size badge.

The strongest reference is the GOV.UK **confirmation page** pattern — the one
used across UK public services to deliver an outcome
[GOV.UK](https://design-system.service.gov.uk/patterns/confirmation-pages/). Its
structure:

1. A large, high-contrast **panel** carrying the outcome and the key reference
   number — unmissable, the visual anchor of the page.
2. Immediately below, a **"What happens next"** heading with concrete, dated steps.
3. Contact details, and a way to **save a record** of it.

That maps onto our three good-news cases almost exactly:

| Case | Panel line | What happens next |
|---|---|---|
| Selected / offer letter | **অভিনন্দন! আপনি নির্বাচিত হয়েছেন** | document verification, dates, what to bring |
| Passed preliminary → written | **অভিনন্দন! আপনি লিখিত পরীক্ষার জন্য উত্তীর্ণ** | exam date, time, venue, gate-closing time, banned items |
| Viva scheduled | **আপনার মৌখিক পরীক্ষার সময়সূচি প্রকাশিত** | batch, date, reporting time |

Two guard rails I want to agree on now:

- **Celebrate accurately.** "অভিনন্দন" is right for an offer letter. For a
  preliminary-test pass it must say *"you qualified for the next round"* — I
  already hit this exact trap last night and nearly shipped "you are on the
  primarily selected list" to 334 people who had merely passed a prelim.
- **GOV.UK's own warning:** interactive elements placed inside the coloured
  confirmation panel fail contrast unless deliberately handled. Buttons go
  *below* the panel, not inside it.

And the neutral case deserves care too. "Not found" currently reads like a
failure. It should read as *"this roll is not in the 9 notices we have indexed"* —
a statement about our data, not about the person — with the official portal
linked.

---

## 7. What gets rebuilt

| Component | Now | After |
|---|---|---|
| Theme tokens | 11 dark hex values | ~24 semantic tokens × 2 themes |
| Theme toggle | none | system / light / dark, persisted, no flash |
| Fonts | none declared | subset Noto Sans Bengali, self-hosted, tabular figures |
| Search box | plain input | + disambiguation strip when >1 job matches |
| Seat-plan card | centre name is headline | post + Job ID headline, centre second |
| Selected card | grey card | outcome panel + "what happens next" |
| Roll list | comma string in a `<td>` | chip grid, capped height, filter, copy |
| Archive truncation | arbitrary 60 | consistent with the expandable component |
| Not-found state | reads as failure | reframed, with official link |
| Focus states | browser default | visible ≥3:1 ring in both themes |

---

## 8. Constraints the design must respect

These are non-negotiable properties of the current build, and they rule out a lot
of conventional advice:

- **Single self-contained `index.html`** with data inlined. No bundler, no
  framework, no npm. The redesign stays vanilla.
- **Offline-capable.** Service worker caches the shell. Therefore no CDN for
  fonts, icons, or CSS.
- **Budget.** Currently 26 KB gzipped. I propose a ceiling of **40 KB gzipped for
  HTML/CSS/JS**, plus the font as a separately-cached ~90–120 KB file. If the
  design cannot fit, the design changes, not the budget.
- **Generated, not hand-edited.** `index.html` is produced by
  `parser/build_site.py` from `app.template.html`. All work happens in the
  template.
- **Bengali text is content, not decoration.** Line-height must accommodate
  vowel signs above and below the matra; the current 1.55 is marginal for Bengali
  at small sizes.

---

## 9. Risks

| Risk | Mitigation |
|---|---|
| Font download hurts first load on slow mobile | subset aggressively; `font-display: swap`; system stack renders instantly meanwhile |
| Light mode shipped as an afterthought and looks bad | design both palettes together, check contrast on both before merging |
| Big rewrite breaks the search | the Playwright probe suite already exists — extend it to cover both themes and the disambiguation flow before touching the template |
| ~~Notices sometimes lack a Job ID~~ **WRONG — corrected** | All 13 notices **do** carry a `jobId`. It is `noticeNo` that is missing on 4. See §12. |
| Scope creep | phase it, ship each phase working |

**Correction, found during the build:** I reported above that 5 of 13 notices
have `jobId: null`. That was wrong — I had read the wrong column. **Every one of
the 13 notices carries a Job ID.** The field missing on 4 of them is `noticeNo`,
and checking `career.html` shows why: for those four the official portal
publishes **no notice number at all**, only a Job ID. So the fallback I was
worried about is not needed, and the finding actually strengthens the case —
for 4 of 13 notices the Job ID is the *only* identifier that exists.

---

## 10. Proposed phasing

Each phase ends with a working, shippable site.

- **Phase A — foundations (no visible redesign).** Token layer, light/dark
  plumbing, toggle, font loading, focus states. Risky-but-invisible groundwork.
- **Phase B — the overflow fix.** Chip grid, capped height, filter, copy button.
  Kills the horizontal scroll. Smallest change with the most immediate relief.
- **Phase C — information architecture.** Job-ID-first card hierarchy,
  disambiguation strip, remembered job preference.
- **Phase D — the outcome cards.** Confirmation-panel pattern, honest
  per-kind headlines, "what happens next", reframed not-found.
- **Phase E — polish.** Spacing scale, motion (respecting
  `prefers-reduced-motion`), print stylesheet so a candidate can print their seat
  plan.

---

## 11. Decisions I need from you

1. **Interface language.** Currently mixed — English headings
   ("You are on the primarily selected list"), Bengali content. Your users are
   Bangladeshi job seekers. Should the UI be Bengali-first with English
   secondary, fully bilingual with a toggle, or stay as it is?
2. **Font cost.** Accept a one-time ~90–120 KB font download for consistent
   typography, or stay at 0 KB with the system stack?
3. **Default theme** for a first-time visitor: follow the OS, or force dark?
4. **Phasing.** All five phases in one go, or ship B (the overflow fix) first
   since that is the visible bug?


---

## 12. What was actually built

Shipped in one pass after the decisions above (bilingual, Hind Siliguri, follow
OS theme, all phases together). Verified by 36 browser checks plus the existing
suites.

### Corrections to this report, found while building

1. **Job IDs are universal.** §9 claimed 5 of 13 notices lack one. Wrong column.
   All 13 have a `jobId`; 4 lack a `noticeNo`, and `career.html` confirms the
   portal publishes no notice number for those four — only a Job ID. The card
   now omits the notice field when it does not exist rather than printing
   `বিজ্ঞপ্তি —`, which is what the earlier screenshot showed. No number was
   invented.
2. **Font cost was underestimated.** I estimated 90–120 KB. The real figure for
   Hind Siliguri at two weights across both scripts is **175 KB** (Bengali
   ~71–75 KB per weight, Latin ~14.5 KB per weight). Kept at two weights (400,
   600) rather than three to hold the number down. Loaded with
   `font-display: swap` and precached by the service worker, so it costs one
   download, once.

### Delivered

| Area | Result |
|---|---|
| Horizontal overflow | **Fixed.** Verified no page-level horizontal scroll at 1280px *and* 360px with all 1,401 roll chips expanded |
| Roll lists | Wrapping chip grid, internal scroll, in-list filter, copy-all, lazy render on expand |
| Archive truncation | Removed — the arbitrary 60-item "…" is gone, the full list is browsable |
| Job ID | Primary identifier on every card and every archive row |
| Disambiguation | Strip appears only when a roll spans >1 job; choice is remembered and floats that job to the top with a "your post" marker |
| Themes | System / light / dark, persisted, no flash, `color-scheme` set |
| Contrast | Every text/surface pair computed against the lightest surface it can sit on; all ≥4.5:1, plus a dedicated ≥3:1 control-border token |
| Fonts | Hind Siliguri self-hosted, split by script via `unicode-range`, tabular figures |
| Language | Full EN/BN toggle; digits follow the language (১০৫৪৩২ vs 105432) |
| Celebration | GOV.UK confirmation-panel pattern + "what happens next" |
| Honesty | Prelim-pass notice still says *"you qualified for the written exam"*, never "selected"; OCR and hand-typed provenance still disclosed, in both languages |
| Not-found | Reframed as a gap in our index, not a verdict on the person |
| Extras | Print stylesheet, `prefers-reduced-motion`, visible focus rings |

### Regression guards added

`tools/selftest.py` now fails if the template loses the theme hook, the no-flash
script, the webfont, the non-overflowing grid, the bilingual table, the
disambiguation copy, reduced-motion or print support — and specifically if roll
lists are ever joined back into a single string.
