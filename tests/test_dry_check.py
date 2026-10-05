"""dry_check self-tests (H5636): the pilot copy passes; corrupted copies fail;
the scanner fallback (no PyYAML on the box) reaches the same verdicts."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DRY_CHECK = REPO / "dry_check.py"
EXAMPLE = REPO / "examples" / "content-front"


def run(target: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(DRY_CHECK), str(target)], capture_output=True, text=True
    )


def test_pilot_copy_passes():
    r = run(EXAMPLE)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "DRY-CHECK PASS" in r.stdout


def test_pristine_template_fails_on_placeholders(tmp_path):
    copy = tmp_path / "t"
    shutil.copytree(REPO / "front", copy)
    r = run(copy)
    assert r.returncode == 1
    assert "placeholder" in r.stdout


def test_missing_profile_fails(tmp_path):
    copy = tmp_path / "t"
    shutil.copytree(EXAMPLE, copy)
    (copy / "profiles" / "science.yaml").unlink()
    r = run(copy)
    assert r.returncode == 1
    assert "profiles" in r.stdout


def test_gate_off_requires_the_exact_line(tmp_path):
    copy = tmp_path / "t"
    shutil.copytree(EXAMPLE, copy)
    g = copy / "anonymisation_gate.yaml"
    g.write_text("schema_version: 1\nfront: content-front\ngate: OFF\n", encoding="utf-8")
    r = run(copy)
    assert r.returncode == 1
    assert "ПДн нет, gate OFF" in r.stdout
    # with the exact line present the gate check passes again
    g.write_text(
        "schema_version: 1\nfront: content-front\ngate: OFF\nreason: ПДн нет, gate OFF\n",
        encoding="utf-8",
    )
    r2 = run(copy)
    assert "gate" not in "\n".join(
        line for line in r2.stdout.splitlines() if line.startswith("  - ")
    )


def test_scanner_fallback_same_verdict(tmp_path, monkeypatch):
    """No-PyYAML box: the line scanner must reach the same PASS on the pilot copy."""
    copy = tmp_path / "t"
    shutil.copytree(EXAMPLE, copy)
    monkeypatch.setitem(sys.modules, "yaml", None)  # forces ImportError -> scanner
    sys.argv = ["dry_check.py", str(copy)]
    import importlib

    spec = importlib.util.spec_from_file_location("dc_fallback", DRY_CHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    kv = mod.load_flat_yaml((copy / "policy" / "agent_policy.yaml").read_text(encoding="utf-8"))
    assert kv["tools.default"] == "deny", "scanner must see nested scalar"
    assert any(k.startswith("verify_gate.required_before.git push") for k in kv), (
        "scanner must capture allowlist items"
    )
    rc = mod.main(sys.argv)
    assert rc == 0
