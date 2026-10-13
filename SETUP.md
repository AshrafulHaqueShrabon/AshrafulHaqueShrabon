# Setup guide

This folder generates a concise, CV-style GitHub profile README: your name and
headline, contact and coding-profile buttons, skills, your top languages and a
small contribution game. Everything comes from one file, **`profile.toml`**.
`build.py` turns it into `README.md` plus a few small images, and two GitHub
workflows keep the live parts (top languages, game) fresh every day.

> **Everything in your README is public**, including your email address.
> Spam bots read GitHub profiles. Consider an address you don't mind sharing.

## 1. Prerequisites

- **A public GitHub repository named exactly like your username**, with
  `README.md` at its root. For user `octocat` that is `octocat/octocat`.
  That's all for the website method below. (Working on your own computer
  instead also needs Python 3.11+ and Git.)

## 2. First-time setup (website only, no commands)

1. In your profile repository on github.com, click **Add file → Upload files**.
2. Drag in `README.md`, `profile.toml`, `build.py`, `SETUP.md` and the folders
   `assets`, `scripts`, `templates` and `.github`. This replaces your old
   `README.md`; the old version stays in the file's *History*.
3. Click **Commit changes**.
4. Open the **Actions** tab. **build** runs first, then **live**. Wait until
   both show a green check (a few minutes).
5. Open your profile page. Top languages and the game show as broken images
   until **live** has finished once; after that everything appears.

**What the two workflows do.** They are small automated jobs (GitHub
Actions, free for public repositories) that run on GitHub's computers:
- **build** runs whenever you change `profile.toml`, and rebuilds `README.md`
  and its pictures.
- **live** runs once a day, and redraws the top-languages bar and the game. It
  stores them in a separate branch named `output`, so your main files don't
  change daily.

Both workflow files contain `permissions: contents: write`. That lets them save
files in this repository only; they can't touch your other repositories or your
account. You don't need to change any GitHub setting for this.

## 3. Changing things later

- On github.com, open `profile.toml`, click the pencil icon, edit, and click
  **Commit changes**. **build** rebuilds `README.md` within about a minute.
- Never edit `README.md` directly; it is regenerated from `profile.toml`.

