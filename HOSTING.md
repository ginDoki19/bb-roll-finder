# Putting your site on the internet — tailored for `ginDoki19`

> ## ✅ DEPLOYED — <https://bb-roll-finder.pages.dev>
> Verified live on 11 Nov 2026: 5/5 roll lookups correct, offline mode working,
> no JS errors, `_headers` applied, Brotli on. Keep this file for the update
> routine (Step 5) and the troubleshooting table.

You already have GitHub, Git installed, and a live repo (`GinArena-patch`, pushed two
days ago). So the usual beginner setup is already done:

| | |
|---|---|
| ~~Install Git~~ | ✅ already done |
| ~~Create a GitHub account~~ | ✅ `ginDoki19` |
| ~~Sign in to Git / cache credentials~~ | ✅ already working — you pushed recently |
| Create a new repo for this project | ← you are here |
| Push this folder into it | 3 minutes |
| Connect Cloudflare Pages | 5 minutes |

**Real time needed: about 12 minutes.** Every command below already has your username
in it, so it's straight copy-paste — no editing.

> ⚠️ **Do not put this inside `GinArena-patch`.** That's an Android patch project.
> This needs its own repo, because Cloudflare Pages publishes a whole repository as
> one website.

---

## What's going to happen

```
   YOUR PC                       GITHUB                     CLOUDFLARE
 ┌───────────┐              ┌────────────────┐           ┌──────────────┐
 │  run.bat  │ ─── push ──▶ │ ginDoki19/     │ ─ sees ─▶ │ publishes in │
 │           │              │ bb-roll-finder │   change  │   ~30 sec    │
 └───────────┘              └────────────────┘           └──────┬───────┘
                                                                │
                                              https://bb-roll-finder.pages.dev
```

After setup, your entire routine is: **double-click `run.bat`.** The live site
updates itself. You never open Cloudflare again.

---

# Step 1 · Create the empty repo (2 min)

1. Go to **<https://github.com/new>**
2. Fill in exactly:

   | Field | Value |
   |---|---|
   | Repository name | `bb-roll-finder` |
   | Public / Private | **Public** *(Private also works with Cloudflare — public is just simpler)* |
   | Add a README file | ⬜ **unticked** |
   | Add .gitignore | **None** |
   | Choose a license | **None** |

   ⚠️ Those last three must stay empty. You know this one already from
   `GinArena-patch` — if GitHub puts files in the repo first, your push gets
   rejected as "unrelated histories".

3. Click **Create repository**. Ignore the commands it shows you; use mine below.

---

# Step 2 · Push the folder (3 min)

Open File Explorer, go into your `bb-notice` folder (you should see `index.html`,
`run.bat`, the `notices` folder). Click the **address bar**, type `cmd`, press Enter.

The window should open at `C:\...\bb-notice>`. Now paste these one at a time:

```cmd
git init
```

```cmd
git add -A
```

```cmd
git commit -m "BB roll finder - seat plans, viva schedules, roll search"
```

```cmd
git branch -M main
```

```cmd
git remote add origin https://github.com/ginDoki19/bb-roll-finder.git
```

```cmd
git push -u origin main
```

**No login window should appear** — Git Credential Manager already has your GitHub
token cached from your `GinArena-patch` work. If one does pop up, just sign in; it's
a one-off.

You should see roughly:

```
Enumerating objects: 46, done.
Writing objects: 100% (46/46), 3.08 MiB | 1.4 MiB/s, done.
To https://github.com/ginDoki19/bb-roll-finder.git
 * [new branch]      main -> main
```

✅ Check it at **<https://github.com/ginDoki19/bb-roll-finder>**

**What gets uploaded:** 40 files, 3.08 MB. I verified there are **no logs, no session
cookies, no tokens** in there — `.gitignore` excludes `logs/`, which matters because
your fetch log records Bangladesh Bank session cookies verbatim when a download fails.

---

# Step 3 · Connect Cloudflare (5 min)

Cloudflare is the free host. No credit card, no bandwidth cap, 330+ locations
including Dhaka.

1. Sign up at **<https://dash.cloudflare.com/sign-up>** (email + password, verify).
2. Left sidebar → **Workers & Pages** → **Create**.

## ⚠️ Read this before you click anything

Cloudflare has **two** products that can host your site, and the dashboard now
pushes you into the wrong one by default.

| | **Pages** | **Workers** |
|---|---|---|
| Needs a config file in your repo | ❌ no | ✅ yes (`wrangler.jsonc`) |
| Your free address | `bb-roll-finder.pages.dev` | `bb-roll-finder.<you>.workers.dev` |
| Static traffic cost | free, unlimited | free, unlimited |
| Custom domain later | any DNS provider | domain must use Cloudflare nameservers |
| Cloudflare's own advice | still fully supported | "start new projects here" |

For a plain folder of HTML like yours, **Pages is the simpler one and needs zero
changes to your repo.** Use path A. Path B is the fallback.

If the screen you are looking at says *"Set up your application — Configure your
**Worker** project"*, or the address bar contains `/create/workers`, **you are in the
Workers flow.** Do not press Deploy: with no `wrangler.jsonc` in the repo it fails
with `Missing entry-point`.

---

## Path A · Pages (recommended — no repo changes)

Cloudflare hid this link, it did not remove it.

