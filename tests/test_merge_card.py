"""Focused regression tests for the merge-gate decision logic of `merge_card.py`.

The bootstrap automerge decision "is made by this script, never by a model";
these tests pin exactly that logic, offline and deterministically:
- `VERDICT_RE` — which comment lines count as verdict lines, and the `-<card>` tag;
- `last` — the last-occurrence index used for ordering;
- `require_normal_card` — the lane gate (NORMAL implementation only);
- `check_verdicts` — the verdict order/voiding rules;
- `verdict_events` — paginated comment parsing and the foreign-card-tag filter
  (via the PATH-injected fake `gh`, with the fake's argv log asserted);
- the re-run contracts: `--disable-automerge` on an already-off repo is a
  clean no-op; re-running a completed merge refuses `nothing-to-merge`;
- cross-script consistency: each script names the other's real CLI flags, and
  both emit the same steering-line shape;
- hostile input: junk comments pages are skipped, not crashed on.

No network is touched; no production file is read or written.
"""
import json
import pathlib
import re
import subprocess
import sys

import file_cards
import merge_card

NORMAL_BODY = (
    "Title: [implementer] demo card\n"
    "Pickup: implementer\n"
    "Work class: implementation\n"
    "Execution tier: implementer\n"
    "Verifier: verifier\n"
    "Escalate if: any other test goes red\n"
    "\n"
    "## Failing test\n"
    "- Test file / class: `tests/test_demo.py::TestDemo`\n"
    "- Command: `python3 -m pytest tests/test_demo.py -q`\n"
    "\n"
    "## Mutants\n"
    "- M1: rename the gated symbol; `tests/test_demo.py` must fail.\n"
)

# The TEST-ONLY lane marker the lane gate must refuse (em dash form, as the
# real cards spell it: `none — TEST-ONLY STRENGTHENING`).
TEST_ONLY_BODY = NORMAL_BODY.replace(
    "- Test file / class: `tests/test_demo.py::TestDemo`\n"
    "- Command: `python3 -m pytest tests/test_demo.py -q`\n",
    "none \u2014 TEST-ONLY STRENGTHENING\n",
)


def groups(line):
    m = merge_card.VERDICT_RE.match(line)
    return (m.group(1), m.group(2)) if m else None


# --- VERDICT_RE --------------------------------------------------------------


def test_verdict_re_matches_verdict_lines_with_optional_card_tag():
    assert groups("VERIFIED-12") == ("VERIFIED", "12")
    assert groups("  ACCEPTED") == ("ACCEPTED", None)
    assert groups("RED-CONFIRMED-3") == ("RED-CONFIRMED", "3")
    assert groups("RED-NOT-CONFIRMED") == ("RED-NOT-CONFIRMED", None)
    assert groups("VERIFIED everything green") == ("VERIFIED", None)


def test_verdict_re_rejects_non_verdict_lines():
    assert groups("not a verdict") is None
    assert groups("verified") is None          # case-sensitive by design
    assert groups("VERIFIEDX") is None         # no word boundary inside a word
    assert groups("") is None
    # PROTOCOL.md specifies bare verdict lines (`VERIFIED-N`); a markdown
    # list-item verdict is NOT recognized — pinned here because it is a
    # sharp edge a commenter could hit silently.
    assert groups("- RED-CONFIRMED-3") is None


# --- last --------------------------------------------------------------------


def test_last_returns_the_final_occurrence_of_any_name():
    events = ["RED-CONFIRMED", "VERIFIED", "SENT-BACK", "VERIFIED", "ACCEPTED"]
    assert merge_card.last(events, "VERIFIED") == 3
    assert merge_card.last(events, "SENT-BACK", "ACCEPTED") == 4
    assert merge_card.last(events, "RED-NOT-CONFIRMED", "NOT-VERIFIED") == -1


# --- require_normal_card (the lane gate) --------------------------------------


def test_require_normal_card_accepts_a_normal_implementation_card():
    merge_card.require_normal_card(NORMAL_BODY, 7)  # must not refuse


def test_require_normal_card_accepts_the_bold_work_class_form():
    body = NORMAL_BODY.replace("Work class: implementation", "**Work class:** implementation")
    merge_card.require_normal_card(body, 7)  # must not refuse


def test_require_normal_card_refuses_non_implementation_lanes():
    for work in ("test-only", "small-fix", "design"):
        body = NORMAL_BODY.replace("Work class: implementation", f"Work class: {work}")
        try:
            merge_card.require_normal_card(body, 7)
        except merge_card.Steer as exc:
            assert exc.line.startswith(f"MERGE-REFUSED not-normal-card: issue 7 has Work class {work}")
        else:
            raise AssertionError(f"Work class {work} was admitted to the automerge lane")


