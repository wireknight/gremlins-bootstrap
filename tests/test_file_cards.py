"""Focused regression tests for the offline logic of `file_cards.py`.

Pinned surface (the decision logic that must never depend on a model):
- `validate_cards` — the card-file contract gate (structure, routing fields,
  required sections, DESIGN SELF-CHECK items, forbidden Evidence section);
- `first_line` — the first-output-line selector used in every steering message;
- `Steer` — the steering-line format `<PREFIX> <rule>: <measured> -- <fix>`;
- `gh` — the wrapper's rc/stdout/stderr contract and the timeout -> 124 rule;
- the re-run contract ("Safe to re-run"): `seed_file` unchanged, already-filed
  cards skipped, `validate_cards` stable across runs;
- hostile input: shell-metacharacter titles reach `gh` verbatim as one argv
  element; junk slurp pages are skipped, not crashed on.

No network is touched: `gh` is exercised only through the PATH-injected fake
from `conftest.fake_gh`, and every such test asserts on the fake's output or
argv log, proving the simulation took effect.
"""
import base64
import json
import sys

import file_cards

B01 = "B0.1-steps.md"


def install_card_set(target, rewrite=None):
    """Copy the real card set into `target`, optionally rewriting one file's text.

    `rewrite` is `(filename, fn)`; `fn` receives the file's text and returns
    the mutated text. Copying the real set (not a synthetic one) keeps the
    error-path tests faithful: the mutation is the ONLY difference from a
    passing tree.
    """
    for src in sorted(file_cards.HERE.glob("*.md")):
        text = src.read_text(encoding="utf-8")
        if rewrite and src.name == rewrite[0]:
            text = rewrite[1](text)
        (target / src.name).write_text(text, encoding="utf-8")


def redirected(monkeypatch, tmp_path):
    """Point `validate_cards` at the copied card set."""
    monkeypatch.setattr(file_cards, "HERE", tmp_path)


# --- first_line -------------------------------------------------------------


def test_first_line_returns_the_first_line_of_the_first_nonempty_text():
    assert file_cards.first_line("", "  \n  first line\nsecond", "later") == "first line"
    assert file_cards.first_line("only") == "only"
    assert file_cards.first_line("", "   ", "\n") == "no output"
    assert file_cards.first_line() == "no output"


# --- Steer -------------------------------------------------------------------


def test_steer_carries_the_steering_line_and_short_str():
    exc = file_cards.Steer("AUTH-ERROR", "not-logged-in",
                           "gh auth status failed", "run the login step")
    assert exc.line == ("AUTH-ERROR not-logged-in: gh auth status failed "
                        "\u2014 run the login step")
    assert str(exc) == "AUTH-ERROR not-logged-in: gh auth status failed"
    assert isinstance(exc, Exception)


# --- validate_cards: the real set passes -------------------------------------


def test_validate_cards_accepts_the_real_card_set():
    cards = file_cards.validate_cards()
    assert [name for name, _title, _body in cards] == list(file_cards.ORDER)
    for name, title, body in cards:
        assert title, f"{name}: empty title"
        assert "\n" not in title, f"{name}: title spans lines"
        assert "## Evidence" not in body, f"{name}: evidence section leaked into the card"


def test_cards_directory_is_exactly_the_order():
    on_disk = sorted(p.name for p in file_cards.HERE.glob("*.md"))
    assert on_disk == sorted(file_cards.ORDER), (
        "every card file on disk must be listed in file_cards.ORDER "
        "(validate_cards silently ignores files missing from ORDER)")


# --- validate_cards: every refusal names the file and the exact defect --------


def test_validate_cards_refuses_a_missing_card_file(tmp_path, monkeypatch):
    install_card_set(tmp_path)
    (tmp_path / B01).unlink()
    redirected(monkeypatch, tmp_path)
    try:
        file_cards.validate_cards()
    except ValueError as exc:
        assert f"missing card file: {B01}" in str(exc)
    else:
        raise AssertionError("missing card file was accepted")


