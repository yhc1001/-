# AGENTS.md

## Project Map
- Entry point: `app.py`
- Static image assets: `EER.png`, `MOF.png`, `RTU.png`, `전력량계.png`, `한전.png`, `기존공기압축기.png`, `효율공기압축기.png`
- Font assets: `MALGUN.TTF`, `MALGUNBD.TTF`, `MALGUNSL.TTF`
- Dependency files: `requirements.txt`, `packages.txt`

## Must Preserve
- Keep Korean text rendering compatible with the bundled Malgun font files.
- Keep image asset filenames stable unless every reference is updated.
- Do not replace real equipment/diagram assets with generic placeholders.

## Work Notes
- Start with `app.py`; most behavior appears to live there.
- When changing layout or export rendering, verify that Korean text and PNG assets still render.
- Avoid adding new large assets unless the task requires them.

## Verification
- After Python edits, run: `python -m compileall .`
- For visual/layout changes, run the app or inspect generated output when practical.
