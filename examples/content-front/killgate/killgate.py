#!/usr/bin/env python3
"""Hard token killgate ON THE FRONT (grill-3 SS13 + R3-Q7, H5636).

Stdlib only, Python >= 3.9 (pyfloor). Reads killgate.json (ceilings per contour,
monthly subscription cap) and usage.jsonl (rows: {"contour": str, "tokens": int}).

Green  -> exit 0, prints per-contour sums vs ceilings and the subscription invariant.
Overflow -> writes TRACE_<ts>.json + STOP marker (auto-stop of the front), exit 2.
Malformed config/usage -> exit 3 (fail loud, never fail-open on a money contour).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

EXIT_OK = 0
EXIT_OVERFLOW = 2
EXIT_MALFORMED = 3


def _load_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"KILLGATE MALFORMED: {path}: {exc}", file=sys.stderr)
        raise SystemExit(EXIT_MALFORMED)


def main(argv: list[str]) -> int:
    args = argv[1:]
    if len(args) >= 2 and args[0] == "--front":
        # <front-dir> is the front root: config lives in <front-dir>/killgate/
        base = Path(args[1]) / "killgate"
    elif args and not args[0].startswith("-"):
        base = Path(args[0]) / "killgate"
    else:
        # no arg: run beside the shipped config (script's own dir)
        base = Path(__file__).resolve().parent
    kg_path = base / "killgate.json"
    usage_path = base / "usage.jsonl"
    cfg = _load_json(kg_path)

    try:
        cap = int(cfg["monthly_subscription_cap_tokens"])
        contours = {c["name"]: int(c["ceiling_tokens"]) for c in cfg["contours"]}
    except (KeyError, TypeError, ValueError) as exc:
        print(f"KILLGATE MALFORMED: bad killgate.json shape: {exc}", file=sys.stderr)
        return EXIT_MALFORMED
    if cap <= 0 or any(v <= 0 for v in contours.values()):
        print("KILLGATE MALFORMED: ceilings and cap must be positive integers", file=sys.stderr)
        return EXIT_MALFORMED

    sums: dict[str, int] = {name: 0 for name in contours}
    if usage_path.exists():
        for lineno, line in enumerate(usage_path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                contour, tokens = str(row["contour"]), int(row["tokens"])
            except (ValueError, KeyError, TypeError) as exc:
                print(f"KILLGATE MALFORMED: usage.jsonl line {lineno}: {exc}", file=sys.stderr)
                return EXIT_MALFORMED
            if contour not in contours:
                print(f"KILLGATE MALFORMED: usage.jsonl line {lineno}: unknown contour {contour!r}", file=sys.stderr)
                return EXIT_MALFORMED
            if tokens < 0:
                print(f"KILLGATE MALFORMED: usage.jsonl line {lineno}: negative tokens", file=sys.stderr)
                return EXIT_MALFORMED
            sums[contour] += tokens

    total = sum(sums.values())
    ceiling_total = sum(contours.values())
    breaches = {c: (sums[c], contours[c]) for c in contours if sums[c] > contours[c]}

    print(f"front={cfg.get('front', '?')} total={total} cap={cap} ceilings_sum={ceiling_total}")
    for name in contours:
        print(f"  contour {name}: {sums[name]}/{contours[name]}")

    stopped = False
    if ceiling_total > cap:
        # invariant: sum of per-contour ceilings must fit the monthly subscription
        breaches["<ceilings-sum-vs-cap>"] = (ceiling_total, cap)
    if breaches:
        ts = int(time.time())
        trace = {
            "front": cfg.get("front"),
            "stopped_at": ts,
            "stop_reason": "token ceiling overflow -> auto-stop of the front (R3-Q7)",
            "monthly_subscription_cap_tokens": cap,
            "ceilings_sum": ceiling_total,
            "total_observed": total,
            "breaches": [
                {"contour": c, "observed": obs, "ceiling": ceil, "overflow": obs - ceil}
                for c, (obs, ceil) in sorted(breaches.items())
            ],
        }
        trace_path = base / f"TRACE_{ts}.json"
        trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
        (base / "STOP").write_text(
            f"auto-stop {ts}: ceiling overflow, see {trace_path.name}\n", encoding="utf-8"
        )
        print(f"KILLGATE STOP: overflow, trace={trace_path}", file=sys.stderr)
        stopped = True
    else:
        print("KILLGATE OK: no overflow")
    return EXIT_OVERFLOW if stopped else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
