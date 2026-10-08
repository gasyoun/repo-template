# front/ — the front layer (H5636)

_Created: 06-10-2026 · Last updated: 08-10-2026_

> **Pointer note (H5770):** the front layer builds and lives HERE, in
> `gasyoun/repo-template` — never a second template repo; the base layer
> ([`base/`](../base/README.md), policy pack) landed 08-10-2026 and the installer
> never touches `front/`.

A **front** is one work contour of the estate (content, business, science, …). This
layer is the portable AI-practice unit (grill-3 ai-maturity 02-10, R3-Q2): one template
for EVERYTHING — against рек/fragmentation (R3-Q9). A new front = copy of this
directory + its own corpus and SLI. The layer is OPTIONAL for a repo that only wants
the base policy pack (H5770); it is MANDATORY for any front that runs agents.

## The four mandatory files

| # | File | Contract | Source ruling |
|---|---|---|---|
| 1 | `policy/agent_policy.yaml` | tool allowlist (default-deny), step/token ceilings, verify-gate before EVERY external action | §19 |
| 2 | `killgate/killgate.json` (+ `killgate.py`) | own ceiling per contour; Σ ceilings ≤ monthly subscription cap; overflow = auto-stop of the front with trace | §13, R3-Q7 |
| 3 | `numbers/six_numbers.yaml` | the six weekly numbers of the front, read in the weekly SLO review | §20 |
| 4 | `anonymisation_gate.yaml` | gate ON with a profile on fronts with ПДн; OFF carries the exact line `ПДн нет, gate OFF`; no gate pass = no ingest | H5562, R3-Q8 |

## Profiles (exactly three — R3-Q9)

`profiles/business.yaml`, `profiles/science.yaml`, `profiles/estate.yaml`. A copy MUST
keep all three (a template with one profile is not this template). The science profile
EXTENDS the science conveyor — `/paper-referee`, `/paper-submission-pack` pipeline
stays unbroken; the profile may only add gates around it, never replace conveyor steps.

## Copy + validation loop

```
cp -r front/ <my-front>/
# fill front name, contours, ceilings, subscription cap, numbers sources, gate, profile
python3 dry_check.py <my-front>        # exit 0 = valid copy
```

## Adoption threshold (R3-Q4)

A front counts as adopted only after: **1 week of SLI wired into goals + gold PASS**.
Before that the front is a pilot: its numbers are recorded, its killgate live, but it
does not count towards pervasiveness.

## Killgate operation

- The front runner records token usage per contour into `killgate/usage.jsonl`
  (`{"contour": "...", "tokens": N}` rows).
- After every batch (and at front start) run
  `python3 killgate/killgate.py --front <front-dir>`: it sums per-contour usage against
  the per-contour ceiling and the Σ ≤ monthly-subscription invariant.
- On overflow it writes `killgate/TRACE_<ts>.json` (the trace: contour, ceiling,
  observed, overflow, front, stopped_at) and `killgate/STOP` (the auto-stop marker),
  then exits 2. The front runner treats STOP as a hard halt — no further contours run
  until a human lifts the stop (delete STOP + record why in the trace dir).
- Ceiling derivation idiom (fleet grill 03-10, ruling №6): ceiling = median weekly
  burn × 1.2, rounded — then the Σ ≤ subscription cap check.