def test_require_normal_card_refuses_a_missing_work_class():
    body = NORMAL_BODY.replace("Work class: implementation\n", "")
    try:
        merge_card.require_normal_card(body, 7)
    except merge_card.Steer as exc:
        assert "issue 7 has Work class missing" in str(exc)
    else:
        raise AssertionError("a card with no Work class was admitted")


def test_require_normal_card_refuses_test_only_strengthening():
    try:
        merge_card.require_normal_card(TEST_ONLY_BODY, 7)
    except merge_card.Steer as exc:
        assert "issue 7 declares TEST-ONLY STRENGTHENING, which has no red-first proof" in str(exc)
    else:
        raise AssertionError("TEST-ONLY STRENGTHENING was admitted to the automerge lane")


def test_require_normal_card_refuses_a_card_without_a_failing_test_section():
    body = NORMAL_BODY.replace("## Failing test", "## Failing tests")  # heading drift
    try:
        merge_card.require_normal_card(body, 7)
    except merge_card.Steer as exc:
        assert "issue 7 has no Failing test section" in str(exc)
        assert exc.line.startswith("MERGE-REFUSED malformed-card:")
    else:
        raise AssertionError("a card with no Failing test section was admitted")


# --- check_verdicts (the verdict order gate) ----------------------------------


def test_check_verdicts_accepts_the_complete_ordered_sequence():
    merge_card.check_verdicts(["RED-CONFIRMED", "VERIFIED", "ACCEPTED"], 7)


def test_check_verdicts_accepts_voiders_that_a_later_verdict_resolves():
    # A SENT-BACK / RED-NOT-CONFIRMED that precedes the final RED-CONFIRMED is
    # resolved by it; only voiders AFTER their verdict refuse.
    merge_card.check_verdicts(["SENT-BACK", "RED-NOT-CONFIRMED", "RED-CONFIRMED",
                               "VERIFIED", "ACCEPTED"], 7)


def test_check_verdicts_refuses_missing_verdicts():
    try:
        merge_card.check_verdicts(["RED-CONFIRMED", "VERIFIED"], 7)
    except merge_card.Steer as exc:
        assert "MERGE-REFUSED verdicts-missing: issue 7 has no ACCEPTED verdict line" in str(exc)
    else:
        raise AssertionError("an incomplete verdict set was accepted")


def test_check_verdicts_refuses_out_of_order_verdicts():
    try:
        merge_card.check_verdicts(["VERIFIED", "RED-CONFIRMED", "ACCEPTED"], 7)
    except merge_card.Steer as exc:
        assert exc.line.startswith("MERGE-REFUSED verdict-order: the verdict lines on issue 7 read")
    else:
        raise AssertionError("VERIFIED before RED-CONFIRMED was accepted")


def test_check_verdicts_refuses_anything_after_accepted():
    try:
        merge_card.check_verdicts(["RED-CONFIRMED", "VERIFIED", "ACCEPTED", "VERIFIED"], 7)
    except merge_card.Steer as exc:
        assert exc.line.startswith("MERGE-REFUSED verdict-order:")
    else:
        raise AssertionError("a verdict after ACCEPTED was accepted")


def test_check_verdicts_refuses_unresolved_voiders():
    voiding = [
        ["RED-CONFIRMED", "RED-NOT-CONFIRMED", "VERIFIED", "ACCEPTED"],
        ["RED-CONFIRMED", "SENT-BACK", "VERIFIED", "ACCEPTED"],
        ["RED-CONFIRMED", "VERIFIED", "NOT-VERIFIED", "ACCEPTED"],
        # "trailing SENT-BACK ... refuse" (docs/findings validation ledger):
        # a voider after ACCEPTED breaks "ACCEPTED last, nothing after it".
        ["RED-CONFIRMED", "VERIFIED", "ACCEPTED", "SENT-BACK"],
    ]
    for events in voiding:
        try:
            merge_card.check_verdicts(events, 7)
        except merge_card.Steer as exc:
            assert exc.line.startswith("MERGE-REFUSED verdict-order:")
        else:
            raise AssertionError(f"unresolved voider was accepted: {events}")


def test_check_verdicts_accepts_a_recovered_failed_verification():
    # "a later successful verification after an earlier failed verification"
    # (docs/findings validation ledger): an early NOT-VERIFIED is resolved by
    # the later VERIFIED, provided RED-CONFIRMED precedes both and ACCEPTED
    # still ends the sequence.
    merge_card.check_verdicts(["RED-CONFIRMED", "NOT-VERIFIED", "VERIFIED", "ACCEPTED"], 7)


# --- verdict_events (paginated comment reading, offline via fake gh) ----------


