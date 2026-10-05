#!/usr/bin/env python3
"""dry_check.py — validate a copy of the front template (H5636).

Usage:  python3 dry_check.py <front-dir>        (default: front)

Exit 0 = the copy is a valid front (four mandatory files + three profiles, all
contracts met). Exit 1 = FAIL, every defect listed. Stdlib only (Python >= 3.9);
if PyYAML happens to be installed it is used for a deep parse, else a line scanner
validates structure. Both paths are flattened to dotted keys before checking.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SIX_NUMBERS = (
    "land_rate",
    "sl_attainment",
    "token_spend",
    "killgate_trips",
    "gate_verdicts",
    "queue_freshness",
)
PROFILES = ("business.yaml", "science.yaml", "estate.yaml")
PLACEHOLDER = re.compile(r"<[a-z0-9-]+>")
WEEK = re.compile(r"^\d{4}-W\d{2}$")


def flatten(obj, prefix: str = "") -> dict:
    out: dict = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, dict):
                out.update(flatten(v, key))
            else:
                out[key] = v
    elif prefix:
        out[prefix] = obj
    return out


def scan_keys(text: str) -> dict:
    """Minimal indentation-aware `key: value` + `- item` scanner -> dotted keys."""
    out: dict = {}
    stack: list[tuple[int, str]] = []
    last_key: tuple[int, str] | None = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        while stack and indent <= stack[-1][0]:
            stack.pop()
        item = re.match(r"^(\s*)-\s+(.*?)\s*$", line)
        if item:
            _, val = item.groups()
            if last_key and indent > last_key[0]:
                out[f"{last_key[1]}.{val}"] = ""
                continue
            continue
        m = re.match(r"^(\s*)([A-Za-z_][\w]*):\s*(.*?)\s*$", line)
        if not m:
            continue
        _, key, val = m.groups()
        path = ".".join([s for _, s in stack] + [key])
        stack.append((indent, key))
        last_key = (indent, path)
        if val:
            v = val.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            out[path] = v
    return out


def load_flat_yaml(text: str) -> dict:
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        if isinstance(data, dict):
            return flatten(data)
    except ImportError:
        pass
    return scan_keys(text)


class Check:
    def __init__(self, front_dir: Path) -> None:
        self.dir = front_dir
        self.errors: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def text(self, rel: str) -> str:
        p = self.dir / rel
        if not p.is_file():
            self.err(f"missing mandatory file: {rel}")
            return ""
        return p.read_text(encoding="utf-8")

    def yaml_kv(self, rel: str) -> dict:
        text = self.text(rel)
        return load_flat_yaml(text) if text else {}

    # ---------- the four mandatory files ----------
    def check_policy(self) -> None:
        kv = self.yaml_kv("policy/agent_policy.yaml")
        if not kv:
            return
        front = str(kv.get("front", ""))
        if not front or PLACEHOLDER.search(front):
            self.err("policy: front name not filled")
        if str(kv.get("tools.default", "")).strip().lower() != "deny":
            self.err("policy: tools.default must be 'deny' (SS19 allowlist, default-deny)")
        if "tools.allow.read" not in kv and "tools.allow" not in kv:
            self.err("policy: tools.allow list empty or missing")
        for key in ("ceilings.max_steps_per_task", "ceilings.max_tokens_per_task"):
            try:
                if int(kv.get(key, 0)) <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                self.err(f"policy: {key} must be a positive integer")
        if not any(k.startswith("verify_gate.required_before") for k in kv):
            self.err("policy: verify_gate.required_before missing (SS19: gate before EVERY external action)")
        else:
            flat = " ".join(
                str(v) for k, v in kv.items() if k.startswith("verify_gate.required_before")
            ) + " " + " ".join(
                k for k in kv if k.startswith("verify_gate.required_before")
            )
            if "git push" not in flat:
                self.err("policy: verify_gate.required_before must include 'git push'")
        if str(kv.get("verify_gate.on_fail", "")).strip().lower() not in ("block", "confirm"):
            self.err("policy: verify_gate.on_fail must be block|confirm (never silent)")

    def check_killgate(self) -> None:
        text = self.text("killgate/killgate.json")
        if not text:
            return
        try:
            cfg = json.loads(text)
        except ValueError as exc:
            self.err(f"killgate: killgate.json not valid JSON: {exc}")
            return
        cap = cfg.get("monthly_subscription_cap_tokens")
        contours = cfg.get("contours")
        if not isinstance(cap, int) or cap <= 0:
            self.err("killgate: monthly_subscription_cap_tokens must be a positive int")
            cap = 0
        if not isinstance(contours, list) or not contours:
            self.err("killgate: contours list empty (own ceiling per contour, R3-Q7)")
            contours = []
        total = 0
        for c in contours:
            ceil = c.get("ceiling_tokens")
            if not isinstance(ceil, int) or ceil <= 0:
                self.err(f"killgate: contour {c.get('name')!r} ceiling_tokens must be positive")
                ceil = 0
            total += ceil
        if cap and total > cap:
            self.err(
                f"killgate: sum of ceilings ({total}) exceeds monthly subscription cap ({cap}) — R3-Q7 invariant"
            )
        ov = cfg.get("overflow") or {}
        if ov.get("action") != "auto_stop":
            self.err("killgate: overflow.action must be 'auto_stop'")
        if not ov.get("trace") or not ov.get("stop_marker"):
            self.err("killgate: overflow trace and stop_marker required (auto-stop with trace)")
        if (self.dir / "killgate" / "STOP").exists():
            self.err("killgate: front is in STOP state — lift (human) before dry-check passes")

    def check_numbers(self) -> None:
        kv = self.yaml_kv("numbers/six_numbers.yaml")
        if not kv:
            return
        if not WEEK.match(str(kv.get("week", ""))):
            self.err("numbers: week must be ISO 'YYYY-Www'")
        missing = [
            n
            for n in SIX_NUMBERS
            if not any(k == f"numbers.{n}" or k.startswith(f"numbers.{n}.") for k in kv)
        ]
        if missing:
            self.err(f"numbers: missing weekly number slots: {missing} (SS20 — exactly six)")
        thr = str(kv.get("adoption_threshold.requires", ""))
        if "1 week" not in thr or "gold" not in thr.lower():
            self.err("numbers: adoption_threshold.requires must name '1 week SLI + gold PASS' (R3-Q4)")

    def check_gate(self) -> None:
        text = self.text("anonymisation_gate.yaml")
        if not text:
            return
        raw = self.yaml_kv("anonymisation_gate.yaml").get("gate", "")
        # YAML 1.1 parses bare ON/OFF as booleans — accept both spellings
        gate = {True: "ON", False: "OFF"}.get(raw, str(raw).strip().upper())
        if gate == "OFF":
            if "ПДн нет, gate OFF" not in text:
                self.err("gate: OFF profile must carry the exact line 'ПДн нет, gate OFF' (R3-Q8)")
        elif gate == "ON":
            kv = self.yaml_kv("anonymisation_gate.yaml")
            if not any(k.startswith("pii_classes") for k in kv):
                self.err("gate: ON profile needs pii_classes (H5562)")
            if "no gate pass = no ingest" not in text:
                self.err("gate: ON profile needs the hard rule 'no gate pass = no ingest' (H5562)")
        else:
            self.err("gate: gate must be ON or OFF")

    # ---------- profiles ----------
    def check_profiles(self) -> None:
        pdir = self.dir / "profiles"
        if not pdir.is_dir():
            self.err("profiles: profiles/ directory missing (R3-Q9 — three profiles)")
            return
        files = sorted(p.name for p in pdir.glob("*.yaml"))
        if files != sorted(PROFILES):
            self.err(f"profiles: expected exactly {sorted(PROFILES)}, found {files}")
        science = self.text("profiles/science.yaml")
        if science:
            if "conveyor_preserved" not in science:
                self.err("profiles/science: conveyor_preserved missing (H5636 Fail clause)")
            if "paper-referee" not in science or "paper-submission-pack" not in science:
                self.err("profiles/science: must name paper-referee AND paper-submission-pack (conveyor unbroken)")

    def check_filled(self) -> None:
        for p in sorted(self.dir.rglob("*")):
            if p.is_file() and p.suffix in (".yaml", ".json", ".md") and "TRACE_" not in p.name:
                hits = [
                    h
                    for h in PLACEHOLDER.findall(p.read_text(encoding="utf-8", errors="replace"))
                    if h != "<unix-ts>"  # intentional trace filename pattern
                ]
                if hits:
                    self.err(f"unfilled template placeholder(s) {sorted(set(hits))} in {p.relative_to(self.dir)}")

    def run(self) -> int:
        for step in (
            self.check_policy,
            self.check_killgate,
            self.check_numbers,
            self.check_gate,
            self.check_profiles,
            self.check_filled,
        ):
            step()
        if self.errors:
            print(f"DRY-CHECK FAIL: {self.dir} ({len(self.errors)} defect(s))")
            for e in self.errors:
                print(f"  - {e}")
            return 1
        print(f"DRY-CHECK PASS: {self.dir} — 4 mandatory files + 3 profiles, all contracts met")
        return 0


def main(argv: list[str]) -> int:
    front_dir = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent / "front"
    if not front_dir.is_dir():
        print(f"DRY-CHECK FAIL: {front_dir} is not a directory")
        return 1
    return Check(front_dir).run()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
