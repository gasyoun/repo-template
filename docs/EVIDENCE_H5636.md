# H5636 evidence — front layer of repo-template

_Created: 06-10-2026 · Last updated: 06-10-2026_

Acceptance proofs for H5636 (front layer: policy §19, killgate §13/R3-Q7, six numbers
§20, anonymisation-gate H5562/R3-Q8, three profiles R3-Q9). All outputs below are real
captured runs on this machine, 06-10-2026; re-run any of them from the repo root.

## 1. dry_check on the content-front copy (лекция→клип, Q18) — exit 0

```
$ python3 dry_check.py examples/content-front
DRY-CHECK PASS: examples/content-front — 4 mandatory files + 3 profiles, all contracts met
$ echo $?
0
```

## 2. Negative killgate test — overflow → auto-stop of the front with trace

Copy of `examples/content-front` with `usage.jsonl` rows summing transcribe to 315 000
against a 300 000 ceiling (cap 800 000, Σ ceilings 600 000):

```
$ python3 front/killgate/killgate.py --front <overflow-copy>
KILLGATE STOP: overflow, trace=.../killgate/TRACE_1791237891.json
front=content-front total=315000 cap=800000 ceilings_sum=600000
  contour transcribe: 315000/300000
  contour clip_cut: 0/240000
  contour upload: 0/60000
exit=2

$ cat <overflow-copy>/killgate/STOP
auto-stop 1791237891: ceiling overflow, see TRACE_1791237891.json

$ cat <overflow-copy>/killgate/TRACE_1791237891.json
{
  "front": "content-front",
  "stopped_at": 1791237891,
  "stop_reason": "token ceiling overflow -> auto-stop of the front (R3-Q7)",
  "monthly_subscription_cap_tokens": 800000,
  "ceilings_sum": 600000,
  "total_observed": 315000,
  "breaches": [
    {"contour": "transcribe", "observed": 315000, "ceiling": 300000, "overflow": 15000}
  ]
}
```

Green path (clean example copy): `exit=0`, `KILLGATE OK: no overflow`, no STOP.

## 3. Test suite — 9 passed

```
$ python3 -m pytest tests/ -q
9 passed, 34 warnings in 0.51s
```

Coverage: overflow auto-stop + trace + idempotent re-stop; Σ-ceilings ≤ cap invariant
(fires even at zero usage); green path with multi-row sums; unknown contour fails loud
(exit 3, never fail-open); dry-check pass on the pilot copy; pristine template fails on
placeholders; missing profile fails; gate OFF without the exact «ПДн нет, gate OFF»
line fails; scanner fallback (box without PyYAML) reaches the same verdicts.

## 4. Science conveyor unbroken (R3-Q9 / H5636 Fail clause)

`front/profiles/science.yaml` carries `conveyor_preserved: true` and names
`paper-referee` + `paper-submission-pack` + `articles-update` as conveyor steps the
profile may only wrap with gates, never remove/rename/reorder; `dry_check.py`
enforces the naming + the flag on every copy.

## 5. Layers

- `front/` = implemented front layer (this handoff).
- `base/` = reserved shape + layer contract for H5770 (MG 03-10-2026: one repo, two
  layers — no second template repo).
