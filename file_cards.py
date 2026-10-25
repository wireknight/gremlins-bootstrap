#!/usr/bin/env python3
"""Bootstrap a repository from the card set, unattended: authenticate-check, create the
private repository if absent, seed LEDGER.md and PROTOCOL.md, file the 19 cards as issues.

Designed to be run BY the pi coding-agent harness (`pi` + `pi-subagents`) paired with the
GitHub CLI (`gh`): every step is idempotent, every `gh` call is time-boxed, every refusal is
a steering-grade line (`<PREFIX> <rule>: <what was measured> -- <how to fix it>`), and the
last stdout line of a successful run is machine-readable.

Usage:
    python3 file_cards.py --bootstrap --repo <owner>/<repo>      # the one command an agent runs
    python3 file_cards.py --bootstrap --repo <owner>/<repo> --no-automerge   # new repo: the operator merges every card
    python3 file_cards.py --check-auth [--repo <owner>/<repo>]   # read-only
    python3 file_cards.py --login                                # the one HUMAN step (browser/device approval)
    python3 file_cards.py --repo <owner>/<repo> [--dry-run]      # file the cards only

Exit: 0 OK | 1 card files invalid | 2 auth/transport/refusal (a steering line names the fix).
Safe to re-run: existing repository, seeded files and filed cards are detected and skipped.
"""
import argparse
import base64
import json
import os
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
HERE = ROOT / "cards"
SEED_FILES = ("LEDGER.md", "PROTOCOL.md", "LICENSE")
AUTOMERGE_PATH = ".cards/AUTOMERGE"
AUTOMERGE_TEXT = (
    "bootstrap\n"
    "# Bootstrap automerge is ON for this repository: merge_card.py may fast-forward the integration branch\n"
    "# when a NORMAL implementation card's receipts and verdicts are complete. Remove this file\n"
    "# (merge_card.py --disable-automerge)\n"
    "# when the ladder has landed: the operator holds the push again.\n"
)
REQUIRED_SCOPES = ("repo", "workflow")
# A hung call becomes a steering error instead of a silent wait. Override with CARDS_GH_TIMEOUT (seconds);
# writes get three times the read limit. Duplicates are prevented by re-listing, never by the clock.
GH_TIMEOUT = int(os.environ.get("CARDS_GH_TIMEOUT", "60"))
WRITE_TIMEOUT = GH_TIMEOUT * 3

# Ledger order: the full 19-card ladder, all drafted.
ORDER = [
    "B0.1-steps.md",
    "B0.2-handoff.md",
    "B0.3-recovery.md",
    "B0.4-profiles.md",
    "B1.0-anchors.md",
    "B1.1-digest.md",
    "B1.2-inject.md",
    "B1.3-write-gate.md",
    "B1.4-hooks.md",
    "B2.1-roles.md",
    "B2.2-kickoff.md",
    "B2.3-router.md",
    "B3.1-qa.md",
    "B3.2-investigate.md",
    "B3.3-synchronize.md",
    "B4.1-build.md",
    "B4.2-local-compute.md",
    "B5.1-battery.md",
    "B5.2-docs-gates.md",
]

REQUIRED_SECTIONS = (
    "## Summary",
    "## Context",
    "## Failing test",
    "## Mutants",
    "## Order for every card (no one-run path)",
    "## Scope",
    "## Dependencies",
    "## Validation (done when)",
    "## Doctrine",
    "## DESIGN SELF-CHECK",
    "## Provenance",
)

SELF_CHECK_ITEMS = (
    "1. Claims and pins:",
    "2. Constants:",
    "3. Shared state and test order:",
    "4. Inherited environment:",
    "5. Mutant kills:",
    "6. Composition:",
)


class Steer(Exception):
    """A refusal that carries its own fix; main() prints it and exits 2."""

    def __init__(self, prefix: str, rule: str, measured: str, fix: str):
        super().__init__(f"{prefix} {rule}: {measured}")
        self.line = f"{prefix} {rule}: {measured} \u2014 {fix}"


