"""Shared test setup: make the repository root importable, provide a fake `gh`.

The two production scripts (`file_cards.py`, `merge_card.py`) live at the
repository root. `python3 -m pytest` puts the root on `sys.path` via the
working directory, but a bare `pytest` invocation does not — this conftest
makes both invocation styles equivalent.
"""
import json
import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def install_fake_gh(directory, monkeypatch, *, stdout="", stderr="", rc=0,
                    sleep_s=0, argv_log=None, rules=None):
    """Write a deterministic fake `gh` executable into `directory` and put it on PATH.

    Single-response mode (default): every invocation gets `stdout`/`stderr`/`rc`.
    Rule-scripted mode (`rules`): a list of `(argv_substring, response)` pairs
    checked in order — first match wins; a call matching no rule falls back to
    the single response. A `response` is a dict whose `stdout`/`stderr`/`rc` keys
    (missing keys default to ""/""/0) select that call's behaviour, so one fake
    can deterministically drive a whole multi-endpoint flow (auth status, user,
    repo read, contents, compare) where each endpoint answers differently.
    """
    fallback = {"stdout": stdout, "stderr": stderr, "rc": int(rc)}
    scripted = [[str(pat), {"stdout": str(resp.get("stdout", "")),
                            "stderr": str(resp.get("stderr", "")),
                            "rc": int(resp.get("rc", 0))}]
                for pat, resp in (rules or [])]
    lines = [
        "#!/usr/bin/env python3",
        "import pathlib, sys, time",
        f"rules = {json.dumps(scripted)}",
        f"fallback = {json.dumps(fallback)}",
        "argv = ' '.join(sys.argv[1:])",
        "resp = fallback",
        "for pat, r in rules:",
        "    if pat in argv:",
        "        resp = r",
        "        break",
    ]
    if argv_log is not None:
        lines.append(f"pathlib.Path({str(argv_log)!r}).write_text(argv)")
    if sleep_s:
        lines.append(f"time.sleep({float(sleep_s)!r})")
    lines.append("sys.stdout.write(resp['stdout'])")
    lines.append("sys.stderr.write(resp['stderr'])")
    lines.append("sys.exit(resp['rc'])")
    exe = directory / "gh"
    exe.write_text("\n".join(lines) + "\n", encoding="utf-8")
    exe.chmod(0o755)
    monkeypatch.setenv("PATH", f"{directory}{os.pathsep}{os.environ.get('PATH', '')}")
    return directory


@pytest.fixture
def fake_gh(tmp_path, monkeypatch):
    """Factory fixture: install a fake `gh` on PATH with the given behaviour.

    Deterministic, offline, and self-verifying: tests that assert on the fake's
    argv log or output prove the fake (not a real gh) answered the call.
    """
    def make(**kwargs):
        return install_fake_gh(tmp_path, monkeypatch, **kwargs)

    return make