def test_validate_cards_refuses_a_card_without_a_title_line(tmp_path, monkeypatch):
    install_card_set(tmp_path, rewrite=(B01, lambda t: t.replace("Title: ", "Headline: ", 1)))
    redirected(monkeypatch, tmp_path)
    try:
        file_cards.validate_cards()
    except ValueError as exc:
        assert f"{B01}: first line must be 'Title: ...'" in str(exc)
    else:
        raise AssertionError("missing Title line was accepted")


def test_validate_cards_refuses_a_missing_routing_field(tmp_path, monkeypatch):
    install_card_set(tmp_path, rewrite=(B01, lambda t: t.replace("Pickup: implementer\n", "", 1)))
    redirected(monkeypatch, tmp_path)
    try:
        file_cards.validate_cards()
    except ValueError as exc:
        assert f"{B01}: missing routing field 'Pickup:'" in str(exc)
    else:
        raise AssertionError("missing routing field was accepted")


def test_validate_cards_refuses_a_missing_required_section(tmp_path, monkeypatch):
    install_card_set(tmp_path, rewrite=(B01, lambda t: t.replace("## Summary", "## Overview", 1)))
    redirected(monkeypatch, tmp_path)
    try:
        file_cards.validate_cards()
    except ValueError as exc:
        assert f"{B01}: missing required section '## Summary'" in str(exc)
    else:
        raise AssertionError("missing required section was accepted")


def test_validate_cards_refuses_a_missing_self_check_item(tmp_path, monkeypatch):
    install_card_set(
        tmp_path, rewrite=(B01, lambda t: t.replace("5. Mutant kills:", "5. Mutant receipts:", 1)))
    redirected(monkeypatch, tmp_path)
    try:
        file_cards.validate_cards()
    except ValueError as exc:
        assert f"{B01}: unanswered or missing DESIGN SELF-CHECK item '5. Mutant kills:'" in str(exc)
    else:
        raise AssertionError("missing DESIGN SELF-CHECK item was accepted")


def test_validate_cards_refuses_an_evidence_section(tmp_path, monkeypatch):
    install_card_set(
        tmp_path,
        rewrite=(B01, lambda t: t.replace(
            "## Provenance\n", "## Provenance\n## Evidence\n- leaked receipt\n", 1)))
    redirected(monkeypatch, tmp_path)
    try:
        file_cards.validate_cards()
    except ValueError as exc:
        assert f"{B01}: unexpected '## Evidence' section" in str(exc)
    else:
        raise AssertionError("an in-card Evidence section was accepted")


# --- paginate_items (shared flattener for `gh api --paginate --slurp`) --------


def test_paginate_items_flattens_slurp_pages_and_flat_item_lists():
    # `gh api --paginate --slurp` emits an array of pages; a bare list of
    # objects (one un-slurped page) is also accepted, each object kept whole.
    assert file_cards.paginate_items('[[{"a": 1}, {"b": 2}], [{"c": 3}]]') == [
        {"a": 1}, {"b": 2}, {"c": 3}]
    assert file_cards.paginate_items('[{"a": 1}, {"b": 2}]') == [{"a": 1}, {"b": 2}]
    assert file_cards.paginate_items("") == []


# --- gh wrapper: rc/stdout/stderr and the timeout rule ------------------------


def test_gh_returns_rc_stdout_and_stderr(fake_gh):
    fake_gh(stdout="line one\n", stderr="a warning\n", rc=3)
    rc, out, err = file_cards.gh(["auth", "status", "--hostname", "github.com"])
    assert (rc, out, err) == (3, "line one\n", "a warning\n")


def test_gh_timeout_becomes_rc_124_with_a_steering_message(fake_gh):
    # The fake sleeps past the 1s budget: the wrapper must cut it off and
    # steer instead of waiting. Asserting rc 124 AND the message proves the
    # timeout path (not a normal exit) produced the result.
    fake_gh(sleep_s=5)
    rc, out, err = file_cards.gh(["api", "user"], timeout=1)
    assert rc == 124
    assert out == ""
    assert err == "gh api user timed out after 1s"


