#!/usr/bin/env python3
"""Bootstrap automerge: fast-forward the integration branch to a NORMAL implementation card's branch
when, and only when, the card's red-first receipts and verdicts are complete. The decision is made
by this script, never by a model. TEST-ONLY and small-fix lanes do not have those red-first
receipts and therefore cannot use this gate.

Bootstrap mode only. The target repository opts in by carrying `.cards/AUTOMERGE` on its integration
branch (`file_cards.py --bootstrap` seeds it; `--disable-automerge` removes it, which is the sunset: once
the ladder has landed, the operator holds the push again). Without that file this tool refuses.

What it checks (every line is a refusal with its fix, exit 2):
  1. the switch: `.cards/AUTOMERGE` exists on the integration branch;
  2. the lane: the issue is a NORMAL implementation card, never TEST-ONLY STRENGTHENING or small-fix;
  3. the branch fast-forwards: ahead of the integration branch, not behind, not diverged (a moved tip is
     an ordinary forward-merge of the integration tip into the card branch and a fresh verification,
     per PROTOCOL.md phase M);
  4. the evidence: `.cards/evidence/<card>/` on the card branch holds the receipts (red.txt, red-confirm.txt,
     fix.md, verify.md; or the step directories vr/ and vf/);
  5. the verdicts, read from the issue's comments in order: RED-CONFIRMED, VERIFIED and ACCEPTED all present,
     in that order, ACCEPTED last, nothing after it (a later SENT-BACK, NOT-VERIFIED or RED-NOT-CONFIRMED
     voids it).
Then it moves the integration branch with a non-forced ref update (GitHub refuses anything that is not a
fast-forward), and posts a MERGED comment on the issue as the audit trail.

Usage:
    python3 merge_card.py --repo <owner>/<repo> --card <N> [--branch card/<N>] [--dry-run]
    python3 merge_card.py --repo <owner>/<repo> --disable-automerge
Exit: 0 merged (or MERGE-READY with --dry-run) | 2 refused (a steering line names the fix).
"""
import argparse
import json
import re
import sys
import urllib.parse

from file_cards import (
    AUTOMERGE_PATH,
    WRITE_TIMEOUT,
    Steer,
    first_line,
    gh,
    paginate_items,
    require_auth,
)

VERDICT_RE = re.compile(
    r"^\s*(RED-NOT-CONFIRMED|RED-CONFIRMED|NOT-VERIFIED|VERIFIED|SENT-BACK|ACCEPTED)(?:-(\d+))?\b")
SEED_RECEIPTS = ("red.txt", "red-confirm.txt", "fix.md", "verify.md")


def refuse(rule: str, measured: str, fix: str) -> Steer:
    return Steer("MERGE-REFUSED", rule, measured, fix)


def api(hostname: str, path: str, *extra: str, timeout: int = 60):
    return gh(["api", "--hostname", hostname, path, *extra], timeout=timeout)


def read_json(hostname: str, path: str, what: str):
    rc, out, err = api(hostname, path)
    if rc != 0:
        raise refuse("read-failed", f"cannot read {what} ({first_line(err, out)})", "re-run; check the card number and branch name")
    return json.loads(out or "null")


def verdict_events(repo: str, hostname: str, card: int) -> list[str]:
    rc, out, err = gh(["api", "--hostname", hostname, "--paginate", "--slurp",
                       f"repos/{repo}/issues/{card}/comments?per_page=100"], timeout=120)
    if rc != 0:
        raise refuse("read-failed", f"cannot read the comments of issue {card} ({first_line(err, out)})", "re-run")
    events: list[str] = []
    for comment in paginate_items(out):
        if not isinstance(comment, dict):
            continue
        for line in str(comment.get("body", "")).splitlines():
            m = VERDICT_RE.match(line)
            if m and (m.group(2) is None or int(m.group(2)) == card):
                events.append(m.group(1))
    return events


def last(events: list[str], *names: str) -> int:
    return max((i for i, e in enumerate(events) if e in names), default=-1)


