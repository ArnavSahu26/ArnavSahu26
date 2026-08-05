# Setup notes

Everything here is tested and working against your real GitHub account
(`ArnavSahu26`) except the portrait, which needs a photo of you to run against.

## What's already done and verified
- `tools/pull_contributions.py` — tested live against your account.
  Pulled 40 contributions over the last year, 4-day longest streak,
  busiest day Monday. Note: GitHub's current markup doesn't expose a
  `data-count` attribute on day cells the way the original walkthrough
  assumed — the count only lives in text inside a sibling `<tool-tip>`
  element. The parser here matches each cell to its tooltip by id, which
  I confirmed against the live page before shipping this.
- `tools/render_graph.py` — tested, produces a clean animated SVG
  (column-by-column reveal, legend, stats line).
- `tools/render_panel.py` — tested, produces the terminal info panel
  with staggered fade-in rows and a blinking cursor. Edit the `ROWS`
  list at the top of the file to change what it says.
- `README.md` and the GitHub Actions workflow are wired up and ready.

## Portrait — already generated
`portrait.svg` is built from your uploaded photo. Worth knowing what
happened in between, since it wasn't a straight run:
- The source photo was sideways (phone selfie), so it got rotated upright first.
- `rembg` needed an `onnxruntime` backend installed and downloaded its
  ~176MB model file on first run -- expected the first time you run
  `clean_photo.py` yourself, just slow.
- The auto-cropped composite came out landscape-oriented with the face
  as a small region in frame, which made the ASCII grid mostly blank
  space. I manually cropped to a tighter portrait-oriented box centered
  on your face/shoulders, and painted out a stray dark artifact (part of
  the car's grab handle) that `rembg` had left attached to the hair
  silhouette.
- If you want to redo it with a different photo later:
  ```
  python -m venv .venv && source .venv/bin/activate
  pip install -r tools/requirements-art.txt
  python tools/clean_photo.py my-photo.jpg
  ```
  Then check `assets/photo-ready.png` -- if the framing is off (subject
  too small, cut off, artifacts from the background), crop/touch it up
  before running `python tools/render_portrait.py`. The renderer just
  maps whatever's in that file to characters; it doesn't detect faces or
  frame automatically.

## Deploying
```
gh repo create ArnavSahu26 --public --clone   # skip if it already exists
# copy all files from this folder into that repo
cd ArnavSahu26
git add -A
git commit -m "profile: living terminal readme"
git push
```
Then go to the Actions tab and manually trigger "Refresh contribution graph"
once (workflow_dispatch) to confirm the daily cron will commit cleanly
before you leave it running.

## Customizing later
- **Panel text**: edit `ROWS` in `tools/render_panel.py`.
- **Color ramp**: `LEVELS` in `render_graph.py` / `FILL_COLOR` in
  `render_portrait.py` — currently both use the same blue accent
  (`#4dabf7`) so the two SVGs feel like one design.
- **Glyph density**: `GLYPHS` in `render_portrait.py`, light-to-dark ramp.
