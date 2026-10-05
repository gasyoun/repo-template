# repo-template

_Created: 06-10-2026 · Last updated: 06-10-2026_

The ONE standalone template repo (MG ruling 03-10-2026: one repo, two layers —
[H5733 §7 rulings](https://github.com/gasyoun/claude-config/blob/main/docs/POLICY_AS_CODE_REPO_TEMPLATE_SPEC_03-10-2026.md)).

- **base/** layer — H5770 (policy-as-code pack: AGENTS.md skeleton, `.agent_policy.json`
  starter, fixtures + guard tests, installer pointer).
- **front/** layer — H5636 (agent policy §19, token killgate on the front §13/R3-Q7,
  six weekly numbers §20, anonymisation-gate H5562/R3-Q8, profiles business/science/estate R3-Q9).

Layers land as PRs into this repo; a new front = a copy of `front/` + its own corpus
and SLI, validated by `dry_check.py` (adoption threshold R3-Q4: 1 week SLI in goals +
gold PASS).

_Гасунс_