def gh(args: list[str], input_text: str | None = None, timeout: int = GH_TIMEOUT):
    """Run `gh <args>`; returns (returncode, stdout, stderr). A timeout is rc 124."""
    try:
        r = subprocess.run(
            ["gh", *args], input=input_text, text=True, capture_output=True,
            stdin=subprocess.DEVNULL if input_text is None else None, timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        return 124, "", f"gh {' '.join(args[:3])} timed out after {timeout}s"
    return r.returncode, r.stdout or "", r.stderr or ""


def first_line(*texts: str) -> str:
    for t in texts:
        if t and t.strip():
            return t.strip().splitlines()[0]
    return "no output"


def is_not_found(err: str) -> bool:
    """True when gh reported the 404/Not-Found shape (absent repo, file or path)."""
    return "404" in err or "Not Found" in err


def paginate_items(out: str) -> list:
    """Flatten `gh api --paginate --slurp` output into one list of items."""
    items: list = []
    for page in json.loads(out or "[]"):
        items.extend(page if isinstance(page, list) else [page])
    return items


def require_auth(hostname: str) -> str:
    """Return the authenticated login, or raise Steer naming the one human step."""
    if not shutil.which("gh"):
        raise Steer("AUTH-ERROR", "gh-missing", "the gh CLI is not installed or not on PATH",
                    "install GitHub CLI (`brew install gh` or https://cli.github.com), then re-run")
    rc, out, err = gh(["auth", "status", "--hostname", hostname])
    if rc != 0:
        raise Steer(
            "AUTH-ERROR", "not-logged-in",
            f"gh auth status for {hostname} failed ({first_line(err, out)})",
            f"HUMAN STEP, an agent cannot approve a browser or device code: run "
            f"`python3 file_cards.py --login --hostname {hostname}` (or `gh auth login --hostname {hostname} "
            f"--scopes {','.join(REQUIRED_SCOPES)}`, or export GH_TOKEN with those scopes), then re-run this command",
        )
    rc, out, err = gh(["api", "--hostname", hostname, "user", "--jq", ".login"])
    login = out.strip()
    if rc != 0 or not login:
        raise Steer("AUTH-ERROR", "api-user", f"gh api user failed ({first_line(err, out)})",
                    f"re-authenticate with `python3 file_cards.py --login --hostname {hostname}`")
    return login


def repo_state(repo: str, hostname: str):
    """-> 'ok' (reachable, push allowed) | 'absent' | raises Steer."""
    rc, out, err = gh(["api", "--hostname", hostname, f"repos/{repo}", "--jq", ".permissions.push"])
    if rc == 0:
        if out.strip() != "true":
            raise Steer("REPO-ERROR", "no-push", f"{repo} is reachable but this login cannot push",
                        "use a repository you own, or ask for write access")
        return "ok"
    if is_not_found(err):
        return "absent"
    raise Steer("REPO-ERROR", "repo-access", f"cannot read {repo} ({first_line(err, out)})",
                "check the owner/name spelling and that the login can see it")


def create_repo(repo: str, hostname: str) -> None:
    rc, out, err = gh(["repo", "create", repo, "--private", "--description",
                       "Bootstrapped from the card set: a self-verifying agent workflow runtime built from work orders"],
                      timeout=WRITE_TIMEOUT)
    if rc != 0:
        raise Steer("REPO-ERROR", "create-failed", f"gh repo create {repo} failed ({first_line(err, out)})",
                    "create it by hand (`gh repo create <owner>/<repo> --private`) or pick another name, then re-run")
    print(f"[repo] created private repository {repo}")


def seed_file(repo: str, hostname: str, name: str, content: bytes | None = None) -> str:
    """Put one seed file into the repository through the contents API. -> created|updated|unchanged."""
    if content is None:
        content = (ROOT / name).read_bytes()
    rc, out, err = gh(["api", "--hostname", hostname, f"repos/{repo}/contents/{name}"])
    sha = None
    if rc == 0:
        try:
            current = json.loads(out)
            sha = current.get("sha")
            if base64.b64decode(current.get("content", "")) == content:
                return "unchanged"
        except (ValueError, TypeError):
            pass
    elif not is_not_found(err):
        raise Steer("SEED-ERROR", "read-failed", f"cannot read {name} in {repo} ({first_line(err, out)})",
                    "re-run; if it persists, check the login's repository permissions")
    fields = ["-f", f"message=chore: seed {name} from the card set",
              "-f", f"content={base64.b64encode(content).decode()}"]
    if sha:
        fields += ["-f", f"sha={sha}"]
    rc, out, err = gh(["api", "--hostname", hostname, "-X", "PUT", f"repos/{repo}/contents/{name}", *fields],
                      timeout=WRITE_TIMEOUT)
    if rc != 0:
        raise Steer("SEED-ERROR", "write-failed", f"cannot write {name} to {repo} ({first_line(err, out)})",
                    "re-run (the seed step is idempotent); check the login can push to the default branch")
    return "updated" if sha else "created"


def validate_cards() -> list[tuple[str, str, str]]:
    """Validate the card files and return [(filename, title, body), ...]."""
    out: list[tuple[str, str, str]] = []
    for name in ORDER:
        path = HERE / name
        if not path.exists():
            raise ValueError(f"missing card file: {name}")
        text = path.read_text(encoding="utf-8")
        first, body = text.split("\n", 1)
        if not first.startswith("Title: "):
            raise ValueError(f"{name}: first line must be 'Title: ...'")
        for field in ("Pickup:", "Work class:", "Execution tier:", "Verifier:", "Escalate if:"):
            if field not in body:
                raise ValueError(f"{name}: missing routing field '{field}'")
        for section in REQUIRED_SECTIONS:
            if section not in body:
                raise ValueError(f"{name}: missing required section '{section}'")
        for item in SELF_CHECK_ITEMS:
            if item not in body:
                raise ValueError(f"{name}: unanswered or missing DESIGN SELF-CHECK item '{item}'")
        if "## Evidence" in body:
            raise ValueError(f"{name}: unexpected '## Evidence' section (evidence lives under .cards/evidence/)")
        out.append((name, first.removeprefix("Title: ").strip(), body))
    return out


def existing_titles(repo: str, hostname: str) -> set[str]:
    rc, out, err = gh(["api", "--hostname", hostname, "--paginate", "--slurp",
                       f"repos/{repo}/issues?state=all&per_page=100"], timeout=120)
    if rc != 0:
        raise Steer("FILE-ERROR", "list-failed", f"cannot list issues in {repo} ({first_line(err, out)})",
                    "re-run; filing is skipped until the existing issues can be read, so no duplicates are created")
    titles: set[str] = set()
    for item in paginate_items(out):
        if isinstance(item, dict) and "pull_request" not in item and isinstance(item.get("title"), str):
            titles.add(item["title"])
    return titles


def file_cards(repo: str, hostname: str, cards) -> tuple[int, int]:
    """File every card whose title is not already an issue. -> (filed, skipped)."""
    have = existing_titles(repo, hostname)
    filed = skipped = 0
    for name, title, body in cards:
        if title in have:
            print(f"[skip] {name} -> already filed")
            skipped += 1
            continue
        rc, out, err = gh(["issue", "create", "-R", repo, "--title", title, "--body-file", "-"],
                          input_text=body.lstrip("\n"), timeout=WRITE_TIMEOUT)
        if rc != 0:
            # A timeout may still have created the issue: re-list before declaring failure.
            if title in existing_titles(repo, hostname):
                print(f"[skip] {name} -> filed despite {first_line(err, out)}")
                skipped += 1
                have.add(title)
                continue
            raise Steer("FILE-ERROR", "create-failed", f"gh issue create failed for {name} ({first_line(err, out)})",
                        "re-run: already-filed cards are skipped, so it resumes where it stopped")
        print(f"[file] {name} -> {out.strip()}")
        have.add(title)
        filed += 1
    return filed, skipped


def run_login(hostname: str) -> int:
    if not shutil.which("gh"):
        raise Steer("AUTH-ERROR", "gh-missing", "the gh CLI is not installed or not on PATH",
                    "install GitHub CLI (`brew install gh` or https://cli.github.com) first")
    cmd = ["gh", "auth", "login", "--hostname", hostname, "--git-protocol", "https",
           "--scopes", ",".join(REQUIRED_SCOPES)]
    print(f"Running: {' '.join(cmd)}")
    if subprocess.run(cmd, check=False).returncode != 0:
        raise Steer("AUTH-ERROR", "login-failed", "`gh auth login` did not complete",
                    f"re-run `{' '.join(cmd)}` or export GH_TOKEN with the {','.join(REQUIRED_SCOPES)} scopes")
    login = require_auth(hostname)
    print(f"GH AUTH OK user={login} host={hostname}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", help="target owner/repo")
    ap.add_argument("--bootstrap", action="store_true",
                    help="auth check, create the private repo if absent, seed LEDGER/PROTOCOL/LICENSE, file the cards")
    ap.add_argument("--no-automerge", action="store_true",
                    help="with --bootstrap: do NOT opt a new repository into bootstrap automerge (the operator merges every card)")
    ap.add_argument("--automerge", action="store_true",
                    help="with --bootstrap: opt an EXISTING repository into bootstrap automerge (a new one is opted in by default)")
    ap.add_argument("--dry-run", action="store_true", help="validate the card files and print titles; no network")
    ap.add_argument("--check-auth", action="store_true", help="read-only: gh installed, logged in, repo reachable")
    ap.add_argument("--login", action="store_true", help="the one human step: interactive `gh auth login` with the required scopes")
    ap.add_argument("--hostname", default="github.com", help="GitHub hostname (default: github.com)")
    args = ap.parse_args()

    try:
        if args.login:
            return run_login(args.hostname)

        if args.check_auth:
            login = require_auth(args.hostname)
            if args.repo:
                state = repo_state(args.repo, args.hostname)
                if state == "absent":
                    raise Steer("REPO-ERROR", "absent", f"{args.repo} does not exist",
                                f"run `python3 file_cards.py --bootstrap --repo {args.repo}` to create and seed it")
                print(f"GH AUTH OK user={login} host={args.hostname} repo={args.repo} (push=true)")
            else:
                print(f"GH AUTH OK user={login} host={args.hostname}")
            return 0

        if not (args.repo or args.dry_run):
            ap.error("--repo <owner>/<repo> is required (or use --dry-run, --check-auth, --login)")

        try:
            cards = validate_cards()
        except ValueError as exc:
            print(f"CARD-ERROR {exc}", file=sys.stderr)
            return 1

        if args.dry_run:
            for name, title, _body in cards:
                print(f"[dry] {name} -> {title}")
            return 0

        login = require_auth(args.hostname)
        state = repo_state(args.repo, args.hostname)
        created = state == "absent"
        if created:
            if not args.bootstrap:
                raise Steer("REPO-ERROR", "absent", f"{args.repo} does not exist",
                            "re-run with --bootstrap to create it (private), or create it first")
            create_repo(args.repo, args.hostname)

        seeded = 0
        if args.bootstrap:
            for name in SEED_FILES:
                result = seed_file(args.repo, args.hostname, name)
                print(f"[seed] {name}: {result}")
                seeded += result != "unchanged"
            enable = args.automerge or (created and not args.no_automerge)
            if not enable:
                print(f"[automerge] unchanged ({AUTOMERGE_PATH} is left as it is; a re-run never re-enables it, "
                      f"pass --automerge to opt in): the operator merges every card unless it already exists")
            else:
                result = seed_file(args.repo, args.hostname, AUTOMERGE_PATH, AUTOMERGE_TEXT.encode())
                print(f"[automerge] ON ({AUTOMERGE_PATH}: {result}): merge_card.py may fast-forward a card whose receipts are complete")

        filed, skipped = file_cards(args.repo, args.hostname, cards)
        print(f"BOOTSTRAP OK repo={args.repo} user={login} seeded={seeded} filed={filed} skipped={skipped} cards={len(cards)}"
              if args.bootstrap else
              f"CARDS OK repo={args.repo} filed={filed} skipped={skipped} cards={len(cards)}")
        return 0
    except Steer as exc:
        print(exc.line, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
