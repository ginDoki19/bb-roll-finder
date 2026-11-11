# Workflow audit — "dynamic site, popular framework, auto-fetch every 12h, free, zero touch"

Date: 2026-11-11. Every number below is either measured on your actual data or cited
from a source with a 2026 date. Where something cannot be done, the reason is a
measurement, not an opinion.

---

## Verdict first

| What you asked for | Verdict | Why |
|---|---|---|
| Free hosting | ✅ **Cloudflare Pages** | Unlimited bandwidth, 330+ PoPs, commercial use allowed |
| Fast | ✅ already is — **25.7 KB gzipped** | A framework would make it *slower*. See §4. |
| "Popular framework" | ⚠️ **Astro, as a build tool only** | Next.js alone ships 80–120 KB of JS. Your whole site is 25.7 KB. |
| Auto-fetch every 12h | ✅ but **must run on your PC** | Cloud IPs are blocked by the WAF. See §1. |
| Deploy automatically | ✅ `git push` → Pages builds | 60 builds/month vs 500 free |
| **"I won't touch a thing"** | ❌ **not fully achievable** | One CAPTCHA re-solve every few weeks. See §6. |

The honest headline: **everything is automatable except the CAPTCHA**, and no amount
of framework or hosting choice changes that, because the blocker is on Bangladesh
Bank's firewall, not in your stack.

---

## 1 · The hard constraint, re-confirmed by your own log

