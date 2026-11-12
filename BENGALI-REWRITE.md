# Bengali overhaul — second attempt, written against a corpus

The first two passes were me guessing at register. This one is written against
what three papers actually print. Everything below is reversible; mark up
anything you disagree with.

## What I read

| Source | What I took from it |
|---|---|
| prothomalo.com — front page + a long feature | sentence architecture, connectors, time-of-day words |
| bangla.thedailystar.net — front page, a news story, the এক্সপ্লেইনার index | standfirst shape, attribution, explainer register |
| dailyamardesh.com — front page | headline punctuation |
| **prothomalo.com/chakri** — eight recruitment-exam stories, including three about **Bangladesh Bank's own notices** | the exact domain vocabulary, date and time conventions, instruction phrasing |

That last row is the one that mattered. Prothom Alo's চাকরি desk writes about
these identical notices — আসনবিন্যাস, প্রবেশপত্র, কেন্দ্রতালিকা, প্রাথমিকভাবে
নির্বাচিত. I stopped inventing wording and started matching theirs.

---

## The five things they do that the old copy didn't

### 1. Dates are spelled out. Always.

This was the worst offender and it wasn't copy at all — it was a formatter.
Every card printed `১৬/১১/২০২৬`. No Bangladeshi paper has ever written a date
that way in running text.

> **PA:** `৩১ অক্টোবর ২০২৬ (শনিবার)` · `১৯ ডিসেম্বর ২০২৫` · `গত ২৫ সেপ্টেম্বর`

A new `fmtDate()` now renders every Bengali date as `১৬ নভেম্বর ২০২৬`. English
keeps `16/11/2026`, which is the ordinary convention there.

### 2. A clock face is spoken, not punctuated.

The cards printed `সকাল ১০:০০`, `দুপুর ৩:০০ – বিকাল ৪:০০`.

> **PA:** `সকাল ১০টা থেকে দুপুর ১২টা পর্যন্ত` · `বেলা ১১টা ১০ মিনিটে` · `ভোর সাড়ে ৪টা`

`clock()` was rewritten: `১০:০০` → `১০টা`, `১০:৩০` → `সাড়ে ১০টা`, and
`১০:৫০` → `১০টা ৫০ মিনিট`. Also:

- **`বিকাল` → `বিকেল`** — both papers use the চলিত spelling throughout.
- **`1:30 PM` → `দেড়টা`, `2:30` → `আড়াইটা`.** "সাড়ে ১টা" is not something
  anyone says or prints; your data has a 1:30 PM sitting, so this was live.
- **`ভোর`** added for 4–5 AM, which previously fell through to `রাত`.

### 3. The em dash introduces a list. It is not an aside.

> **PA:** `কেন্দ্রগুলো হলো—শেরেবাংলা নগর…` · `পরীক্ষাসংক্রান্ত নির্দেশাবলি হলো—`
> **PA headlines use a comma instead:** `বিসিআইসিতে ২৭৪ জনের চাকরি, ৯ম ও ১০ম গ্রেডে বড় সুযোগ`

The old copy used `—` nine times as an English-style trailing afterthought.
All nine are gone; the one place a dash introduces a list (`hintBase`) kept it.

### 4. `ও` joins nouns in writing. `আর` is spoken.

> **PA:** `পুলিশ, বিজিবি ও শিল্প পুলিশ` · `মূল ভবনের চতুর্থ তলায়`

`আর` appears in their quoted speech and as a contrastive clause-linker, never
between two nouns in reported prose. Three instances fixed.

### 5. Bengali counts with a classifier glued to the numeral.

The stat bar said `১৩ নোটিশ`, `৩৫ কেন্দ্র`.

> **PA:** `১৩৯টি বোমারু বিমান` · `৪৪৯টি শূন্য পদ` · `২১ জন প্রার্থী`

Number-first with no classifier is the one shape they never print. Now
`১৩টি নোটিশ · ৩৫টি কেন্দ্র · ৪,২০৪টি রোল নম্বর`.

---

## I was wrong last time, in both directions

**I banned words that are perfectly normal journalism.** My previous pass
treated `রয়েছে`, `কমপক্ষে`, `সম্পন্ন`, `তালিকাভুক্ত`, `আসন্ন` as bureaucratic
tells. The corpus disproves that flatly — PA writes `কমপক্ষে এক ঘণ্টা আগে
কেন্দ্রে উপস্থিত হতে হবে`, `মোট ১৩৯টি বোমারু বিমান রয়েছে`,
`কালো তালিকাভুক্তির প্রথা`. The problem was never a word blacklist. It is
**sentence architecture** — finite verbs, one idea per sentence, concrete
subjects. `আসন্ন` is restored as the "upcoming" badge.

