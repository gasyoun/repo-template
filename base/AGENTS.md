<!-- repo-template:agents-skeleton:v{{TEMPLATE_VERSION}} START — managed block, refreshed by claude-config scripts/install_repo_template.py; text ABOVE and BELOW the markers is yours and is never touched -->

# {{REPO_NAME}} — agent working contract

_Created: {{INSTALL_DATE}} · Last updated: {{INSTALL_DATE}}_

_Byline: <author name in the document's language, e.g. `Dr. Mārcis Gasūns` (EN) / `к.ф.н. М.Ю. Гасунс` (RU)>_

## Project policy pack (policy-as-code)

This repo carries `.agent_policy.json` (repo-template base starter pack, template
v{{TEMPLATE_VERSION}}). The global guard (`~/.claude/hooks/guard_project_policy.py`,
one box-wide `settings.json` PreToolUse entry — see the installer output) resolves
cwd → git repo root → `.agent_policy.json` and enforces it on every covered call:

- rules evaluate in order, **first match wins**: `block` (call prevented, reason on
  stderr), `confirm` (harness asks the human), `audit` (logged, call proceeds);
- a malformed pack fails **CLOSED** (every covered call in the repo blocks loudly)
  — validate after edits: `python ~/.claude/hooks/agent_policy.py --check .agent_policy.json`;
- a shell command carrying a rule's literal override marker (e.g. `[env-edit-ok]`)
  bypasses THAT rule only, never the pack;
- a repo with NO pack is a designed pass-through — absence is not a defect.

**Edit the pack for this repo's real fences** (secret paths, money contours,
private-data dirs): every rule needs an `id` + a `reason` a human can read.

## House contracts this skeleton carries

- Dated header + byline on every authored document (real git dates; bare surname
  is never a valid byline).
- Closer contract: end work on the concrete outcome; human-decision items get
  options + facts + one recommendation, never a named decision-maker.
- Code and wiring are GLOBAL (the estate); data and domain prose are PER-REPO.
  Per-repo `rules/` trees are banned — everything inline here (H5733 §7 Q7b).

## Updating this skeleton

Re-run the installer (`python scripts/install_repo_template.py <repo-root>` in a
claude-config clone): the managed block between the markers is refreshed to the
current template version; your text above/below the markers is preserved. The
scaffolded pack is never overwritten once you have edited it.

<!-- repo-template:agents-skeleton END -->
