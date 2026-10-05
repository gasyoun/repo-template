# base/ — RESERVED for H5770 (base layer)

_Created: 06-10-2026 · Last updated: 06-10-2026_

**Do not implement here — H5770 owns the base layer of THIS repo** (MG ruling
03-10-2026: one repo, two layers). This file documents the reserved shape only, so the
front layer (H5636, `front/`) and the base layer never collide.

## Layer contract (per H5733 §7 rulings + H5770 mission)

The base layer packages, into adopting repos:

1. `AGENTS.md` skeleton (1 page) — dated header + byline, closers, pointer to the
   policy pack; domain prose goes on top (ruling Q4).
2. `.agent_policy.json` starter pack v1 — secret-path deny + audit rules, with
   `schema_version` (rulings Q3, Q5). Per-repo DATA, not code.
3. Test fixtures + guard tests INSIDE the template — the template must be verifiable
   on a box that never cloned claude-config (ruling Q9).
4. Installer: `claude-config scripts/install_repo_template.py` — idempotent, version
   stamped, appends the AGENTS.md skeleton without overwriting, prints the
   `settings.json` PreToolUse wiring snippet (rulings Q2, Q7).

## Boundary rule (H5733 §2)

Code and wiring are global (claude-config estate); data and domain prose are per-repo.
Absence of `.agent_policy.json` = designed pass-through, not a defect (ruling Q6:
silence by design).

## Update path

Re-run the installer; template version is stamped into scaffolded files so drift is
visible (ruling Q7). The front layer (`front/`) is OPTIONAL per adopting repo and is
never touched by the installer.