**Working on your computer instead (optional).** Run `python build.py --check`
for a checklist (`[FAIL]` lines name what's wrong), then `python build.py` to
rebuild, and commit and push as usual. Pull first: **build** sometimes
commits a rebuilt README.

## 4. Fields in `profile.toml`

Text goes in `"quotes"`; numbers and `true`/`false` don't. An empty value hides
whatever uses it.

| Field | What to enter | Example | Where it appears |
|---|---|---|---|
| `profile.name` | Your name, exactly as it should look | `"Ada Lovelace"` | Page title |
| `profile.github_username` | Your GitHub username | `"octocat"` | Needed for top languages, the game and the visitor counter |
| `profile.headline` | Short parts, joined with ` \| ` | `["Competitive programmer", "C++ · Python"]` | Line under your name (≤ 90 characters keeps it on one line) |
| `profile.bio` | Optional 1–2 sentence summary, plain text | `"CS student who…"` | Under the contact buttons |
| `contact.email` | Email address | `"you@example.com"` | Email button (public!) |
| `contact.linkedin` | LinkedIn profile URL | `"https://www.linkedin.com/in/you"` | LinkedIn button |
| `contact.website` | Website URL | `"https://your-site.com"` | Website button |
| `contact.website_label` | Text on that button, ≤ 11 characters | `"Portfolio"` | Website button |
| `profiles.<site>` | Full profile URL (Codeforces, AtCoder, LeetCode, CodeChef, HackerRank, beecrowd, CSES, vjudge) | `"https://codeforces.com/profile/you"` | One button each under *competitive programming*, in file order |
| `skills.<group>` | Icon IDs, one row per group | `languages = ["c", "cpp", "py"]` | *skills* (the group name is the row label) |
| `github.top_languages` | 1–8 | `5` | *top languages*; the rest is grouped as "Other" |
| `github.exclude_languages` | Languages to leave out | `["Jupyter Notebook"]` | *top languages* |
| `display.accent` | `"amber"` or `"green"` | `"amber"` | Button icons and the game's colors |
| `display.arcade` | `"pacman"`, `"breakout"`, `"galaga"`, `"puzzle-bobble"`, `"bomberman"`, `"minesweeper"`, `"snake"`, or `""` to hide | `"pacman"` | Game strip at the bottom |
| `display.visitor_counter` | `true` / `false` | `true` | "Profile views" badge at the very bottom |

Profile URLs are flexible: missing `https://`, `www.`, trailing slashes and
`?query` parts are fine. `leetcode.cn` isn't supported; use leetcode.com.

## 5. How to…

**Change the accent color.** Set `display.accent = "green"` (or `"amber"`) and push.

**Change or hide the game.** Set `display.arcade` to another game, or `""` to
hide it, and push. Games come from
[pacman-contribution-graph](https://github.com/abozanona/pacman-contribution-graph)
(`"snake"` from [Platane/snk](https://github.com/Platane/snk)); the grid is
recolored to your accent.

**Add or remove profile buttons.** Add or delete lines under `[profiles]`. The
buttons follow the order of the lines.

**Add skills.** Use icon IDs from the *Icons List* on
[skillicons.dev](https://skillicons.dev), e.g. `"rust"`, `"docker"`, `"linux"`.
Short aliases work (`py`, `js`, `ts`, `sklearn`). Notes:
- `"ml"` and `"ai"` are this project's own tiles. On skillicons, `ai` means
  Adobe Illustrator; write `"illustrator"` if you want that.
- `"numpy"` and `"pandas"` come from devicon.
- New icons are downloaded once (`python build.py --fetch-icons`, or
  automatically by the build workflow); until then a "?" tile is shown.
- `--check` rejects unknown IDs. skillicons itself would silently show a blank tile.
- A custom hover label looks like `"cpp:C++17"`. A new row is a new line,
  e.g. `databases = ["postgres"]`.

**Include private repositories in top languages (optional token).**
1. On GitHub: *Settings → Developer settings → Personal access tokens → Tokens
   (classic) → Generate new token*. Select the **`repo`** and **`read:user`**
   scopes and set an expiry date.
2. In your profile repository: *Settings → Secrets and variables → Actions →
   New repository secret*, named **`PROFILE_PAT`**, with the token as its value.
3. Renew the token before it expires. Until then the workflows quietly fall
   back to the built-in token, which only sees public repositories.

**Change the layout.** The section order lives in `templates/readme.md.tmpl`;
colors and sizes live in `scripts/style.py`.

## 6. Troubleshooting

**Images look out of date.** GitHub caches images (its camo proxy, and
raw.githubusercontent.com for 5 minutes). Wait a few minutes and hard-refresh
(`Ctrl+Shift+R`). Live images change once a day.

**Broken images right after the first push.** Top languages and the game come
from the `output` branch, which exists only after the **live** workflow has run
once. Run it from the Actions tab.

**The daily refresh stopped.** In public repositories, GitHub disables
scheduled workflows after **60 days without repository activity** (it usually
emails a warning first). Open *Actions → live → Enable workflow*. This project
deliberately doesn't use "keepalive" tricks: the popular keepalive action's
repository was blocked by GitHub in 2025.

**A workflow fails with "Permission denied" or a 403 on push.** This shouldn't
happen, because the workflow files ask for the permission they need. If it
does, open *Settings → Actions → General → Workflow permissions*, choose
*Read and write permissions*, and run the workflow again.

**GitHub's API or the game generator fails.** Nothing breaks: the last
successful image is kept, from `cache/live.json` and the previous files on the
`output` branch. Before the very first success, a quiet "appears after the
first daily update" placeholder is shown instead.

**A "?" tile in skills.** That icon isn't downloaded yet. Run
`python build.py --fetch-icons` or just push.

## 7. Optional: developer tools

Builds and workflows never need these.

```bash
bash scripts/dev/setup_dev.sh                    # .venv with Playwright + Chromium, PyYAML
python3 -m unittest discover -s tests -t .       # unit tests (standard library, offline)
.venv/bin/python scripts/dev/preview.py mine     # screenshots of YOUR README → preview/mine/ (offline)
.venv/bin/python scripts/dev/preview.py readme   # the fictional demo, via GitHub's renderer → preview/
```

`examples/demo.toml` is a fully fictional profile that shows every section.

## 8. What this depends on

| Dependency | Used for | If it goes down |
|---|---|---|
| GitHub Actions + `actions/checkout` (pinned SHA) | Running the workflows | Nothing updates; the README keeps its last images |
| raw.githubusercontent.com | Serving the live images from the `output` branch | Top languages and the game don't load; everything else does |
| GitHub GraphQL API | Top languages | Last-known-good image; a placeholder before the first success |
| abozanona/pacman-contribution-graph v5.3.2 / Platane/snk v3.5.0 (pinned SHAs) | The contribution game | Previous game kept; a placeholder before the first success |
| skillicons.dev, devicon (only when adding icons) | Downloading a new icon once | "?" tile for the new icon; existing icons are committed |
| komarev.com (only if `visitor_counter = true`) | "Profile views" badge | The badge doesn't load; set it to `false` |