def test_verdict_events_reads_slurped_pages_and_filters_foreign_card_tags(fake_gh, tmp_path):
    # The shape `gh api --paginate --slurp` really produces: an array of pages,
    # each page an array of comment objects.
    pages = (
        '[[{"body": "RED-CONFIRMED-7\\nprose that is not a verdict\\nVERIFIED-9"},'
        ' {"body": "accepted? no\\nVERIFIED-7"}],'
        ' [{"body": "ACCEPTED-7"}]]'
    )
    log = tmp_path / "argv.log"
    fake_gh(stdout=pages, argv_log=log)
    events = merge_card.verdict_events("owner/repo", "github.com", 7)
    assert events == ["RED-CONFIRMED", "VERIFIED", "ACCEPTED"]
    # Prove the fake gh (not a real one) served the call, at the right endpoint:
    assert "repos/owner/repo/issues/7/comments" in log.read_text()


def test_verdict_events_refuses_when_comments_cannot_be_read(fake_gh):
    fake_gh(stderr="Not Found", rc=1)
    try:
        merge_card.verdict_events("owner/repo", "github.com", 7)
    except merge_card.Steer as exc:
        assert "MERGE-REFUSED read-failed: cannot read the comments of issue 7" in str(exc)
    else:
        raise AssertionError("an unreadable comment list was accepted")


# --- refuse ------------------------------------------------------------------


def test_refuse_builds_a_merge_refused_steer():
    exc = merge_card.refuse("not-fast-forward", "card/7 is behind", "forward-merge and re-run")
    assert isinstance(exc, file_cards.Steer)
    assert exc.line == ("MERGE-REFUSED not-fast-forward: card/7 is behind "
                        "\u2014 forward-merge and re-run")


# --- idempotency: the re-run contracts ------------------------------------------
# tdd-coverage: idempotency


def test_disable_automerge_when_already_off_is_a_clean_noop(fake_gh, tmp_path, capsys):
    # The sunset is safe to re-run: disabling an automerge that is already off
    # prints "already off" and returns 0 — never an error, never a DELETE.
    # Rule-scripted fake `gh` (conftest): first match wins, so the specific
    # contents path must be listed before the bare repo path.
    log = tmp_path / "argv.log"
    fake_gh(argv_log=log, rules=[
        ("auth status", {"rc": 0}),
        ("user", {"stdout": "bootstrapper\n"}),
        ("repos/o/r/contents/.cards/AUTOMERGE", {"rc": 1, "stderr": "404 Not Found"}),
        ("repos/o/r", {"stdout": '{"default_branch": "main"}'}),
    ])
    assert merge_card.disable("o/r", "github.com") == 0
    out = capsys.readouterr().out
    assert "AUTOMERGE already off" in out
    assert "absent on main" in out
    # Took-effect control: the last gh call was the contents read, not a DELETE.
    assert "repos/o/r/contents/.cards/AUTOMERGE" in log.read_text()


def test_a_rerun_of_a_completed_merge_refuses_nothing_to_merge(fake_gh, tmp_path):
    # After the fast-forward the card branch and the integration branch are
    # identical; re-running the merge must refuse "nothing-to-merge" with a
    # steering line instead of merging anything a second time.
    log = tmp_path / "argv.log"
    fake_gh(argv_log=log, rules=[
        ("auth status", {"rc": 0}),
        ("user", {"stdout": "bootstrapper\n"}),
        ("repos/o/r/contents/.cards/AUTOMERGE", {"stdout": '{"sha": "opt-in"}'}),
        ("repos/o/r/issues/7", {"stdout": json.dumps({"body": NORMAL_BODY})}),
        ("git/ref/heads/card/7", {"stdout": '{"object": {"sha": "deadbeefdeadbeef"}}'}),
        ("compare/", {"stdout": '{"status": "identical"}'}),
        ("repos/o/r", {"stdout": '{"default_branch": "main"}'}),
    ])
    try:
        merge_card.merge("o/r", "github.com", 7, "card/7", dry_run=False)
    except merge_card.Steer as exc:
        assert exc.line.startswith(
            "MERGE-REFUSED nothing-to-merge: card/7 has no commits beyond main")
    else:
        raise AssertionError("an identical branch pair was merged")
    # Took-effect control: the refusal came from the real comparison call.
    assert "compare/main...card/7" in log.read_text()


# --- cross-script consistency: the two scripts must agree ------------------------
# tdd-coverage: cross_script_consistency