`erecruitment.bb.org.bd` runs **F5 BIG-IP ASM** (the `TSPD_101`, `TS01cf43c8`,
`bb_cookie` cookies in your `logs/fetch.log` are its signature). F5's device
fingerprinting stores an encrypted device ID in `TSPD_101` and requires a real
browser to execute a JavaScript challenge. [4](https://my.f5.com/manage/s/article/K19556739)

Industry analysis of F5 in 2026 is blunt about the IP layer: F5 maintains *"one of
the largest IP and ASN reputation databases in the industry; datacenter ranges are
almost universally blocked."* [5](https://scrapfly.io/blog/posts/how-to-bypass-anti-bot-protection) A headless browser on a datacenter IP is
*"blocked on reputation before behavior even matters."* [10](https://www.sparkproxy.io/blog/bypass-shape-security-web-scraping)

Your log is the local proof, and it is unusually clean evidence:

```
09:54:34  ✗ still blocked after waiting        ← Playwright bundled Chromium
10:00:19  ✗ still blocked after waiting        ← same, retried
10:20:04  browser: ...BraveSoftware\brave.exe
          · 31 KB, 7 PDF row(s)                ← real Brave: through
          ↓ 20261102_bb_83_1793613569.pdf  (412 KB)
```

Same machine, same residential IP, same minute. **The only variable that changed was
the browser binary.** That rules out IP-only explanations and proves the fingerprint
layer matters too — which is exactly why a cloud runner cannot work even with a proxy.

**Consequence:** the fetch must originate from a real browser on a residential
connection. Every "run it in the cloud" design below dies on this line.

---

## 2 · Every cloud-cron option, priced and dismissed

| Option | Free limit | Verdict for a 12-hour fetch |
|---|---|---|
| **Vercel Cron (Hobby)** | **once per day, max** — sub-daily schedules are *rejected at deploy time* with `"Hobby accounts are limited to daily Cron Jobs"` [1](https://runhooks.app/blog/vercel-hobby-cron-job-limits-explained/) | ❌ 12h is literally un-deployable. Also 10 s function timeout. [7](https://cronjobpro.com/blog/vercel-cron-jobs) |
| **Netlify Scheduled Functions** | 30 s execution cap, 1-day log retention [3](https://merginit.com/blog/26062026-free-cron-job-scheduler-comparison) | ❌ A browser fetch cannot finish in 30 s. |
| **GitHub Actions (hosted runner)** | 2,000 min/month free | ❌ Datacenter IP → CAPTCHA. Dies at §1. |
| **GitHub Actions (self-hosted runner on your PC)** | free | ⚠️ Solves the IP problem, but the *schedule* is still evaluated by GitHub's servers — see below. |
| **Cloudflare Workers Cron** | 100k req/day | ❌ No real browser; datacenter IP. |

### Why I am not recommending GitHub Actions cron even with a self-hosted runner

This looked like the elegant answer. The evidence says no:

- Scheduled workflows *"may be delayed or, if load is sufficiently high, potentially
  dropped"*; delays of **10–30 minutes are common**, over an hour reported. [3](https://cronjobpro.com/blog/github-actions-scheduled-workflows)
- Public repos have scheduled workflows **auto-disabled after 60 days without a
  commit, issue or PR** — and *"a workflow successfully running on schedule does not
  count as activity."* [4](https://dev.to/vincentabolarin/how-to-monitor-github-actions-scheduled-workflows-2l5g) So a quiet period silently kills your automation.
- With a self-hosted Windows runner specifically, users report `*/15` cron *"only
  gets scheduled every 3-4 hours"*, and GitHub's own community thread confirms the
  schedule is triggered by GitHub, not the runner. [1](https://github.com/orgs/community/discussions/185024)

**Windows Task Scheduler has none of these failure modes.** It is the right tool.

---

## 3 · The architecture I recommend

Three tiers, each doing the one thing it is actually good at.

```
┌─ YOUR PC ──────────────────────────┐   ┌─ GITHUB ────┐   ┌─ CLOUDFLARE PAGES ─┐
│  Task Scheduler  09:00 / 21:00     │   │             │   │                     │
│        ↓                           │   │  git repo   │   │  build on push      │
│  fetch_notices.py --build --push   │──▶│  (source of │──▶│  astro build        │
│    Brave + cached F5 cookie        │   │   truth)    │   │        ↓            │
│    → career.html + new PDFs        │   │             │   │  330+ edge PoPs     │
│    → build_data → notices.json     │   └─────────────┘   │  unlimited BW       │
│    → git commit && push            │                     └─────────────────────┘
└────────────────────────────────────┘                               ↓
                                                          visitors (incl. Dhaka PoP)
```

**Why Cloudflare Pages over Netlify/Vercel/GitHub Pages:**

| | Cloudflare Pages | Netlify | Vercel Hobby | GitHub Pages |
|---|---|---|---|---|
| Bandwidth | **Unlimited** | 100 GB/mo | 100 GB/mo | 100 GB/mo |
| Builds free | 500/mo | 300 min/mo | 6,000 min/mo | 10 min limit |
| Edge PoPs | **330+** | ~8 regions | ~40 | limited |
| Commercial use | ✅ | ✅ | ❌ **not allowed** | ✅ |

Sources: [2](https://khimananda.com/blog/cloudflare-pages-vs-netlify-vs-vercel-for-static-sites), [4](https://dev.to/lazydev_oh/vercel-vs-netlify-vs-cloudflare-pages-2026-deep-comparison-with-real-numbers-8pl)

Two pushes a day = **60 builds/month against a 500 free allowance** — 12 % utilisation.
Cloudflare has a PoP in Dhaka, which matters for your actual audience far more than
any framework choice. Vercel's Hobby tier is also *non-commercial only*, a licence
risk you don't need to take.

---

## 4 · The framework question — the measurement that changes the answer

I measured your current site before recommending anything:

```
notices.json    257.8 KB raw   →  18.4 KB gzipped
index.html      278.3 KB raw   →  25.7 KB gzipped   ← everything a visitor downloads
```

**25.7 KB, one request, zero dependencies, works offline.**

Now compare against what the frameworks cost *before any of your content loads*:

| Framework | Baseline JS shipped | Typical Lighthouse |
|---|---|---|
| Next.js 15 static export | **80–120 KB** | 80–85 |
| SvelteKit (prerendered) | 15–30 KB | 90–98 |
| **Astro (no islands)** | **0 KB** | 95–100 |

Sources: [1](https://dev.to/pockit_tools/nextjs-vs-remix-vs-astro-vs-sveltekit-in-2026-the-definitive-framework-decision-guide-lp5), [2](https://www.pkgpulse.com/guides/astro-vs-nextjs-2026), [5](https://talos.tools/blog/best-static-site-generators-2026)

**Putting Next.js on this would make your site 3–5× heavier.** Its React runtime
alone is larger than your entire application including all 3,840 roll numbers. That
is the single most important finding in this audit, and it inverts the usual advice.

### Recommendation: Astro — and use it as a *build tool*, not a runtime

Astro ships **0 KB of JavaScript by default** and hydrates only marked "islands".
The architecture maps onto your app exactly:

- **Static (0 KB JS):** header, all 9 notice cards, the tables, the footer. These
  never change between visits.
- **One island (`client:load`):** the roll search box. It is the only interactive
  thing on the page, and it is ~4 KB of logic you already wrote in vanilla JS.

You get a real framework, a component model, a build pipeline, and typed content
collections — while shipping *less* than today. If you would rather not add a
dependency at all, keeping the current vanilla build is defensible: it is already at
the performance ceiling. Astro's win is maintainability, not speed.

### The real speed win is the data format, not the framework

Your `rollIndex` currently stores one object per roll:

```json
"522567": {"d":"05/11/2026","t":"3:30 PM","b":"01"}      // 58 bytes per roll
```

The date, time and batch repeat for every roll in the same sitting. Group by sitting
and delta-encode the roll numbers, and I measured:

| | raw | gzipped |
|---|---|---|
| 350/2026 today | 105.9 KB | 6.9 KB |
| grouped by sitting | 16.1 KB | 5.8 KB |
| **+ delta-encoded** | **7.8 KB** | **3.0 KB** |
| **whole site today** | **160.5 KB** | **17.5 KB** |
| **whole site regrouped** | **28.4 KB** | **10.8 KB** |

**A 5.6× cut in raw bytes and a 1.6× cut over the wire.** Raw size is what matters
on a cheap Android phone: that is JSON the browser must parse on the main thread
before the search box responds. This single change is worth more than any framework
migration, and it is about 30 lines in `build_data.py` plus 10 in the client.

---

## 5 · The 12-hour schedule, concretely

```
Task Scheduler → Create Task
  Triggers:  Daily, 09:00, repeat every 12 hours, indefinitely
  Action:    Program  pythonw.exe
             Args     tools\fetch_notices.py --build --push --log logs\fetch.log
             Start in C:\Users\<you>\bb-notice
  Settings:  ☑ Run task as soon as possible after a scheduled start is missed
             ☑ If the task fails, restart every 15 minutes, up to 3 times
             ☐ Stop the task if it runs longer than...  (uncheck — CAPTCHA waits)
```

The two checked boxes matter: the first covers your PC being asleep at 09:00, the
second covers a transient network failure — and your log shows exactly that failure
happening for real (`ERR_INTERNET_DISCONNECTED`, `ECONNRESET` on two PDFs).

**Push triggers everything downstream.** Cloudflare Pages watches the repo; a commit
rebuilds and redeploys in ~30 seconds. You never log into anything.

---

## 6 · Where "I won't touch a thing" actually breaks

I am not going to tell you this is 100 % hands-off, because your own log disproves it.

1. **The F5 cookie expires.** Your log shows a successful run at 09:44, then
   `✗ still blocked` at 09:54 and 10:00 — ten minutes later. Once the cached
   `TSPD_101` goes stale, the next run needs a human to solve an image CAPTCHA.
   Realistically: **a few minutes of your attention every couple of weeks.**
2. **Your PC must be awake** at 09:00 or 21:00. "Wake the computer to run this task"
   in Task Scheduler helps; a machine that is fully off does not run.
3. **Two notices are photographs** (83/2026, 372/2026 — 100 % image coverage, no
   text layer). No automation fixes that; the site now flags them honestly.

### The one free path that removes your PC entirely — and its honest odds

**ZenRows** free tier: **5,000 credits/month, refreshes monthly, no credit card.** [3](https://aifree.dev/learn/free-web-scraping-api)
A protected page (JS rendering + premium residential proxy) costs **25 credits**. [4](https://webscraping.cc/blog/zenrows-pricing/)

The arithmetic actually fits:

```
2 listing pages × 2 runs/day × 30 days × 25 credits  =  3,000 credits
~10 new PDFs/month × 25 credits                      =    250 credits
                                                TOTAL ≈ 3,250 / 5,000   ✓ 65 %
```

So it is *free and within quota*. The catch is success rate: independent benchmarking
puts ZenRows at *"15 % (Scrapeway Aug 2026), ~40 % mid-2026"* on protected targets,
while **Scrapfly measures ~98 %** but gives only **1,000 one-time credits**, then
$30/month. [4](https://webscraping.cc/blog/zenrows-pricing/) [1](https://www.zenrows.com/blog/best-web-scraping-apis-benchmarked)

**My recommendation:** keep the PC fetch as the primary, and spend 30 minutes wiring
ZenRows as an *optional fallback* behind a `--api` flag. It costs nothing to try, and
if it works on this particular target you can retire the PC. If it does not, you have
lost half an hour and learned the answer instead of guessing.

---

## 7 · Migration plan

| # | Task | Effort | Payoff |
|---|---|---|---|
| 1 | **Repack the data** (group by sitting + delta) | 1 h | 160 KB → 28 KB raw. Biggest single win. |
| 2 | **Deploy to Cloudflare Pages** | 20 min | Unlimited bandwidth, Dhaka PoP, auto-deploy on push |
| 3 | **Task Scheduler, 12-hourly** | 20 min | The automation you asked for |
| 4 | Port to **Astro** (static + 1 island) | 3–4 h | Maintainability; keeps 0 KB JS baseline |
| 5 | **PWA** (manifest + service worker) | 1 h | Installable, instant repeat loads, works in an exam hall with no signal |
| 6 | `ntfy.sh` push when a new notice lands | 1 h | You learn about notices without visiting |
| 7 | ZenRows `--api` fallback experiment | 30 min | Possible full removal of the PC |

**Do 1–3 first.** They are 1h40m total and deliver every functional thing you asked
for. Step 4 is a refactor that will not make the site measurably faster — do it
because you want the component model, not because of performance.

### Step 5 deserves a mention it usually doesn't get

A service worker makes the *second* visit effectively instant and, more importantly,
**works with no signal**. Your users are candidates standing outside an exam centre
in Dhaka on congested mobile networks, checking which room they are in. Offline
capability is worth more to them than any millisecond of TTFB.

---

## 8 · What I would not do

- **Do not put Next.js on this.** 80–120 KB of React runtime to render 9 cards and a
  text input, when the entire current app is 25.7 KB.
- **Do not use Vercel.** Hobby is non-commercial-only, cron is daily-max, and the
  bandwidth is capped where Cloudflare's is not.
- **Do not rely on GitHub Actions cron**, even with a self-hosted runner: 10–30 min
  drift, drops under load, and silent 60-day auto-disable.
- **Do not add a database or SSR.** The dataset is 28 KB after repacking. Serving it
  as a static file from an edge PoP is faster than any query you could write, and it
  cannot go down.
- **Do not buy residential proxies** before testing ZenRows free. A residential IP
  alone does not defeat F5 — it still needs the browser fingerprint and the JS
  challenge. [10](https://www.sparkproxy.io/blog/bypass-shape-security-web-scraping)