1. On the **Create an application** screen, scroll to the **bottom of the page**.
2. Below the big template box there is a small line of grey text:
   **"Looking to deploy Pages? Get started →"** — or a **Pages** tab next to
   **Workers** at the top. Click it.
   - Direct link if you cannot find it:
     **<https://dash.cloudflare.com/?to=/:account/workers-and-pages/create/pages>**
3. Choose **Connect to Git** → **Connect GitHub** → **Only select repositories** →
   pick **`bb-roll-finder`** → **Install & Authorize**.

   > "Only select repositories" means Cloudflare sees only this repo, not
   > `GinArena-patch`.

4. Select `bb-roll-finder` → **Begin setup**, then set exactly:

   | Field | Value |
   |---|---|
   | Project name | `bb-roll-finder` |
   | Production branch | `main` |
   | Framework preset | **None** |
   | Build command | **completely empty** |
   | Build output directory | `/` |

   ⚠️ **Leave "Build command" blank.** Your `index.html` is already built — there is
   nothing to compile. Anything typed here fails the deploy.

5. **Save and Deploy.** ~30 seconds later: `https://bb-roll-finder.pages.dev`

---

## Path B · Workers (if you cannot find the Pages link)

This works just as well — it only needs one small file added to your repo first.

1. In your `bb-notice` folder there is a file called **`wrangler.jsonc.sample`**.
   **Rename it to `wrangler.jsonc`** (delete the `.sample` from the end).

   Or do it from the black window:

   ```cmd
   git mv wrangler.jsonc.sample wrangler.jsonc
   git commit -m "add Workers config"
   git push
   ```

2. Back on the Cloudflare screen you already have open:

   | Field | Value |
   |---|---|
   | Project name | `bb-roll-finder` |
   | Build command | **completely empty** |
   | Deploy command | `npx wrangler deploy` |

3. **Deploy.** Your address will be `bb-roll-finder.<your-subdomain>.workers.dev`.

> ⚠️ Only rename that file if you are using Workers. If you later switch to Pages,
> rename it back — Pages **rejects** a `wrangler.jsonc` that has no
> `pages_build_output_dir` key, and the build will fail with a config error.

Everything else in this guide works the same on either path. `_headers`, the service
worker, and offline mode are all supported by both.

---

# Step 4 · Test it (2 min)

1. Open the `.pages.dev` link. Search **`105432`** → you should get two cards
   (মোল্লা কলেজ and Milestone College).
2. Search **`617125`** → should show VIVA, 350/2026, Batch 34.
3. **Open it on your phone** — this is how people will actually use it.
4. Phone browser menu → **Add to Home screen**. It installs with its own icon.
5. **Turn on airplane mode and open it again from the home screen.** It still works —
   the whole site caches itself on first visit. That's the point: candidates check
   their centre while standing outside it, where the network is dead.

---

# Step 5 · Your routine from now on

```
Double-click  run.bat
```

- Browser opens, fetches new notices from Bangladesh Bank.
- Solve the CAPTCHA if one appears. Don't close the window.
- It rebuilds, commits, and pushes automatically.
- Cloudflare republishes in ~30 seconds.

```
Double-click  check.bat
```

- Runs the offline test suite and tells you which published notices you haven't
  downloaded yet. No network needed.

---

# If something goes wrong

| What you see | Fix |
|---|---|
| `remote origin already exists` | `git remote remove origin` then re-run the `git remote add` line |
| `failed to push some refs` / `rejected` | You ticked a box in Step 1. Run `git pull origin main --allow-unrelated-histories` then `git push -u origin main` |
| `Repository not found` | Check with `git remote -v`. Fix: `git remote set-url origin https://github.com/ginDoki19/bb-roll-finder.git` |
| `Authentication failed` | Run `git push` alone and complete the sign-in |
| Cloudflare build fails | You put something in "Build command". Project → Settings → Builds & deployments → clear it → Retry deployment |
| `Missing entry-point` | You are in the **Workers** flow with no `wrangler.jsonc`. Use Path A, or do Path B step 1 |
| `Configuration file ... pages_build_output_dir` | A `wrangler.jsonc` exists but you chose Pages. Rename it back to `wrangler.jsonc.sample` and push |
| Site loads but unstyled/broken | Build output directory must be `/` |
| `run.bat`: *"no GitHub remote is configured"* | Step 2 didn't finish — redo from the `git remote add` line |
| `run.bat`: *"CAPTCHA NEEDED"* | Run it again and solve the puzzle in the window |
| New notices not showing live | You're seeing a cached copy. `Ctrl+Shift+R` to hard-refresh |

Still stuck? Run these two and send me the output — it pinpoints the failing piece:

```cmd
git remote -v
git status
```

---

# Two notes

**A nicer address.** `bb-roll-finder.pages.dev` is free forever. If you later buy a
domain (~$2/year), Pages project → **Custom domains** → **Set up a domain**;
the HTTPS certificate is automatic.

**Nothing here can bill you.** Cloudflare Pages has no bandwidth cap and no payment
method on file. If 100,000 candidates hit the site the week before an exam, it stays
free. That's why I picked Cloudflare over Netlify and Vercel — both cap free
bandwidth at 100 GB/month, and Vercel's free tier is non-commercial only.

**One suggestion given your repo history.** `GinArena-patch` is GPL-3.0. For this
one, consider adding a short `LICENSE` (MIT is fine) and a line in the README saying
it's an unofficial convenience tool, not affiliated with Bangladesh Bank, and that
every result links to the official PDF. The disclaimer is already in the site footer
— having it in the repo too is just tidy.
