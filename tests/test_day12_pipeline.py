from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.check_text_template import EXPECTED_FIXTURE_COUNT, run_all_checks  # noqa: E402


def test_day12_text_template_pipeline() -> None:
    ok, errors, passed = run_all_checks()

    assert passed == EXPECTED_FIXTURE_COUNT
    assert ok, "\n".join(errors)


def test_day12_check_script_cli_output() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "check_text_template.py")],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Text template check passed: 10/10" in result.stdout
    assert "Determinism: PASS" in result.stdout