# --- idempotency: the module contract "Safe to re-run" ------------------------
# tdd-coverage: idempotency


def test_seed_file_reports_unchanged_when_the_content_already_matches(fake_gh, tmp_path):
    # Re-seeding identical bytes must not produce a write: the contents-API
    # read answers with the same content, and seed_file returns "unchanged"
    # without ever issuing the PUT. The argv log is the took-effect control:
    # it must show the read and never a write, on the first seed AND a re-run.
    content = b"ledger body\n"
    current = json.dumps({"sha": "deadbeef", "content": base64.b64encode(content).decode()})
    log = tmp_path / "argv.log"
    fake_gh(stdout=current, argv_log=log)
    first = file_cards.seed_file("o/r", "github.com", "LEDGER.md", content=content)
    second = file_cards.seed_file("o/r", "github.com", "LEDGER.md", content=content)
    assert first == second == "unchanged"
    log_text = log.read_text()
    assert "repos/o/r/contents/LEDGER.md" in log_text
    assert "-X" not in log_text and "PUT" not in log_text


def test_file_cards_skips_every_already_filed_card_on_a_rerun(fake_gh, tmp_path):
    # The whole card set already filed: a re-run must file nothing and skip
    # all cards — on the first call AND the second (state equality between
    # runs) — and no `gh issue create` may ever fire.
    cards = file_cards.validate_cards()
    titles = sorted({title for _name, title, _body in cards})
    pages = json.dumps([[{"title": t} for t in titles]])
    log = tmp_path / "argv.log"
    fake_gh(stdout=pages, argv_log=log)
    first = file_cards.file_cards("o/r", "github.com", cards)
    second = file_cards.file_cards("o/r", "github.com", cards)
    assert first == second == (0, len(cards))
    assert "issue create" not in log.read_text()


def test_validate_cards_is_stable_across_reruns():
    # Re-running the validator over the same tree must return the identical
    # card list (same order, same titles, same bodies).
    assert file_cards.validate_cards() == file_cards.validate_cards()


# --- hostile input --------------------------------------------------------------
# tdd-coverage: hostile_input


def test_a_hostile_card_title_reaches_gh_verbatim_as_one_argv_element(fake_gh, tmp_path, monkeypatch):
    # A card title carrying shell metacharacters must reach `gh issue create`
    # as ONE argv element, byte-for-byte: the wrapper shells out with a list
    # argv and no shell, so nothing may reinterpret $(...), backticks, ; or &&.
    # The fake's argv log is the took-effect control: it records exactly what
    # the gh process received.
    hostile = "x'; $(rm -rf /); `echo pwned` && ls || true #"
    install_card_set(tmp_path, rewrite=(
        B01, lambda t: "Title: " + hostile + "\n" + t.split("\n", 1)[1]))
    redirected(monkeypatch, tmp_path)
    cards = file_cards.validate_cards()
    others = sorted({title for name, title, _body in cards if name != B01})
    log = tmp_path / "argv.log"
    fake_gh(stdout=json.dumps([[{"title": t} for t in others]]), argv_log=log)
    filed, skipped = file_cards.file_cards("o/r", "github.com", cards)
    assert (filed, skipped) == (1, len(cards) - 1)
    assert hostile in log.read_text()


def test_existing_titles_ignores_nonobject_and_pull_request_items(fake_gh):
    # A hostile or degenerate slurp page — bare strings, numbers, nulls, and a
    # pull_request object that happens to share a title — must not crash the
    # listing or suppress a card as "already filed".
    junk = '[["raw string", 42, null, {"title": "T", "pull_request": {}}, {"title": "T2"}]]'
    fake_gh(stdout=junk)
    assert file_cards.existing_titles("o/r", "github.com") == {"T2"}


# --- is_not_found (the documented 404/Not-Found shape) -----------------------


