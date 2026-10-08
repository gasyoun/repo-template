# base/ — the base layer (policy-as-code pack, H5770)

_Created: 06-10-2026 · Last updated: 08-10-2026_

The BASE layer of the ONE repo-template (MG ruling 03-10-2026: one repo, two
layers — [H5733 §7 rulings](https://github.com/gasyoun/claude-config/blob/main/docs/POLICY_AS_CODE_REPO_TEMPLATE_SPEC_03-10-2026.md)).
It packages what every adopting repo gets from day one. The front layer
([`front/`](../front/README.md), H5636) is OPTIONAL and builds in THIS same repo —
never a second template repo.

## What ships (per H5733 §7 Q1–Q4, Q7, Q9)

| # | File | What it is |
|---|---|---|
| 1 | [`AGENTS.md`](AGENTS.md) | 1-page skeleton: dated header/byline, house contracts, pointer to the pack — inside managed markers so re-runs refresh it without touching your prose (Q4, Q7) |
| 2 | [`.agent_policy.json`](.agent_policy.json) | starter pack v1, `schema_version` "1": secret-file deny (block) + force-push and package-publish (audit); per-repo DATA — edit it, it is yours (Q3, Q5) |
| 3 | [`tests/`](tests/) | pack fixtures + guard tests that run on a box that NEVER cloned claude-config (Q9) |
| 4 | installer | `claude-config scripts/install_repo_template.py` scaffolds this layer into an existing repo — idempotent, version-stamped, never clobbers your content (Q2, Q7) |

The runtime guard is NOT vendored here: code and wiring stay GLOBAL (claude-config
estate, one deployed copy per box); data and domain prose are per-repo (H5733 §2
boundary rule). The installer prints the one-time `settings.json` PreToolUse wiring
snippet pointing at the deployed guard.

## Install into a repo

```
python3 scripts/install_repo_template.py /path/to/repo   # from a claude-config clone
```

Second run is byte-idempotent; drift is visible via the stamped template version
(`base/TEMPLATE_VERSION`, echoed into the managed AGENTS block and reported for the
pack). The adopter-edited pack is NEVER overwritten.

## Verify this layer standalone (no claude-config needed)

```
python3 -m unittest discover -s base/tests -v
```

- `tests/agent_policy_mirror.py` — trimmed, provenance-marked mirror of the estate
  matcher (`hooks/agent_policy.py`), test-only; no hook_config clause parsing, raw-text
  fallback semantics.
- `tests/test_base_pack.py` — the starter pack: validates, blocks a secret-path write
  and a secret-file read, passes clean calls, honours override markers, audits
  force-push/publish, fails CLOSED on a malformed pack, passes through on absence.

On a wired box also cross-check against the real guard:
`python ~/.claude/hooks/agent_policy.py --check base/.agent_policy.json`.

## Layer contract + boundary rule

Unchanged from the original reservation:

1. `AGENTS.md` skeleton — domain prose goes on top (Q4).
2. `.agent_policy.json` starter pack — per-repo DATA, not code (Q3/Q5).
3. Test fixtures + guard tests INSIDE the template (Q9).
4. Installer in claude-config `scripts/` (Q2), re-run to update (Q7).

**Boundary rule (H5733 §2):** code and wiring are global; data and domain prose are
per-repo. Absence of `.agent_policy.json` = designed pass-through, not a defect
(Q6: silence by design). No per-repo `rules/` tree — everything inline in AGENTS.md
(Q7b). The front layer (`front/`) is never touched by the installer.

_H5733 §7 rulings + H5770. Prior art: [H5733 spec](https://github.com/gasyoun/claude-config/blob/main/docs/POLICY_AS_CODE_REPO_TEMPLATE_SPEC_03-10-2026.md)._