**And `স্বয়ংক্রিয়ভাবে` stays reverted.** That one I had right the second time:
the audit told me to use it, I obeyed over my own ear, and it was the string
your screenshot landed on.

---

## Every changed string

### Copy — `assets/js/core/language.js`

| Key | Before | After |
|---|---|---|
| `tagline` | …আসন বিন্যাস ও ফলাফল **—** সব এক জায়গায় | …**আসনবিন্যাস** ও ফলাফল এক জায়গায় |
| `hintBase` | **আসন বিন্যাস, ভাইভার** সূচি… | **আসনবিন্যাস, মৌখিক পরীক্ষার** সূচি… |
| `upcoming` | সামনে | **আসন্ন** |
| `srFound` | রোল ২০০৯৮৩ **—** ২টি ফলাফল… | রোল ২০০৯৮৩**,** ২টি ফলাফল… |
| `srAmbig` | …মোট ২টি ফলাফল **—** আপনার পদটি বেছে নিন | …মোট ২টি ফলাফল**। আপনার পদটি বেছে নিন।** |
| `mapOffline` | উপরের বোতামে চাপ **দিয়ে** গুগল ম্যাপে **খুলুন।** | উপরের বোতামে চাপ **দিলে** গুগল ম্যাপে **খুলবে।** |
| `disambigWhy` | …বেছে নিন **— মনে রাখা হবে।** | …বেছে নিন**। পরেরবারের জন্য মনে রাখা হবে।** |
| `congratsOffer` | অভিনন্দন! **আপনার নিয়োগপত্র দেওয়া হয়েছে** | অভিনন্দন! **আপনি নিয়োগপত্র পেয়েছেন** |
| `nextOffer[1]` | **নোটিশে দেওয়া যোগদানের শেষ তারিখের মধ্যে** যোগ দিন। | **নোটিশে যোগদানের যে শেষ তারিখ দেওয়া আছে, তার মধ্যে** যোগ দিন। |
| `nextPrimary[2]` | মূল কাগজপত্র **আর** এক সেট ফটোকপি… | মূল কাগজপত্র **ও** এক সেট ফটোকপি… |
| `nextSeat[0]` | প্রবেশপত্র **আর** ছবিসহ পরিচয়পত্র… | প্রবেশপত্র **ও** ছবিসহ পরিচয়পত্র… |
| `nextSeat[1]` | অন্তত এক ঘণ্টা আগে… | **পরীক্ষা শুরুর** অন্তত এক ঘণ্টা আগে… |
| `nextSeat[2]` | …সাধারণত **ভেতরে নেওয়া** যায় না। | …সাধারণত **কেন্দ্রে আনা** যায় না। |
| `nextViva[1]` | …**হাজির থাকুন —** দেরি করলে… | …**কেন্দ্রে উপস্থিত থাকুন।** দেরি করলে… |
| `notFoundBody` | …যোগ হয়নি **—** নতুন নোটিশ… | …যোগ হয়নি**।** নতুন নোটিশ… |
| `tooShort` | …খোঁজা যাবে না **—** পুরো রোল… | …খোঁজা যাবে না**।** পুরো রোল… |
| `pastNotices` | …পুরোনো নোটিশ **—** শেষ হয়ে গেছে, তবে… | …পুরোনো নোটিশ**, পরীক্ষা** শেষ হয়ে গেছে **তবু**… |
| `ocrProv` | **নম্বরগুলো** কম্পিউটারে… নোটিশটি **ছবি হিসেবে স্ক্যান করা**… **তবুও ভুল থাকতে পারে —** | **রোল নম্বরগুলো** কম্পিউটারে… নোটিশটি **স্ক্যান করা ছবি**… **তবু ভুল থাকতে পারে, তাই** |
| `manualProv` | **নম্বরগুলো** হাতে টাইপ… **একটা একটা** করে… | **রোল নম্বরগুলো** হাতে টাইপ… **একটি একটি** করে… |
| `scannedWarn` | এই নোটিশটি **শুধু একটি ছবি।** | এই নোটিশটি **স্ক্যান করা ছবি মাত্র।** |
| `fConfirm` | …মিলিয়ে নিন **— এটি শুধু একটি সহায়ক সাইট,** অফিসিয়াল উৎস নয়। | …মিলিয়ে নিন**। এই সাইট কেবল সহায়ক,** অফিসিয়াল উৎস নয়। |
| `beThereBy` | দুপুর ২টা**-এর** মধ্যে কেন্দ্রে পৌঁছান | দুপুর ২টা**র** মধ্যে কেন্দ্রে পৌঁছান |
| `statRolls` | তালিকায় থাকা রোল | রোল নম্বর *(classifier now carries the count)* |
| `KIND.seat` badge | আসন **বিন্যাস** | **আসনবিন্যাস** *(PA spells it as one word, every time)* |

