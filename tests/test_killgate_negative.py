"""Negative killgate test (H5636 acceptance): ceiling overflow -> auto-stop of the
front with a trace attached. Plus the SS<=subscription invariant and green path."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
KILLGATE = REPO / "front" / "killgate" / "killgate.py"


def make_front(tmp_path: Path, cap: int, contours: dict, usage: list) -> Path:
    d = tmp_path / "front-under-test"
    (d / "killgate").mkdir(parents=True)
    (d / "killgate" / "killgate.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "front": "test-front",
                "monthly_subscription_cap_tokens": cap,
                "contours": [
                    {"name": n, "ceiling_tokens": c, "median_weekly_burn_tokens": c}
                    for n, c in contours.items()
                ],
                "overflow": {
                    "action": "auto_stop",
                    "trace": "killgate/TRACE_<unix-ts>.json",
                    "stop_marker": "killgate/STOP",
                },
            }
        ),
        encoding="utf-8",
    )
    (d / "killgate" / "usage.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in usage), encoding="utf-8"
    )
    return d


def run(front_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KILLGATE), "--front", str(front_dir)],
        capture_output=True,
        text=True,
    )


def test_overflow_auto_stop_with_trace(tmp_path):
    """R3-Q7 negative: contour burn 150 over a 100 ceiling -> exit 2, STOP, trace."""
    d = make_front(tmp_path, cap=1000, contours={"c1": 100}, usage=[{"contour": "c1", "tokens": 150}])
    r = run(d)
    assert r.returncode == 2, r.stderr
    assert (d / "killgate" / "STOP").is_file(), "auto-stop marker missing"
    traces = list((d / "killgate").glob("TRACE_*.json"))
    assert traces, "trace file missing"
    trace = json.loads(traces[0].read_text(encoding="utf-8"))
    assert trace["front"] == "test-front"
    assert trace["breaches"] == [{"contour": "c1", "observed": 150, "ceiling": 100, "overflow": 50}]
    assert "overflow" in trace["stop_reason"]
    # idempotent stop: second run still exit 2, still exactly the same verdict
    r2 = run(d)
    assert r2.returncode == 2
    assert json.loads(traces[0].read_text(encoding="utf-8"))["breaches"][0]["overflow"] == 50


def test_ceilings_sum_over_cap_stops_even_with_zero_usage(tmp_path):
    """R3-Q7 invariant: sum of ceilings > monthly subscription cap -> auto-stop."""
    d = make_front(tmp_path, cap=1000, contours={"a": 600, "b": 600}, usage=[])
    r = run(d)
    assert r.returncode == 2, r.stderr
    trace = json.loads(next((d / "killgate").glob("TRACE_*.json")).read_text(encoding="utf-8"))
    assert trace["breaches"][0]["contour"] == "<ceilings-sum-vs-cap>"


def test_green_path_and_multi_row_sum(tmp_path):
    d = make_front(
        tmp_path, cap=1000, contours={"a": 600, "b": 400},
        usage=[{"contour": "a", "tokens": 300}, {"contour": "a", "tokens": 200}, {"contour": "b", "tokens": 350}],
    )
    r = run(d)
    assert r.returncode == 0, r.stderr
    assert "contour a: 500/600" in r.stdout
    assert "contour b: 350/400" in r.stdout
    assert "KILLGATE OK" in r.stdout
    assert not (d / "killgate" / "STOP").exists()


def test_malformed_usage_fails_loud(tmp_path):
    d = make_front(tmp_path, cap=1000, contours={"a": 600}, usage=[])
    (d / "killgate" / "usage.jsonl").write_text('{"contour": "zzz", "tokens": 1}\n', encoding="utf-8")
    r = run(d)
    assert r.returncode == 3, "unknown contour must fail loud (exit 3), never fail-open"
