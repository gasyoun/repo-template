# repo-template — one template for everything (policy-as-code, two layers)

_Created: 06-10-2026 · Last updated: 06-10-2026_

The ONE standalone repo-template (MG ruling 03-10-2026: **one repo, two layers** —
[H5733 §7 rulings](https://github.com/gasyoun/claude-config/blob/main/docs/POLICY_AS_CODE_REPO_TEMPLATE_SPEC_03-10-2026.md),
Q1: standalone repo, against per-repo forks). A new front = a copy of this template +
its own corpus and SLI. Nothing here is forked from the claude-config estate; code and
wiring stay global, per-front data and domain prose live in the copy.

## Layers

| Layer | Owner | Contents | Status |
|---|---|---|---|
| **base/** | H5770 (policy-as-code pack per H5733 §7) | AGENTS.md skeleton, `.agent_policy.json` starter pack v1, test fixtures + guard tests, installer pointer in claude-config | reserved — shape + contract documented, content lands per H5770 |
| **front/** | H5636 (this pass) | agent policy (§19), token killgate on the front (§13/R3-Q7), weekly 6 numbers (§20), anonymisation-gate H5562 (R3-Q8), profiles business/science/estate (R3-Q9) | implemented |

## Front layer — the four mandatory files

Every front copy carries these four files (in `front/`):

1. **`policy/agent_policy.yaml`** — agent policy in code (grill-3 §19): tool allowlist
   (default-deny), step/token ceilings, verify-gate before EVERY external action.
2. **`killgate/killgate.json` + `killgate.py`** — hard token killgate ON THE FRONT
   (§13 + R3-Q7): own ceiling per contour, sum of ceilings ≤ monthly subscription cap,
   overflow = auto-stop of the front with a trace file.
3. **`numbers/six_numbers.yaml`** — the six weekly numbers of the front (§20), read in
   the weekly SLO review.
4. **`anonymisation_gate.yaml`** — mandatory anonymisation gate (H5562, R3-Q8): profile
   `ON` on fronts touching personal data; profile `OFF` must carry the exact line
   `ПДн нет, gate OFF`.

Plus **three profiles** — `business / science / estate` (R3-Q9): one template for
everything, against fragmentation. The science profile EXTENDS the science conveyor
(referee / submission-pack) and never replaces it.

## Adopting a new front

1. Copy this repo (GitHub *Use this template*, or `cp -r` of `front/`).
2. Fill in: front name, contours, ceilings, subscription cap, six-number sources, gate
   ON/OFF by personal data, profile.
3. Validate the copy: `python3 dry_check.py examples/content-front` (exit 0 = copy OK).
4. Adoption threshold (R3-Q4): **1 week of SLI wired into goals + gold PASS** before the
   front counts as внедрён (adopted).

## Checks

- `python3 dry_check.py <front-dir>` — validates a front copy (exit 0/1).
- `python3 -m pytest tests/ -q` — killgate negative test (overflow → auto-stop with
  trace) + dry-check self-tests.

## Sources and rulings

- Grill-3 ai-maturity 02-10-2026: R3-Q2 (this template), R3-Q4 (adoption threshold),
  R3-Q7 (killgate on front), R3-Q8 (anonymisation-gate file), R3-Q9 (one template,
  3 profiles), Q18 (content front = лекция→клип).
- H5733 spec + MG rulings 03-10-2026 (Q1–Q9). H5770 = base layer into THIS repo.
- H5562 = 152-FZ anonymisation gate for support history (no gate pass = no ingest).
- Fleet grill 03-10 ruling №6: ceiling shape = median × 1.2 → hard killgate.

_Гасунс_