def test_each_script_names_the_others_real_flags():
    # file_cards seeds AUTOMERGE_TEXT telling the operator to sunset via
    # `merge_card.py --disable-automerge`; merge_card's opt-in refusal tells
    # the operator to run `file_cards.py --bootstrap --repo ... --automerge`.
    # Both cross-references must resolve against the OTHER script's real CLI:
    # a renamed flag on either side must fail here, not at bootstrap time.
    root = pathlib.Path(file_cards.__file__).parent
    assert "--disable-automerge" in file_cards.AUTOMERGE_TEXT
    merge_help = subprocess.run(
        [sys.executable, str(root / "merge_card.py"), "--help"],
        capture_output=True, text=True, check=False)
    assert merge_help.returncode == 0, merge_help.stderr
    assert "--disable-automerge" in merge_help.stdout
    cards_help = subprocess.run(
        [sys.executable, str(root / "file_cards.py"), "--help"],
        capture_output=True, text=True, check=False)
    assert cards_help.returncode == 0, cards_help.stderr
    assert "--automerge" in cards_help.stdout


def test_both_scripts_share_the_steering_line_shape():
    # Both scripts promise steering-grade refusals `<PREFIX> <rule>: <measured>
    # — <fix>` (one em dash, fix always present): the two constructors must
    # keep emitting the identical shape.
    shape = re.compile(r"^[A-Z][A-Z-]+ [a-z][a-z0-9-]*: .+ \u2014 .+$")
    assert shape.match(file_cards.Steer(
        "AUTH-ERROR", "not-logged-in", "gh auth status failed", "run the login step").line)
    assert shape.match(merge_card.refuse(
        "not-fast-forward", "card/7 is behind", "forward-merge and re-run").line)


def test_merge_refuses_without_the_optin_and_names_the_real_optin_flag(fake_gh, tmp_path):
    # The gate: no .cards/AUTOMERGE on the integration branch -> refuse, and
    # the refusal's fix must name an opt-in command file_cards.py really accepts
    # (verified against its --help in test_each_script_names_the_others_real_flags).
    fake_gh(rules=[
        ("auth status", {"rc": 0}),
        ("user", {"stdout": "bootstrapper\n"}),
        ("repos/o/r/contents/.cards/AUTOMERGE", {"rc": 1, "stderr": "404 Not Found"}),
        ("repos/o/r", {"stdout": '{"default_branch": "main"}'}),
    ])
    try:
        merge_card.merge("o/r", "github.com", 7, "card/7", dry_run=True)
    except merge_card.Steer as exc:
        assert exc.line.startswith(
            "MERGE-REFUSED automerge-off: .cards/AUTOMERGE is absent on main")
        assert "file_cards.py --bootstrap --repo o/r --automerge" in exc.line
    else:
        raise AssertionError("a repo without the opt-in file was merged")


# --- hostile input ----------------------------------------------------------------
# tdd-coverage: hostile_input


def test_verdict_events_skips_nonobject_comments_instead_of_crashing(fake_gh):
    # A hostile or degenerate comments page — bare strings, numbers and nulls
    # as items — must be skipped exactly like the sister reader
    # `file_cards.existing_titles` skips them, not crash the gate with a
    # traceback (the script promises a steering-grade refusal on every failure).
    pages = '[[{"body": "RED-CONFIRMED-7"}, "ACCEPTED-7", 42, null, {"body": "VERIFIED-7"}]]'
    fake_gh(stdout=pages)
    assert merge_card.verdict_events("owner/repo", "github.com", 7) == [
        "RED-CONFIRMED", "VERIFIED"]


# --- the real card set through the lane gate (docs/findings claims) -----------


def test_require_normal_card_accepts_all_real_card_bodies():
    # docs/findings/local-first-reassessment-2026-10-25.md ("Automerge
    # behavior"): "all 19 filed card bodies pass as NORMAL implementation
    # cards" — pinned against the REAL card set, not a synthetic body, so a
    # card drifting out of the automerge lane fails here first.
    for number, (_name, _title, body) in enumerate(file_cards.validate_cards(), 1):
        merge_card.require_normal_card(body, number)  # must not refuse


def test_require_normal_card_accepts_a_work_class_with_a_trailing_description():
    # "NORMAL variants pass, including `Work class: implementation —
    # description`" (docs/findings): the lane reads the class word, not the
    # rest of the line.
    body = NORMAL_BODY.replace(
        "Work class: implementation",
        "Work class: implementation \u2014 the seven local contracts")
    merge_card.require_normal_card(body, 7)  # must not refuse


def test_require_normal_card_refuses_the_hyphen_test_only_form():
    # "TEST-ONLY declarations with both em-dash and hyphen forms refuse"
    # (docs/findings): the em-dash form is covered above; this pins the
    # hyphen separator so one spelling cannot silently slip the gate.
    body = TEST_ONLY_BODY.replace("none \u2014 TEST-ONLY STRENGTHENING",
                                  "none - TEST-ONLY STRENGTHENING")
    try:
        merge_card.require_normal_card(body, 7)
    except merge_card.Steer as exc:
        assert "issue 7 declares TEST-ONLY STRENGTHENING, which has no red-first proof" in str(exc)
    else:
        raise AssertionError("the hyphen TEST-ONLY form was admitted to the automerge lane")
