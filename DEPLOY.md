# Deploy to Cloudflare Pages (free, unlimited bandwidth)

Your workflow after this is: **double-click `run.bat` → the live site updates itself.**

---

## One-time: push to GitHub

```cmd
cd bb-notice
git init
git add -A
git commit -m "BB roll finder"
git branch -M main
git remote add origin https://github.com/ginDoki19/bb-roll-finder.git
git push -u origin main
```

Credentials are already cached from your other repo, so no login prompt is expected.
Full walkthrough with screenshots-in-words: **`HOSTING.md`**.

## One-time: connect Cloudflare Pages

1. <https://dash.cloudflare.com> → sign up (free, no card).
2. **Workers & Pages → Create → Pages → Connect to Git** → pick `bb-roll-finder`.
3. Build settings — **this is a plain static site, so leave the build empty:**

   | Field | Value |
   |---|---|
   | Framework preset | **None** |
   | Build command | *(leave blank)* |
   | Build output directory | `/` |

4. **Save and Deploy.** ~30 seconds later you get
   `https://bb-roll-finder.pages.dev`

That URL is what you share. Cloudflare has a Dhaka edge location, so it loads
locally rather than from another continent.

## From then on

```
double-click run.bat
   ↓  fetches new notices (solve the CAPTCHA if asked)
   ↓  rebuilds data/notices.json and index.html
   ↓  git commit + push
Cloudflare sees the push and redeploys     (~30 s, automatic)
```

You never open the Cloudflare dashboard again.

### Checking it worked

```cmd
check.bat
```

Runs the offline test suite, the data invariants, and lists any published notice
you have not downloaded yet.

---

## Why Cloudflare Pages and not the others

| | Cloudflare Pages | Netlify | Vercel Hobby | GitHub Pages |
|---|---|---|---|---|
| Bandwidth | **Unlimited** | 100 GB/mo | 100 GB/mo | 100 GB/mo |
| Edge locations | **330+ (incl. Dhaka)** | ~8 regions | ~40 | limited |
| Commercial use | ✅ | ✅ | ❌ not allowed | ✅ |
| Free builds | 500/mo | 300 min/mo | 6,000 min/mo | 10 min limit |

You will use roughly 10–30 builds a month against a 500 allowance.

## Custom domain (optional, free)

Pages → your project → **Custom domains → Set up a domain**. If the domain is
already on Cloudflare DNS it is two clicks and the certificate is automatic.

---

## What is in the deployed site

| File | Purpose |
|---|---|
| `index.html` | the whole app — 80 KB, **19.9 KB gzipped**, data inlined |
| `sw.js` | service worker — the site works with **no internet** after one visit |
| `manifest.webmanifest` | makes it installable ("Add to Home screen") |
| `_headers` | cache rules: `index.html` revalidates, PDFs cached for a year |
| `notices/*.pdf` | the official PDFs, linked from every card |

### The offline bit matters

Candidates check their centre while standing outside it, on a congested Dhaka
mobile network. After one visit the service worker serves the whole app from
cache — verified here by killing the network, reloading, and searching a roll
successfully.

### After you deploy a new version

The service worker caches aggressively. If you change `index.html` and want to be
certain returning visitors get it immediately, bump the cache name in `sw.js`:

```js
const CACHE = "bb-roll-v2";   // was v1
```

Old caches are deleted automatically on activation.