`শুধু একটি X` and `এটি শুধু একটি X` are the English copula calque — Bangla
carries it with `মাত্র`. `২টা-এর` is a transliteration habit: a vowel-final
word takes `র`, so it is `২টার`. That is now computed, not hand-written.

### Notice 87 — `meta/overrides.json`

| Field | Before | After |
|---|---|---|
| `headlineBn` | …উত্তীর্ণ হয়েছেন **—** এরপর লিখিত পরীক্ষা | …উত্তীর্ণ হয়েছেন**,** এরপর লিখিত পরীক্ষা |
| `noteBn` | লিখিত পরীক্ষা **২০/১১/২০২৬, বিকাল ৩:০০ – ৫:০০টা**, …**গেট** বন্ধ… | লিখিত পরীক্ষা **২০ নভেম্বর ২০২৬ (শুক্রবার), দুপুর ৩টা থেকে বিকেল ৫টা পর্যন্ত।** …**মূল ফটক** বন্ধ… |
| detail `সময়` | বিকাল ৩:০০ – ৫:০০ | দুপুর ৩টা থেকে বিকেল ৫টা |
| detail `কেন্দ্র` | একাডেমিক ভবন, ব্যবসায় শিক্ষা অনুষদ, ঢাকা বিশ্ববিদ্যালয় | ঢাকা বিশ্ববিদ্যালয়ের ব্যবসায় শিক্ষা অনুষদের একাডেমিক ভবন |
| detail `পৌঁছানোর সময়` | দুপুর ২:০০ **—** বিকাল ৩:০০টায় গেট বন্ধ… | দুপুর ২টা**;** দুপুর ৩টায় মূল ফটক বন্ধ… |

The address reversal is straight from the Daily Star, which wrote
`ব্যবসায় শিক্ষা অনুষদের একাডেমিক ভবনের সামনে` about this very building.
Bengali goes big → small through genitives; comma-separated small → big is
English address order.

The parenthetical weekday — `(শুক্রবার)` — **stays**. I nearly "fixed" it;
PA writes exactly that: `৩১ অক্টোবর ২০২৬ (শনিবার)`.

---

## Left alone deliberately

- **`congratsPrimary` — "আপনি প্রাথমিকভাবে নির্বাচিত হয়েছেন".** PA uses this
  phrase verbatim for these notices: *"২২৫ জন প্রার্থীকে … প্রাথমিকভাবে
  নির্বাচিত করে"*. Confirmed, not guessed.
- **`ভাইভা` on the badge.** PA uses both: `মৌখিক পরীক্ষা` in notice-reporting
  prose, `ভাইভা` in headlines and features. The badge is the candidate's own
  word; the prose (`hintBase`) now says `মৌখিক পরীক্ষার সূচি`. If you'd rather
  it were uniform, say which way.
- **`লাইট` / `ডার্ক` / `অটো`, `পিডিএফ`, `ওসিআর`, `ম্যাপ`, `শেয়ার`, `ব্যাচ`.**
  The papers borrow freely when the loanword is the common word —
  `ক্যালকুলেটর`, `স্মার্টওয়াচ`, `মুঠোফোন`/`মোবাইল ফোন`, `সিরিয়াল`, `ইপেপার`.
- **The English notice titles** in the list. Those are the official titles off
  the PDFs. Translating them would be inventing text the Bank never wrote.
- **English dates and times.** `16/11/2026` and `10:00 AM` are the normal
  convention in English here. Say the word and I'll move them too.

## Judgement calls you may want to reverse

1. `আসন্ন` vs `সামনে` for the upcoming badge.
2. `শেষ` for completed — `সম্পন্ন` is what a notice would say, but it reads as
   officialese next to two one-word badges.
3. `রোল নম্বর` as the third stat, which drops "তালিকায় থাকা".
4. `দুপুর ৩টা` for 3 PM. PA also writes `বেলা ৩টা`; I picked `দুপুর` so the
   hand-written note and the generated cards agree.
5. Dropping `(শুক্রবার)` from generated exam dates — I kept the weekday only in
   the hand-written note, to avoid widening the date cells. Easy to add.

---

## Verification

`selftest` ALL PASS · parity **101 EN / 100 BN** · `uitest` **139/139** ·
`test_fetch` **9/9** · rebuild byte-identical · service worker
`bb-roll-15fc4c84`.

None of that proves the Bengali is good — a parity test cannot see register.
Every string above was rendered and read in the dark theme at 900 px before
being kept.