def require_normal_card(body: str, card: int) -> None:
    """Refuse lanes that do not have the normal red-first proof, even with forged receipts."""
    work = re.search(r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?Work class:(?:\*\*)?\s*([A-Za-z-]+)", body)
    if not work or work.group(1) != "implementation":
        actual = work.group(1) if work else "missing"
        raise refuse("not-normal-card", f"issue {card} has Work class {actual}; bootstrap automerge requires implementation",
                     "use a NORMAL implementation card, or land this lane through the operator/mechanical local gate")
    failing = re.search(r"(?ims)^\s*(?:#+\s*)?Failing test:?\s*\n(.*?)(?=^\s*(?:#+\s*)?Mutants|\Z)", body)
    if not failing:
        raise refuse("malformed-card", f"issue {card} has no Failing test section",
                     "card-check must repair the card before any landing decision")
    if re.search(r"(?im)^\s*(?:[-*]\s*)?none\s+[—-]\s+TEST-ONLY STRENGTHENING\s*$", failing.group(1)):
        raise refuse("not-normal-card", f"issue {card} declares TEST-ONLY STRENGTHENING, which has no red-first proof",
                     "land it through the operator/mechanical local gate; bootstrap automerge accepts NORMAL implementation only")


def check_verdicts(events: list[str], card: int) -> None:
    need = {"RED-CONFIRMED": last(events, "RED-CONFIRMED"), "VERIFIED": last(events, "VERIFIED"),
            "ACCEPTED": last(events, "ACCEPTED")}
    missing = [k for k, v in need.items() if v < 0]
    if missing:
        raise refuse("verdicts-missing", f"issue {card} has no {', '.join(missing)} verdict line",
                     f"run the missing phases (PROTOCOL.md) and post each verdict as a comment line, e.g. `VERIFIED-{card}`")
    voiders = {"RED-NOT-CONFIRMED": last(events, "RED-NOT-CONFIRMED"), "NOT-VERIFIED": last(events, "NOT-VERIFIED"),
               "SENT-BACK": last(events, "SENT-BACK")}
    order_ok = (need["RED-CONFIRMED"] < need["VERIFIED"] < need["ACCEPTED"] == len(events) - 1
                and voiders["RED-NOT-CONFIRMED"] < need["RED-CONFIRMED"]
                and voiders["SENT-BACK"] < need["RED-CONFIRMED"]
                and voiders["NOT-VERIFIED"] < need["VERIFIED"])
    if not order_ok:
        raise refuse("verdict-order", f"the verdict lines on issue {card} read {' > '.join(events)}",
                     "the card must end RED-CONFIRMED, VERIFIED, ACCEPTED in that order, with nothing after ACCEPTED "
                     "and no unresolved SENT-BACK, NOT-VERIFIED or RED-NOT-CONFIRMED; finish the open phase and re-run")


def disable(repo: str, hostname: str) -> int:
    require_auth(hostname)
    base = read_json(hostname, f"repos/{repo}", repo)["default_branch"]
    rc, out, err = api(hostname, f"repos/{repo}/contents/{AUTOMERGE_PATH}?ref={base}")
    if rc != 0:
        print(f"AUTOMERGE already off for {repo} ({AUTOMERGE_PATH} absent on {base})")
        return 0
    sha = json.loads(out)["sha"]
    rc, out, err = api(hostname, f"repos/{repo}/contents/{AUTOMERGE_PATH}", "-X", "DELETE",
                       "-f", "message=chore: end bootstrap automerge; the operator holds the push again",
                       "-f", f"sha={sha}", "-f", f"branch={base}", timeout=WRITE_TIMEOUT)
    if rc != 0:
        raise refuse("disable-failed", f"cannot remove {AUTOMERGE_PATH} ({first_line(err, out)})", "re-run, or delete the file by hand")
    print(f"AUTOMERGE OFF repo={repo} base={base}")
    return 0


def merge(repo: str, hostname: str, card: int, branch: str, dry_run: bool) -> int:
    require_auth(hostname)
    base = read_json(hostname, f"repos/{repo}", repo)["default_branch"]

    rc, out, err = api(hostname, f"repos/{repo}/contents/{AUTOMERGE_PATH}?ref={urllib.parse.quote(base)}")
    if rc != 0:
        raise refuse("automerge-off", f"{AUTOMERGE_PATH} is absent on {base}, so this repository has not opted in",
                     f"the operator merges card {card} by hand; to opt in, run `file_cards.py --bootstrap --repo {repo} --automerge`")

    issue = read_json(hostname, f"repos/{repo}/issues/{card}", f"issue {card}")
    require_normal_card(str(issue.get("body") or ""), card)

    head = read_json(hostname, f"repos/{repo}/git/ref/heads/{branch}", f"branch {branch}")["object"]["sha"]
    cmp_ = read_json(hostname, f"repos/{repo}/compare/{urllib.parse.quote(base)}...{urllib.parse.quote(branch, safe='/')}", "the comparison")
    if cmp_.get("status") == "identical":
        raise refuse("nothing-to-merge", f"{branch} has no commits beyond {base}",
                     "the implementer commits the card's work to the branch first; nothing has been built yet")
    if cmp_.get("status") != "ahead" or cmp_.get("behind_by", 0) != 0:
        raise refuse("not-fast-forward",
                     f"{branch} is {cmp_.get('status')} of {base} (ahead_by={cmp_.get('ahead_by')}, behind_by={cmp_.get('behind_by')})",
                     "the tip moved underneath the card: forward-merge the integration tip into the card branch with an ordinary merge commit and re-run phase V on the merged tree, then re-run this")

    rc, out, err = api(hostname, f"repos/{repo}/contents/.cards/evidence/{card}?ref={urllib.parse.quote(branch, safe='/')}")
    names = {item["name"] for item in json.loads(out)} if rc == 0 else set()
    if not ({"vr", "vf"} <= names or all(n in names for n in SEED_RECEIPTS)):
        missing = [n for n in SEED_RECEIPTS if n not in names]
        raise refuse("evidence-missing", f".cards/evidence/{card}/ on {branch} lacks {', '.join(missing) or 'the receipts'}",
                     "each phase commits its receipt under .cards/evidence/<card>/ (PROTOCOL.md); finish the phase that is missing")

    check_verdicts(verdict_events(repo, hostname, card), card)

    if dry_run:
        print(f"MERGE-READY repo={repo} card={card} branch={branch} base={base} sha={head}")
        return 0
    rc, out, err = api(hostname, f"repos/{repo}/git/refs/heads/{base}", "-X", "PATCH",
                       "-f", f"sha={head}", "-F", "force=false", timeout=WRITE_TIMEOUT)
    if rc != 0:
        raise refuse("update-refused", f"GitHub refused the fast-forward of {base} to {head[:12]} ({first_line(err, out)})",
                     "the branch is not a clean fast-forward any more; forward-merge, re-verify and re-run")
    note = (f"MERGED-{card}: fast-forwarded `{base}` to `{head}` from `{branch}` by merge_card.py "
            f"(bootstrap automerge; receipts and verdicts checked; the push gate returns to the operator when "
            f"`{AUTOMERGE_PATH}` is removed).")
    gh(["issue", "comment", str(card), "-R", repo, "--body-file", "-"], input_text=note, timeout=WRITE_TIMEOUT)
    print(f"MERGED repo={repo} card={card} base={base} sha={head}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", required=True, help="target owner/repo")
    ap.add_argument("--card", type=int, help="card (issue) number")
    ap.add_argument("--branch", help="card branch (default card/<N>)")
    ap.add_argument("--dry-run", action="store_true", help="run every check, move nothing")
    ap.add_argument("--disable-automerge", action="store_true", help=f"remove {AUTOMERGE_PATH}: the operator holds the push again")
    ap.add_argument("--hostname", default="github.com")
    args = ap.parse_args()
    try:
        if args.disable_automerge:
            return disable(args.repo, args.hostname)
        if not args.card:
            ap.error("--card <N> is required")
        return merge(args.repo, args.hostname, args.card, args.branch or f"card/{args.card}", args.dry_run)
    except Steer as exc:
        print(exc.line, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