def test_is_not_found_recognizes_the_documented_not_found_shapes():
    # Docstring: "True when gh reported the 404/Not-Found shape (absent repo,
    # file or path)." Both spellings count; anything else does not.
    assert file_cards.is_not_found("HTTP 404 (Not Found)") is True
    assert file_cards.is_not_found("gh: Not Found") is True
    assert file_cards.is_not_found("404") is True
    assert file_cards.is_not_found("rate limit exceeded") is False
    assert file_cards.is_not_found("") is False


# --- repo_state (reachable+push | absent | refusal) ---------------------------


def test_repo_state_ok_when_push_is_allowed(fake_gh):
    fake_gh(stdout="true\n")
    assert file_cards.repo_state("owner/repo", "github.com") == "ok"


def test_repo_state_refuses_a_login_that_cannot_push(fake_gh):
    fake_gh(stdout="false\n")
    try:
        file_cards.repo_state("owner/repo", "github.com")
    except file_cards.Steer as exc:
        assert exc.line.startswith(
            "REPO-ERROR no-push: owner/repo is reachable but this login cannot push")
    else:
        raise AssertionError("a login without push was reported 'ok'")


def test_repo_state_absent_on_the_not_found_shape(fake_gh):
    fake_gh(stderr="HTTP 404 (Not Found)", rc=1)
    assert file_cards.repo_state("owner/repo", "github.com") == "absent"


def test_repo_state_refuses_an_unreadable_repo(fake_gh):
    fake_gh(stderr="rate limit exceeded", rc=1)
    try:
        file_cards.repo_state("owner/repo", "github.com")
    except file_cards.Steer as exc:
        assert exc.line.startswith("REPO-ERROR repo-access: cannot read owner/repo")
    else:
        raise AssertionError("an unreadable repo did not refuse")


# --- the documented write time-box --------------------------------------------


def test_write_timeout_is_three_times_the_read_limit():
    # "A hung call becomes a steering error instead of a silent wait ...
    # writes get three times the read limit."
    assert file_cards.WRITE_TIMEOUT == file_cards.GH_TIMEOUT * 3


# --- main(): the documented exit codes (module docstring + BOOTSTRAP.md) ------


def test_main_dry_run_exits_0_with_one_machine_readable_line_per_card(capsys, monkeypatch):
    # "python3 file_cards.py --repo <owner>/<repo> [--dry-run]" / "Exit: 0 OK":
    # the offline dry-run prints one "[dry] <name> -> <title>" line per card.
    monkeypatch.setattr(sys, "argv", ["file_cards.py", "--dry-run"])
    assert file_cards.main() == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == len(file_cards.ORDER)
    assert lines[0].startswith(f"[dry] {file_cards.ORDER[0]} -> ")
    assert lines[-1].startswith(f"[dry] {file_cards.ORDER[-1]} -> ")
    for line in lines:
        assert line.startswith("[dry] ") and " -> " in line, line


def test_main_exits_1_with_a_card_error_line_for_an_invalid_card_set(capsys, monkeypatch, tmp_path):
    # "Exit: 1 card files invalid" (BOOTSTRAP.md: report verbatim, never edit
    # cards to hide it): the refusal must name the file and the exact defect.
    install_card_set(tmp_path)
    (tmp_path / B01).unlink()
    redirected(monkeypatch, tmp_path)
    monkeypatch.setattr(sys, "argv", ["file_cards.py", "--dry-run"])
    assert file_cards.main() == 1
    assert capsys.readouterr().err.startswith(f"CARD-ERROR missing card file: {B01}")


def test_main_exits_2_printing_the_steering_line_when_auth_refuses(capsys, monkeypatch, tmp_path):
    # "Exit: 2 auth/transport/refusal (a steering line names the fix)" + the
    # Steer class docstring "main() prints it and exits 2": no `gh` anywhere
    # on PATH, so require_auth raises and main() answers with the fix.
    monkeypatch.setattr(sys, "argv", ["file_cards.py", "--check-auth"])
    monkeypatch.setenv("PATH", str(tmp_path))  # an empty dir: nothing to find
    assert file_cards.main() == 2
    err = capsys.readouterr().err
    assert err.startswith("AUTH-ERROR gh-missing:")
    assert "install GitHub CLI" in err
