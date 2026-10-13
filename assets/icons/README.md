# Icons

| Folder | What | Source / license |
|---|---|---|
| `vendor/` | Skill icons, fetched once per icon ID and committed | [skillicons.dev](https://skillicons.dev) (MIT, [LICENSE-skill-icons.txt](LICENSE-skill-icons.txt)); NumPy and pandas glyphs from [devicon](https://devicon.dev) v2.17.0 (MIT, [LICENSE-devicon.txt](LICENSE-devicon.txt)) placed on the same tile |
| `custom/` | `ml` (neural network) and `ai` (microchip) tiles | Original art for this project |
| `registry.json` | Valid skillicons IDs and short aliases (`py` → `python`) | skillicons.dev API + its source; used by `build.py --check` |

Brand logos remain trademarks of their owners and are shown only to name the
skills. `python build.py --fetch-icons` downloads icons added to `[skills]` in profile.toml
(the build workflow runs it on every push); until then a "?" tile is shown.
